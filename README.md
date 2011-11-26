# Crossworder
By Huon Wilson

[Crossworder](https://github.com/dbaupp/crossworder) is a python3 program that reads a file specifying crossword clues and answers (and their position and direction), and outputs the crossword in [LaTeX](https://en.wikipedia.org/wiki/LaTeX) with [TikZ](https://en.wikipedia.org/wiki/PGF/TikZ) with options like whether to print answer or not, and the ability to change the formatting.

It detects mismatched letters, but doesn't check for clues running on to each other, or overlapping or anything like that. The size of the grid and the number for each clue is automatically computed based on the clues (so `x` and `y` below can be negative, for example).

## File format 
The input file is processed line by line. Lines starting with `#` are comments. Lines starting with `@` are metadata. Anything else is a clue (unless it is invalid, in which case it is ignored). See `examples/` for some examples (logically).


### Clues
The format for each clue is

    (<name>)direction|x|y|answer|clue

where

- `name` is an optional name for the clue, surrounded by `<...>`, it
  can be used in the actual text of clues to refer to 3-down, or
  10-across by putting `<name>` in the text in the appropriate place
- `direction` is either `a` (across) or `d` (down)
- `x` and `y` are integers that represent the point `(x,y)` where the
  first letter of the answer goes on the grid
- `answer` is either the answer (e.g. `employ` or `crossword clue`) or
  a length specification of the answer surrouded by brackets
  (e.g. `(6)` or `(9,4)`)
- `clue` is the actual clue that is printed (e.g. `A zombie is sure
  for punishment`), it can have LaTeX in it

#### Separated clues
A clue can be broken across multiple series of cells, e.g.
    
    ACROSS
    44  See 14 down
    
    DOWN
    14, 44-across  This prison piece. (8,8)

This is done by putting multiple values in each of `direction`, `x`, `y` and `answer`, separated by `&`, in the order that the clues should be (NB. if `answer` is a length spec then the `&` goes inside the spec), e.g. the example above is (ignoring the numbers and references, which are generated automatically)

    d&a|18&1|3&17|(8,&8)|This prison piece.

### Metadata
Metadata control the output, all metadata is optional. The format for
a metadata line is

    @key(+): data
    
Some keys take an optional  `+`, and indicates that there are multiple
pieces of data associated with that key. For example,
    
    @package+: upgreek
    @package+: wasysym

    
#### Recognised keys
- `author`: The author of the crossword
- `break`: Whether to have the clues and crossword on separate pages,
  anything other than `true` is equivalent to `false` (defaults to
  `false`)
- `documentclass`: The document class to use; options can be given as
  with `package` (defaults to `[a4paper,10pt]article`)
- `margin`: The margins of the page (defaults to `1in`). Can be: 
   - 1 number (with units), for the margin around the whole page
   - 2 numbers (space separated), to set the vertical and horizontal
     margins separately (`@margin: <vertical> <horizontal>`)
   - 4 numbers, to set each margin separately (`@margin: <top> <right>
     <bottom> <left>`)
- `orientation`: Alignment of the page, either `portrait` (default) or
  `landscape`
- `package(+)`: An extra package to load (options to that package can
  be specified by putting them in `[...]` before the name of the
  package (e.g. `[xspace] ellipsis` will put
  `\loadpackage[xspace]{ellipsis}` in the preamble)
- `scale`: The relative size of the `tikzpicture` environment for the
  crossword grid, defaults to `0.8`
- `title`: The title of the crossword

## Compiling
To run crossworder, open a terminal to the directory with crossworder.py and run

    python3 crossworder.py [options] filename
    
It outputs to stdout, so to write to a file try
    
    python3 crossworder.py [options] filename > outputfile.tex
    
The only command line option supported is `-A`, which will print the answers inside the squares of the grid of the crossword.

## Output
The output is LaTeX. It loads the following packages: `inputenc`, `fontenc`, `lmodern`, `geometry`, `tikz`, `multicol` and `amsmath`. 

The crossword grid is draw using TikZ, and the clues are placed in two columns using `multicol`.

## License
See LICENSE

