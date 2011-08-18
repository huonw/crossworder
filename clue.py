import re
RE_CLUE_NUMBER = re.compile(r'^\([0-9]+([,-.][0-9]+)*\)$')
RE_PUNCT = re.compile(r'[,.-]')
RE_WORD_SPLIT = re.compile(r'([ ,.-])')

def tokenise_line(s):
    # recieve line in the form "direction|x|y|answer|clue"
    try:
        t = tuple(s.split('|',4))
        (_direction,_x,_y,_answer,clue) = t
    except ValueError as e:
        raise ValueError("Line could not be parsed: %s" % s)
    data = {}
    
    first_direction = _direction[:1].lower()
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
    
    if RE_CLUE_NUMBER.match(_answer):
        answer = None
        lengthstring = _answer.strip('()')
    else:
        answer = _answer
        
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
    
    return (direction,x,y,answer,lengthstring,length,clue)

def dir2str(dirr,long=False):
    names = ['a','d']
    if long:
        names = ['across','down']
        
    if dirr == Direction.ACROSS:
        return names[0]
    else:
        return names[1]

class Direction:
    ACROSS = 1
    DOWN = 2

class Clue(object):
    def __init__(self,direction,x=None,y=None,answer=None,lenstring=None,length=None,clue=None):
    
        # if there is one argument, try to parse it as a line
        if len(set([x,y,answer,lenstring,length,clue])) == 1 and x == None:
            (direction,x,y,answer,lenstring,length,clue) = tokenise_line(direction)
        self._direction = direction
        self._x = x
        self._y = y
        self._answer = answer
        self._lengthstring = lenstring
        self._length = length
        self._clue = clue
    
    def number(self,n=None):
        if n != None:
            self._number = n
        else:
            return self._number
    
    def clue(self):
        return self._clue
    def lengthstring(self):
        return self._lengthstring
    
    def startpoint(self):
        return(self._x,self._y)
        
    def endpoint(self):
        if self.is_across():
           return (self._x + self._length, self._y)
        else:
           return (self._x, self._y + self._length)
    
    def is_across(self):
        return self._direction == Direction.ACROSS
         
    def __str__(self):
        return '%i. %s at (%i,%i) "%s" => "%s" (%s)' % (
                        self._number,
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
