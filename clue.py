import re, sys
RE_SPLIT_NAME_BEGIN = re.compile(r'^\<([^>]*)\>')
RE_SPLIT_NAME = re.compile(r'\<([^>]*)\>')
RE_CLUE_NUMBER = re.compile(r'^\([0-9]+([,-.](\([^\)]*\))?[0-9]+)*\)$')
RE_PUNCT = re.compile(r'[,.-]')
RE_WORD_SPLIT = re.compile(r'([ ,.-])')
RE_AMPERSANDS = re.compile(r'&')

def parse_clues(line):
    return tokenise_line(line)

def tokenise_line(_s):
    # recieve line in the form "[<name>]direction|x|y|answer|clue"
    # if an answer spans multiple clues, then <name> can be placed just before
    # the clue break.
    # e.g. "exit strategy" over two clues is "exit <otherclue>strategy", or "(4,<otherclue>8)"
    # in clues, <name> will expand to "3 across" or whatever the clue <name> is
    name = None
    s = _s.strip()
    try:
        m = RE_SPLIT_NAME_BEGIN.match(s)
        if m:
            name = m.group(1)
            s = s.split('>',1)[1]
            
        t = tuple(s.split('|',4))
        (_directions,_xs,_ys,_answers,clue) = t
    except ValueError as e:
        raise ValueError("Line could not be parsed: %s" % s)

    clean_answers = RE_AMPERSANDS.sub('',_answers)
    is_lengths = False
    if RE_CLUE_NUMBER.match(clean_answers):
        is_lengths = True
        answer = None
        lengthstring = clean_answers.strip('()')
        usable_answers = _answers.strip('()')
    else:
        answer = RE_SPLIT_NAME.sub('',clean_answers.strip())
        usable_answers = _answers
        lengthbuilder = []
        for (i,w) in enumerate(RE_WORD_SPLIT.split(answer)):
            if i % 2: # punctuation
                if w == ' ':
                    lengthbuilder.append(',')
                else:
                    lengthbuilder.append(w)
            else: # word
                lengthbuilder.append(str(len(w)))
                    
                lengthstring = ''.join(lengthbuilder) 
    length = sum([int(x) for x in RE_PUNCT.split(lengthstring)])
    
    count = _directions.count('&')
    for k in [_xs,_ys,_answers]:
        if k.count('&') != count:
            raise ValueError('Mismatched number of splits: %s' % s)

    raw_clues = list(zip(*[ss.split('&') for ss in [_directions,_xs,_ys,usable_answers]]))
    num_parts = len(raw_clues)

    clues = []
    for (i,(_direction,_x,_y,_answer)) in enumerate(raw_clues):
        first_direction = _direction.strip()[:1].lower()
        if first_direction == 'a':
            direction = Direction.ACROSS 
        elif first_direction == 'd':
            direction = Direction.DOWN
        else:
            raise ValueError("Invalid direction: %s" % _direction)
        
        try:
            x = int(_x)
            y = int(_y)
        except:
            raise ValueError("Invalid position: (%s,%s)" % (_x,_y))
        
        #answer = RE_SPLIT_NAME.sub('',clean_answers.strip())
        
        if is_lengths:
            lengths = map(int,RE_PUNCT.split(_answer))
        else:
            
            lengths = map(len, RE_PUNCT.split(_answer))
        mylength = sum(lengths)
            
        
        if num_parts > 1:
            if i:
                child = Clue(direction,name,x,y,_answer,None,mylength,None, [], parent)
                clues.append(child)
                parent.add_child(child)
            else:
                parent = Clue(direction,name,x,y,_answer,lengthstring,mylength,clue,[])
                clues.append(parent)
        else:
            c = Clue(direction,name,x,y,_answer,lengthstring,length,clue,[],[])
            clues.append(c)
    return clues


def dir2str(dirr,long=False,capital=False):
    names = ['a','d']
    if long:
        names = ['across','down']
    
    if capital:
        names = [x.title() for x in names]
        
    if dirr == Direction.ACROSS:
        return names[0]
    else:
        return names[1]

class Direction:
    ACROSS = 1
    DOWN = 2

class Clue(object):
    def __init__(self,direction,name,x,y,answer,lenstring,length,clue,children=[],parent=None):
    
        # if there is one argument, try to parse it as a line
        #if all(map(lambda x: x is None, [name,x,y,answer,lenstring,length,clue,children,parent])):
        #    (name,direction,x,y,answer,lenstring,length,clue,children,parent) = tokenise_line(direction)
        self._name = name
        self._direction = direction
        self._x = x
        self._y = y
        self._answer = answer
        self._lengthstring = lenstring
        self._length = length
        self._clue = clue
        self._children = children
        self._parent = parent
    
    def name(self,name=None):
        if name:
            self._name = name
        else:
            return self._name
    
    def number(self,n=None):
        if n:
            self._number = n
        else:
            return self._number
    
    def clue(self,clue=None):
        if clue:
            self._clue = clue
        else:
            return self._clue
    def add_child(self, c):
        self._children.append(c)
    def children(self,children=None):
        if children is None:
            return self._children
        else:
            self._children = children


    def text_answer(self):
        if self._answer:
            return RE_WORD_SPLIT.sub('',self._answer)
        else:
            return None
    def answer(self):
        return self._answer
    def lengthstring(self):
        return self._lengthstring
    def length(self):
        return self._length
    def startpoint(self):
        return(self._x,self._y)
        
    def endpoint(self):
        if self.is_across():
           return (self._x + self._length - 1, self._y)
        else:
           return (self._x, self._y + self._length - 1)
    def points(self):
        if self.is_across():
            return [(self._x + i,self._y) for i in range(self._length)]
        else:
            return [(self._x, self._y + i) for i in range(self._length)]

    def is_across(self):
        return self._direction == Direction.ACROSS
         
    def direction_name(self,long=False,capital=False):
        return dir2str(self._direction,long,capital)
         
    def resolve_names(self,clues):
        if self._clue is None and self._parent:
            self._clue = "See %d-%s" % (self._parent.number(),self._parent.direction_name(True))
        else:
            newclue = []
            for i,s in enumerate(RE_SPLIT_NAME.split(self._clue)):
                if i % 2:
                    if s in clues:
                        c = clues[s]
                        newclue.append('%d-%s' % (c.number(),c.direction_name(True)))
                    else:
                        raise ValueError("Named clue '%s' not found" % s)
                else:
                    newclue.append(s)
            self._clue = ''.join(newclue)
         
    def __str__(self):
        if hasattr(self,'_number'):
            return '%i. %s at (%i,%i) "%s" => "%s" (%s)' % (
                        self._number,
                        dir2str(self._direction,True),
                        self._x, self._y, self._clue,
                        self._answer, self._lengthstring)
        else:
            return '  %s at (%i,%i) "%s" => "%s" (%s)' % (
                        dir2str(self._direction,True),
                        self._x, self._y, self._clue,
                        self._answer, self._lengthstring)
    def __repr__(self):
        if self._answer == None:
            return '%s|%i|%i|(%s)|%s' % (dir2str(self._direction),self._x,self._y,
                                        self._lengthstring,self._clue)
        else:
            return '%s|%i|%i|%s|%s' % (dir2str(self._direction),self._x,self._y,
                                        self._answer,self._clue)            
