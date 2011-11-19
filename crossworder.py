#!/usr/bin/env python3
import re, clue,sys

def load_clues(iterable):
    clues = {}
    metadata = {}
    count = 0
    for cl in iterable:
        stripped = cl.strip()
        if stripped:
            start = stripped[0]
            if start == '@':
                # metadata
                try:
                    title,data = stripped[1:].split(':',1)
                    parsed = title.lower().strip()
                    sdata = data.strip()
                    if parsed:
                        if len(parsed) > 1 and parsed[-1] == '+':
                            parsed = parsed[:-1]
                            if parsed in metadata:
                                if isinstance(metadata[parsed],list):
                                    metadata[parsed].append(sdata)
                                else:
                                    metadata[parsed] = [metadata[parsed], sdata]
                            else:
                                metdata[parsed] = [sdata]
                        else:
                            metadata[parsed] = data.strip()
                except:
                    pass
            elif start != '#':
                for c in clue.parse_clues(stripped):
                    id =  c.name()
                    if not id:
                        id = count 
                        count += 1
                    
                    clues[id] = c
    return (metadata,clues)
    
def from_file(filename):
    return load_clues(open(filename,'rU'))
    
    
def make_grid(clues):
    minx,maxx = (float('inf'),float('-inf'))
    miny,maxy = minx,maxx
    
    for name,c in clues.items():
        for x,y in (c.endpoint(),c.startpoint()):
            maxx = max(maxx,x)
            minx = min(minx,x)
            maxy = max(maxy,y)
            miny = min(miny,y)

    xlen = maxx - minx + 1
    ylen = maxy - miny + 1

    grid = [[None] * xlen for _ in range(ylen)]
   
    for name,c in clues.items():
        x,y = c.startpoint()
        endx,endy = c.endpoint()
        x -= minx
        y -= miny
        endx -= minx
        endy -= miny

        a = c.text_answer()
        if not a:
            a = [None] * c.length()
        
        cur = grid[y][x]
        if not cur:
            cur = (a[0],None,None)
        elif not cur[0]:
            cur = (a[0],cur[1],cur[2])

        if a[0] and cur[0] and a[0] != cur[0][0]:
            raise ValueError("Mismatched letters ('%s' vs '%s') at (%d, %d)" % (cur[0],a[0],x+minx,y+miny))

        if c.is_across():
            gridset = (cur[0],c,cur[2])
            for char,i in zip(a[1:],range(x+1,endx + 1)):
                curgrid = grid[y][i]
                if not curgrid:
                    grid[y][i] = (char,None,None)
                elif char and curgrid[0] != char:
                    if not curgrid[0]:
                        grid[y][i] = (char,curgrid[1],curgrid[2])
                    else:
                        raise ValueError("Mismatched letters ('%s' vs. '%s') at (%d, %d)" % (curgrid[0],char,i+minx,y+miny))
        else:
            gridset = (cur[0],cur[1],c)
            for char,i in zip(a[1:],range(y+1,endy + 1)):
                curgrid = grid[i][x]
                if not curgrid:
                    grid[i][x] = (char,None,None)
                elif char and curgrid[0] != char:
                    if not curgrid[0]:
                        grid[i][x] = (char,curgrid[1],curgrid[2])
                    else:
                        raise ValueError("Mismatched letters ('%s' vs. '%s') at (%d, %d)" % (curgrid[0],char,x+minx,i+miny))
        grid[y][x] = gridset
            
    count = 0
    for row in grid:
        for c in row:
            if c and (c[1] or c[2]):
                    count += 1
                    if c[1]:
                        c[1].number(count)
                    if c[2]:
                        c[2].number(count)
    for name,c in clues.items():
        c.resolve_names(clues)
        
    return grid
    
def render_as_latex(grid,metadata={},answers=False):
    ylen = len(grid)
    xlen = len(grid[0])

    break_page = 'break' in metadata and metadata['break'].lower() == "true"

    landscape = metadata.get('orientation','portrait').lower() == 'landscape'
    margin = 'margin=1in'
    if 'margin' in metadata:
        if ' ' in metadata['margin'].strip():
            l = metadata['margin'].split()
            if len(l) == 2:
                margin = 'top={0},right={1},bottom={0},left={1}'.format(*l)
            elif len(l) == 4:
                margin = 'top=%s,right=%s,bottom=%s,left=%s' % tuple(l)
            else:
                raise ValueError("Invalid margin declaration: %s" % metadata['margin'])
        else:
            margin = 'margin=%s' % metadata['margin']

    latex = [r'''\documentclass[a4paper,10pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[%s,%s]{geometry}
\usepackage{tikz}
\usetikzlibrary{positioning}
\usepackage{multicol}
\usepackage{amsmath}
\usepackage{todonotes}
\usepackage{scalefnt}''' % (landscape and 'landscape' or 'portrait', margin)]
    RE_OPTIONS = re.compile(r'^\[([^\]]*)\](.*)$')
    
    packagesl = metadata.get('package',[])
    if not isinstance(packagesl, list):
        packagesl = [packagesl]
    for p in packagesl:
        m = RE_OPTIONS.match(p)
        options = ''
        name = p
        if m:
            options = m.group(1)
            name = m.group(2)
        latex.append(r'\usepackage[%s]{%s}' % (options,name))

    latex.append(r'''\renewcommand{\familydefault}{\sfdefault}
\setlength\parindent{0pt}
\begin{document}''')
    
    
    if 'title' in metadata and 'author' in metadata:
        latex.append(r'\centerline{\Large %s}\medskip'%metadata['title'])
        latex.append(r'\centerline{%s}\medskip'%metadata['author'])
        

    latex.append(r'\pagestyle{empty}\thispagestyle{empty}')
    if landscape:
        latex.append(r'\begin{multicols}{2}')
    
    scale = metadata.get('scale','0.8')

    tikz = [r'\vspace*{\fill}']
    tikz.append(r'''\begin{center}
        \scalebox{%s}{
        \begin{tikzpicture}[number/.style={below right},
                  answer/.style={color=gray,font=\scshape}]''' % (scale))
    tikz.append(r'\draw[black] (0,%d) grid (%d,0);' % (-ylen,xlen))
    
    across = []
    down = []
    
    for i,row in enumerate(grid):
        for j,c in enumerate(row):
            if c:
                if answers and c[0]:
                    tikz.append(r'\node[answer] at (%.1f,%.1f) {%s};' % (j+0.5,-i-0.5,c[0]))
                if c[1] or c[2]:
                    if c[1]:
                        num = c[1].number()
                        across.append(c[1])
                    if c[2]:
                        num = c[2].number()
                        down.append(c[2])

                    tikz.append(r'\node[number] at (%d,%d) {%d};' % (j,-i,num))
            else:
                tikz.append(r'\fill[black] (%d,%d) rectangle (%d,%d);' % (j,-i,j+1,-i-1))
    tikz.append(r'''
        \end{tikzpicture}}
    \end{center}''')
    #if landscape:
    if True:
        tikz.append(r'\vspace*{\fill}\vspace*{\fill}\vspace*{\fill}\vspace*{\fill}')
    #else:
        #tikz.append(r'\vspace*{\fill}')
        latex += tikz
        
    
    if break_page:
        latex.append(r'\pagebreak\vspace*{\fill}')
    latex.append(r'\begin{multicols}{2}')
    latex.append(r'\subsection*{Across}')
    
    def rrr(num, clu, lstring, children):
        extra = []
        if children:
            for cccc in children:
                extra.append("%d-%s" % (cccc.number(), cccc.direction_name(True)))
        if lstring is None:
            return '\\textbf{%d%s} %s' % (num,', '+ ', '.join(extra) if extra else '', clu)
        else:
            return '\\textbf{%d%s} %s (%s)' % (num,', ' + ', '.join(extra) if extra else '', clu,lstring)
    
    latex += [rrr(c.number(), c.clue(),c.lengthstring(),c.children()) + '\n' for c in across]
    
    latex.append(r'\subsection*{Down}')
    latex += [rrr(c.number(), c.clue(), c.lengthstring(),c.children()) + '\n' for c in down]
    latex.append(r'\end{multicols}')
    if break_page:
        latex.append(r'\vspace*{\fill}\vspace*{\fill}\vspace*{\fill}')
    if landscape:
        latex += tikz
        latex.append(r'\end{multicols}')

    latex.append(r'\end{document}')
    return '\n'.join(latex)
    
    
if __name__ == '__main__':
    import sys, getopt
    
    ops,args = getopt.getopt(sys.argv[1:],'A')

    answers = False
    for op,arg in ops:
        if op == '-A':
            answers = True

    f = sys.stdin
    if args:
        f = open(args[0],'rU')
    m,cl=load_clues(f)
    if cl:
        try:
            g = make_grid(cl)
        except ValueError as e:
            print("Error: %s" % e,file=sys.stderr)
            sys.exit(1)
        print(render_as_latex(g,m,answers))
