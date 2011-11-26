import re, sys
# name of a clue (<blah>a|1|1...) (these record the name found)
RE_SPLIT_NAME_BEGIN = re.compile(r'^\<([^>]*)\>') # at the start of a line only
RE_SPLIT_NAME = re.compile(r'\<([^>]*)\>') # anywhere

# recognise length specs, i.e. (1,2-3.4)
RE_LENGTH_SPEC = re.compile(r'^\([0-9]+([,-.](\([^\)]*\))?[0-9]+)*\)$')

# punctuation
RE_PUNCT = re.compile(r'[,.-]')

# things that split words in an answer (and save them)
RE_WORD_SPLIT = re.compile(r'([ ,.-])')

# yep, need a regex for this
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
        # see if it has a name at the start of the line
        m = RE_SPLIT_NAME_BEGIN.match(s)
        if m: # yep, so remember the name, and deal with the rest of the clue
            name = m.group(1)
            s = s.split('>',1)[1]
            
        # split the clue on pipe
        t = tuple(s.split('|',4))
        
        # try unwrapping, this could fail
        (_directions,_xs,_ys,_answers,clue) = t
    except ValueError as e:
        raise ValueError("Line could not be parsed: %s" % s)

    # get rid of &'s from the answer
    clean_answers = RE_AMPERSANDS.sub('',_answers)
    is_length_spec = False 
    if RE_LENGTH_SPEC.match(clean_answers): # yep it is a length spec
        is_length_spec = True
        answer = None # so no answer
        length_spec = clean_answers.strip('()') # we have a ready made length spec
        usable_answers = _answers.strip('()') # this one is for separated clues
    else: # nope, an actual answer
        answer = RE_SPLIT_NAME.sub('',clean_answers.strip()) # remove names
        usable_answers = _answers # separated clues
        lengthbuilder = []
        for (i,w) in enumerate(RE_WORD_SPLIT.split(answer)): # split the words up
            if i % 2: # punctuation
                if w == ' ': # commas instead of spaces
                    lengthbuilder.append(',')
                else:
                    lengthbuilder.append(w)
            else: # word
                lengthbuilder.append(str(len(w)))
        length_spec = ''.join(lengthbuilder) 
    # convert the length spec to the total length of the clue
    length = sum([int(x) for x in RE_PUNCT.split(length_spec)])
    
    # check that all of the fields have the same number of splits
    count = _directions.count('&')
    for k in [_xs,_ys,_answers]:
        if k.count('&') != count:
            raise ValueError('Mismatched number of splits: %s' % s)

    # get the fields for each subclue of our current one (this works
    # for unsplit clues too)
    raw_clues = list(zip(*[ss.split('&') for ss in [_directions,_xs,_ys,usable_answers]]))
    num_parts = len(raw_clues)

    # go through all the raw clues, and make them real clues!
    clues = []
    for (i,(_direction,_x,_y,_answer)) in enumerate(raw_clues):
        
        # get the direction
        first_direction = _direction.strip()[:1].lower() # only bother with the first letter
        if first_direction == 'a':
            direction = Direction.ACROSS 
        elif first_direction == 'd':
            direction = Direction.DOWN
        else:
            raise ValueError("Invalid direction: %s" % _direction)
        
        # get the position
        try: 
            x = int(_x)
            y = int(_y)
        except:
            raise ValueError("Invalid position: (%s,%s)" % (_x,_y))
        
        #answer = RE_SPLIT_NAME.sub('',clean_answers.strip())
        
        # compute the length of this subclue
        if is_length_spec:
            lengths = map(int,RE_PUNCT.split(_answer))
            myanswer = None
        else:
            lengths = map(len, RE_PUNCT.split(_answer))
            myanswer = _answer
        mylength = sum(lengths)
            
        if num_parts > 1: # separated clue
            if i: # not the first one (so it's a child)
                # it's a child, so it doesn't have a length spec or a clue
                child = Clue(direction,name,x,y,myanswer,None,mylength,None, [], parent)
                clues.append(child)
                parent.add_child(child)
            else: # the first clue (so it's the parent)
                parent = Clue(direction,name,x,y,myanswer,length_spec,mylength,clue,[])
                clues.append(parent)
        else: # not separated, so easy
            c = Clue(direction,name,x,y,myanswer,length_spec,length,clue,[],[])
            clues.append(c)
    return clues

# convert a direction to a string
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

# the representation of a clue
class Clue(object):
    def __init__(self,direction,name,x,y,answer,lenstring,length,clue,children=[],parent=None):
        self._name = name
        self._direction = direction
        self._x = x
        self._y = y
        self._answer = answer
        self._length_spec = lenstring
        self._length = length
        self._clue = clue
        self._children = children
        self._parent = parent
    
    # set/get the name of the clue
    def name(self,name=None): 
        if name:
            self._name = name
        else:
            return self._name
    
    # set/get the number
    def number(self,n=None): 
        if n:
            self._number = n
        else:
            return self._number
    
    # set/get the text of the clue
    def clue(self,clue=None):
        if clue:
            self._clue = clue
        else:
            return self._clue
    
    # add a child to the clue
    def add_child(self, c):
        self._children.append(c)
    
    # get/set the children of the clue
    def children(self,children=None):
        if children is None:
            return self._children
        else:
            self._children = children

    # return the actual answer to the clue without any word gaps, if
    # it exists, else None
    def text_answer(self):
        if self._answer:
            return RE_WORD_SPLIT.sub('',self._answer)
        else:
            return None

    # get various properties
    def answer(self):
        return self._answer
    def length_spec(self):
        return self._length_spec
    def length(self):
        return self._length
    def startpoint(self): # starting position
        return(self._x,self._y)
        
    def endpoint(self): # ending position
        if self.is_across():
           return (self._x + self._length - 1, self._y)
        else:
           return (self._x, self._y + self._length - 1)
    
    def points(self): # the points the clue goes through
        if self.is_across():
            return [(self._x + i,self._y) for i in range(self._length)]
        else:
            return [(self._x, self._y + i) for i in range(self._length)]

    def is_across(self):
        return self._direction == Direction.ACROSS
         
    # the name of the direction the clue points (e.g. 'across')
    def direction_name(self,long=False,capital=False):
        return dir2str(self._direction,long,capital)
         
    # convert any references like "The <blahblah> more clue" into "The
    # 23-down more clue", and write the clue for child clues (to say
    # "See 23-down", or whatever is appropriate)
    #
    # clues is a dictionary mapping names to Clue objects
    def resolve_names(self,clues):
        if self._clue is None and self._parent: # yep, child clue
            self._clue = "See %d-%s" % (self._parent.number(),self._parent.direction_name(True))
        else: # nope not child clue
            newclue = []
            # split the current clue on the names
            # so "The <blahblah> more clue" becomes ["The ","blahblah"," more clue"]
            for i,s in enumerate(RE_SPLIT_NAME.split(self._clue)):
                if i % 2: # it's a name
                    if s in clues: # yep, the name exists
                        c = clues[s]  
                        # put the appropriate thing into the newclue
                        newclue.append('%d-%s' % (c.number(),c.direction_name(True)))
                    else:
                        raise ValueError("Named clue '%s' not found" % s)
                else: # just normal text
                    newclue.append(s)
            # set the clue
            self._clue = ''.join(newclue)
         
    # convert to a string nicely
    def __str__(self):
        if hasattr(self,'_number'):
            return '%i. %s at (%i,%i) "%s" => "%s" (%s)' % (
                        self._number,
                        dir2str(self._direction,True),
                        self._x, self._y, self._clue,
                        self._answer, self._length_spec)
        else:
            return '  %s at (%i,%i) "%s" => "%s" (%s)' % (
                        dir2str(self._direction,True),
                        self._x, self._y, self._clue,
                        self._answer, self._length_spec)
    
    # should be approximately the inverse of parse_clues above (almost...)
    def __repr__(self):
        namestr = ''
        if self._name:
            namestr = '<%s>' % self._name
        if self._answer == None:
            return '%s%s|%i|%i|(%s)|%s' % (namestr,dir2str(self._direction),self._x,self._y,
                                        self._length_spec,self._clue)
        else:
            return '%s%s|%i|%i|%s|%s' % (namestr,dir2str(self._direction),self._x,self._y,
                                        self._answer,self._clue)            
