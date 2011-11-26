#!/usr/bin/env python3

# crossworder.py

import re, clue,sys

def message(*m):
    print(*m,file=sys.stderr)

# loads the clues "line" by "line" from iterable (could be a file,
# list of strings etc), 
# returns (dictionary of metadata (key => data), dictionary of clues (name => Clue))
def load_clues(iterable):
    clues = {}
    metadata = {}
    count = 0
    for cl in iterable:
        stripped = cl.strip()
        if not stripped:
            continue
        start = stripped[0] # get first character
        if start == '@': # metadata
            try:
                rawkey,rawdata = stripped[1:].split(':',1) # separate on :
                key = rawkey.lower().strip()
                data = rawdata.strip()

                if not key: # no real key
                    continue
                if len(key) > 1 and key[-1] == '+': # its a multiple option, so make a list
                    key = key[:-1]
                    if key in metadata:
                        mk = metadata[key]
                        if isinstance(mk,list):
                            mk.append(data)
                        else:
                            metadata[key] = [mk, data]
                    else:
                        metadata[key] = [data]
                else:
                    metadata[key] = data.strip()
            except Exception as e:
                message("Warning: Tried but couldn't parse as metadata:", cl)
                message(str(e))
                
        elif start != '#': 
            # not a comment

            # parse the clues, possibly multiple due to separated
            # clues
            try:
                for c in clue.parse_clues(stripped): 
                    id =  c.name()
                    if not id:
                        id = count 
                        count += 1
                    
                    clues[id] = c
            except:
                # probably couldn't parse the clue...
                message("Warning: Couldn't parse as a clue:", cl)
                
    return (metadata,clues)
    
# load clues from a file
def from_file(filename):
    return load_clues(open(filename,'rU'))
    
# turn a dictionary of clues into a representation of the grid
def make_grid(clues):
    # work out the size of the grid, by going through all the clues
    minx,maxx = (float('inf'),float('-inf'))
    miny,maxy = minx,maxx
    
    for name,c in clues.items():
        for x,y in (c.endpoint(),c.startpoint()):
            maxx = max(maxx,x)
            minx = min(minx,x)
            maxy = max(maxy,y)
            miny = min(miny,y)

    # we've got the size of the grid
    xlen = maxx - minx + 1
    ylen = maxy - miny + 1

    # the grid is represent by a matrix of 
    # (letter, across_clue_that_starts_here, down_clue_that_starts_here)
    # with None for blank cells, and None in any of the elements of the 
    # tuple to represent missing value
    grid = [[None] * xlen for _ in range(ylen)]
    
    # go through the clues again, filling in the grid with the letters
    # die if there is a overlap, with mismatched letters
    for name,c in clues.items():
        x,y = c.startpoint()
        endx,endy = c.endpoint()

        # normalise the clue to fit in the 0-based indexed grid
        x -= minx
        y -= miny
        endx -= minx
        endy -= miny
        
        # get the answer, if the clue doesn't have one (i.e. it was
        # defined by a length spec), then use None
        answer = c.text_answer()
        if not answer:
            answer = [None] * c.length()
        
        # get the stuff at our current letter
        cur = grid[y][x]
        if not cur: # it is answer blank square
            cur = (answer[0],None,None)
        elif not cur[0]: # it doesn't have a letter
            cur = (answer[0],cur[1],cur[2])
        
        # check the first letter match
        if answer[0] and cur[0] and answer[0] != cur[0][0]:
            raise ValueError("Mismatched letters ('%s' vs '%s') at (%d, %d)" % (cur[0],answer[0],x+minx,y+miny))
        
        # across clue
        if c.is_across():
            if cur[1]:
                raise ValueError("Two clues starting at (%d,%d)" % (x+minx,y+miny))
            
            grid[y][x] = (cur[0],c,cur[2])  # update the starting cell

            # go through the rest of the answer, filling in as appropriate
            for char,i in zip(answer[1:],range(x+1,endx + 1)):
                curgrid = grid[y][i]
                if not curgrid: # blank cell, 
                    grid[y][i] = (char,None,None)
                elif not curgrid[0]: # the letter was blank
                    grid[y][i] = (char,curgrid[1],curgrid[2])   
                elif char and curgrid[0] != char: # mismatch!!
                    raise ValueError("Mismatched letters ('%s' vs. '%s') at (%d, %d)" % (curgrid[0],char,i+minx,y+miny))
        else: # down clue
            if cur[2]:
                raise ValueError("Two clues starting at (%d,%d)" % (x+minx,y+miny))

            grid[y][x] = (cur[0],cur[1],c) # update the starting cell
            
            # go through the rest of the answer, filling in as appropriate
            for char,i in zip(answer[1:],range(y+1,endy + 1)):
                curgrid = grid[i][x]
                if not curgrid: # blank cell
                    grid[i][x] = (char,None,None)
                elif not curgrid[0]: # the letter was blank
                    grid[i][x] = (char,curgrid[1],curgrid[2])   
                elif char and curgrid[0] != char: # mismatch!!
                    raise ValueError("Mismatched letters ('%s' vs. '%s') at (%d, %d)" % (curgrid[0],char,i+minx,y+miny))
    
    # now go through the grid from left-to-right, top-to-bottom,
    # numbering clues
    count = 0
    for row in grid:
        for clue in row:
            # check that the cell isn't blank and that a clue starts here
            if clue and (clue[1] or clue[2]): 
                    count += 1
                    if clue[1]:
                        clue[1].number(count)
                    if clue[2]:
                        clue[2].number(count)
    
    # the numbers are known, so now go and resolve references
    # (like "See 12-across")
    for name,c in clues.items():
        c.resolve_names(clues)
        
    return grid

# massively hacky, but, take a grid and metadata and render the crossword
def render_as_latex(grid,metadata={},answers=False):
    # matches stuff in the form "[foo]bar"
    RE_OPTIONS = re.compile(r'^\[([^\]]*)\](.*)$')

    ylen = len(grid)
    xlen = len(grid[0])

    break_page = 'break' in metadata and metadata['break'].lower() == "true"

    landscape = metadata.get('orientation','portrait').lower() == 'landscape'

    # parse the margin
    margin = 'margin=1in'
    if 'margin' in metadata:
        # space in the middle, so it's a complicated declaration
        m = metadata['margin'].strip()
        if ' ' in m: 
            l = m.split()
            if len(l) == 2: # <vertical> <horizontal>
                margin = 'top={0},right={1},bottom={0},left={1}'.format(*l)
            elif len(l) == 4: # <top> <right> <bottom> <left>
                margin = 'top=%s,right=%s,bottom=%s,left=%s' % tuple(l)
            else:
                raise ValueError("Invalid margin declaration: %s" % metadata['margin'])
        else: # just one number
            margin = 'margin=%s' % m

    # \documentclass stuff
    docclass='article'
    docclassoptions = 'a4paper,10pt'
    if 'documentclass' in metadata:
        # check if it's of the form "[options,...]class"
        m = RE_OPTIONS.match(metadata['documentclass'])
        if m: # yep there's new options 
            docclass = m.group(2).strip()
            docclassoptions = m.group(1)
        else: # nope
            docclass = metadata['documentclass']
            docclassoptions = ''

    # the document is represented as a large list, which is "".join'd at the end

    # setup, default/required packages
    latex = [r'''\documentclass[%s]{%s}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[%s,%s]{geometry}
\usepackage{tikz}
\usetikzlibrary{positioning}
\usepackage{multicol}
\usepackage{amsmath}''' % (docclassoptions,docclass,landscape and 'landscape' or 'portrait', margin)]
    
    # load more packages
    packagesl = metadata.get('package',[])
    if not isinstance(packagesl, list): # make sure its a list
        packagesl = [packagesl]
    for p in packagesl:
        m = RE_OPTIONS.match(p)
        if m: # check if it has options
            options = m.group(1)
            name = m.group(2).strip()
        else: # no options
            options = ''
            name = p
        latex.append(r'\usepackage[%s]{%s}' % (options,name))
    
    # no indent, and use sans serif, and no page numbers
    latex.append(r'''\renewcommand{\familydefault}{\sfdefault}
\setlength\parindent{0pt}
\pagestyle{empty}
\begin{document}
\thispagestyle{empty}''')

    # we have a title!
    if 'title' in metadata:
        latex.append(r'\centerline{\Large %s}\medskip'%metadata['title'])

    # we have an author!
    if 'author' in metadata:
        latex.append(r'\centerline{%s}\medskip'%metadata['author'])
        
    # in landscape the clues and crossword go next to each other
    if landscape:
        latex.append(r'\begin{multicols}{2}')
    
    # the scale of the tikzpicture (default is .8)
    scale = metadata.get('scale','0.8')

    tikz = [r'\vspace*{\fill}'] # make it vertically centered (approximately)
    tikz.append(r'''\begin{center}
        \scalebox{%s}{
        \begin{tikzpicture}[number/.style={below right},
                  answer/.style={color=gray,font=\scshape}]''' % (scale))

    tikz.append(r'\draw[black] (0,%d) grid (%d,0);' % (-ylen,xlen)) # draw the grid
    
    # might as well save the clues for later, for efficiencies sake
    across = []
    down = []
    
    # go through the grid (left-to-right, top-to-bottom) drawing
    # numbers or black squares as appropriate
    for i,row in enumerate(grid):
        for j,c in enumerate(row):
            if c: # yep there is a letter
                if answers and c[0]: # we need to print the letter (and it exists)
                    tikz.append(r'\node[answer] at (%.1f,%.1f) {%s};' % (j+0.5,-i-0.5,c[0]))
                if c[1] or c[2]: # a clue starts here
                    if c[1]: # a wild across clue appears
                        num = c[1].number()
                        across.append(c[1])
                    if c[2]: # down too!
                        num = c[2].number()
                        down.append(c[2])

                    # draw the number
                    tikz.append(r'\node[number] at (%d,%d) {%d};' % (j,-i,num)) 
            else:
                # it's empty, so make it black
                tikz.append(r'\fill[black] (%d,%d) rectangle (%d,%d);' % (j,-i,j+1,-i-1))
    
    # finish up                
    tikz.append(r'''
        \end{tikzpicture}}
    \end{center}''')
    

    # vertically centered
    tikz.append(r'\vspace*{\fill}\vspace*{\fill}\vspace*{\fill}\vspace*{\fill}')

    # crossword goes on the right in landscape, so it needs to be added later
    if not landscape: 
        latex += tikz
        
    # do we put the clues separately?
    if break_page:
        latex.append(r'\pagebreak\vspace*{\fill}') # (vertically center the clues)
    
    # clues in 2 columns
    latex.append(r'\begin{multicols}{2}')
    latex.append(r'\subsection*{Across}')
    
    # How to render the clues. Takes a number, the text of the clue, a
    # length spec and a list of the "child" clues of this clue
    # (i.e. separate parts of a separated clue)
    def rrr(num, clu, lstring, children):
        # extra things to put as referenced clues
        extra = ''
        
        if children: # there are children
            _extra = []
            for cccc in children:
                _extra.append("%d-%s" % (cccc.number(), cccc.direction_name(True)))
            extra = ', '+ ', '.join(_extra) # comma separated ", 1-down, 2-across"

        if lstring is None: # no length string
            return r'\textbf{%d%s} %s' % (num,extra, clu)
        else:
            return r'\textbf{%d%s} %s (%s)' % (num, extra, clu,lstring)
    
    # add all the rendered across clues
    for c in across:
        latex.append(rrr(c.number(), c.clue(),c.length_spec(),c.children()) + '\n')
    
    # down!
    latex.append(r'\subsection*{Down}')
    for c in down:
        latex.append(rrr(c.number(), c.clue(),c.length_spec(),c.children()) + '\n')
    
    latex.append(r'\end{multicols}') # end the multicols for the clues

    if break_page: # vertically center clues if they are on a different page
        latex.append(r'\vspace*{\fill}\vspace*{\fill}\vspace*{\fill}')
    
    # crossword on the right (and end the multicol that aligns everything)
    if landscape:
        latex += tikz
        latex.append(r'\end{multicols}')

    # done! phew!
    latex.append(r'\end{document}')
    return '\n'.join(latex)
    
    
if __name__ == '__main__':
    import sys, getopt
    
    # options
    ops,args = getopt.getopt(sys.argv[1:],'A')

    # only one option though
    answers = False
    for op,arg in ops:
        if op == '-A':
            answers = True

    f = sys.stdin # default to stdin
    if args: # but if there are files specified, use them
        f = open(args[0],'rU')

    # load the clues
    metadata,clues=load_clues(f)
    if clues: # yep, found clues!
        try:
            grid = make_grid(clues)
        except ValueError as e: # failed!
            message("Error:", e)
            sys.exit(1)
        print(render_as_latex(grid,metadata,answers))
    else:
        message("Error: No clues found")
        sys.exit(2)
