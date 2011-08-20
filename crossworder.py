#!/usr/bin/python3
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
                    metadata[title.lower().strip()] = data.strip()
                except:
                    pass
            elif start != '#':
                c = clue.Clue(stripped)
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
            if x > maxx:
                maxx = x
            if x < minx:
                minx = x    
            if y > maxy:
                maxy = y
            if y < miny:
                miny = y

    xlen = maxx - minx
    ylen = maxy - miny

    grid = [[None] * xlen for _ in range(ylen)]
    
    for name,c in clues.items():
        x,y = c.startpoint()
        endx,endy = c.endpoint()
        a = c.text_answer()
        if not a:
            a = [None] * c.length()

        cur = grid[y][x]
        if not cur:
            cur = (a[0],None,None)

        if a[0] and cur[0] and a[0] != cur[0][0]:
            raise ValueError("Mismatched letters ('%s' vs '%s') at (%d, %d)" % (cur[0],a[0],x,y))

        if c.is_across():
            gridset = (cur[0],c,cur[2])
            for char,i in zip(a[1:],range(x+1,endx)):
                curgrid = grid[y][i]
                if not curgrid:
                    grid[y][i] = (char,None,None)
                elif char and curgrid[0] != char:
                    if not curgrid[0]:
                        grid[y][i] = (char,curgrid[1],curgrid[2])
                    else:
                        raise ValueError("Mismatched letters ('%s' vs. '%s') at (%d, %d)" % (curgrid[0],char,i,y))
        else:
            gridset = (cur[0],cur[1],c)
            for char,i in zip(a[1:],range(y+1,endy)):
                curgrid = grid[i][x]
                if not curgrid:
                    grid[i][x] = (char,None,None)
                elif char and curgrid[0] != char:
                    if not curgrid[0]:
                        grid[i][x] = (char,curgrid[1],curgrid[2])
                    else:
                        raise ValueError("Mismatched letters ('%s' vs. '%s') at (%d, %d)" % (curgrid[0],char,x,i))
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
    
    latex = [r'''\documentclass[a4paper,10pt]{article}
\usepackage[top=1in]{geometry}
\usepackage{tikz}
\usepackage{multicol}

\setlength\parindent{0pt}

\begin{document}''']
    
    
    if 'title' in metadata and 'author' in metadata:
        latex.append(r'\title{%s}'%metadata['title'])
        latex.append(r'\author{%s}'%metadata['author'])
        latex.append(r'\date{}\maketitle')
    
    latex.append(r'''\thispagestyle{empty}\begin{figure}[h]
    \centering
        \begin{tikzpicture}[scale=0.8,
                  number/.style={below right,font=\scriptsize},
                  answer/.style={color=gray,font=\scshape}]''')
    latex.append(r'\draw[black] (0,%d) grid (%d,0);' % (-ylen,xlen))
    
    across = []
    down = []
    
    for i,row in enumerate(grid):
        for j,c in enumerate(row):
            if c:
                if answers:
                    latex.append(r'\node[answer] at (%.1f,%.1f) {%s};' % (j+0.5,-i-0.5,c[0] if c[0] else '-'))
                if c[1] or c[2]:
                    if c[1]:
                        num = c[1].number()
                        across.append(c[1])
                    if c[2]:
                        num = c[2].number()
                        down.append(c[2])

                    latex.append(r'\node[number] at (%d,%d) {%d};' % (j,-i,num))
            else:
                latex.append(r'\fill[black] (%d,%d) rectangle (%d,%d);' % (j,-i,j+1,-i-1))
    latex.append(r'\end{tikzpicture}\end{figure}')
    latex.append(r'\begin{multicols}{2}')
    latex.append(r'\subsection*{Across}')
    
    latex += ['%d. %s (%s)\n' % (c.number(), c.clue(), c.lengthstring()) for c in across]
    
    latex.append(r'\columnbreak\subsection*{Down}')
    latex += ['%d. %s (%s)\n' % (c.number(), c.clue(), c.lengthstring()) for c in down]

    latex.append(r'\end{multicols}\end{document}')
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
    
    
    
