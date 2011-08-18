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
    print(clues,file=sys.stderr)            
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
    print(xlen,ylen,file=sys.stderr)
    grid = [[None] * xlen for _ in range(ylen)]
    
    for name,c in clues.items():
        x,y = c.startpoint()
        endx,endy = c.endpoint()
        
        cur = grid[y][x]
        if not cur:
            cur = (None,None)
            
        if c.is_across():
            gridset = (c,cur[1])
            for i in range(x,endx):
                if not grid[y][i]:
                    grid[y][i] = (None,None)
        else:
            gridset = (cur[0],c)
            for i in range(y,endy):
                if not grid[i][x]:
                    grid[i][x] = (None,None)
        
        grid[y][x] = gridset
            
    count = 0
    for row in grid:
        for c in row:
            if c:
                if c[0] or c[1]:
                    count += 1
                    if c[0]:
                        c[0].number(count)
                    if c[1]:
                        c[1].number(count)
    for name,c in clues.items():
        c.resolve_names(clues)
        
    return grid
    
def render_as_latex(grid,metadata={}):
    ylen = len(grid)
    xlen = len(grid[0])
    
    latex = [r'''\documentclass[a4paper]{article}
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
        \begin{tikzpicture}[scale=0.8,number/.style={below right,font=\scriptsize}]''')
    latex.append(r'\draw[black] (0,%d) grid (%d,0);' % (-ylen,xlen))
    
    across = []
    down = []
    
    for i,row in enumerate(grid):
        for j,c in enumerate(row):
            if c:
                if c[0] or c[1]:
                    if c[0]:
                        num = c[0].number()
                        across.append(c[0])
                    if c[1]:
                        num = c[1].number()
                        down.append(c[1])

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
    import sys
    f = sys.stdin
    if len(sys.argv) > 1:
        f = open(sys.argv[1],'rU')
    m,cl=load_clues(f)
    g = make_grid(cl)
    print(render_as_latex(g,m))
    
    
    
