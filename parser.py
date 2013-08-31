import sys

import reader
import tree

class node(tree.tnode):
    def __init__(self, seq):
        tree.tnode.__init__(self)
        self.seq   = seq
        self.block = None
        self.start = None
        self.end   = None

    def name(self):
        return self.__class__.__name__

    def printexp(self):
        return "(" + " ".join([ x.printexp() for x in self.children ]) + ")"

    def parse(self):
        return self.parse0()

    def pos(self):
        return self.start.pos

    def atend(self):
        self.push()
        eof = (self.seq.nextsafe() == None)
        self.rollback()
        return eof

    def oneofdict(self, tokendict):
        token = self.seq.nextsafe()
        if token:
            token.seq = self.seq
            for ttype, retval in tokendict.items():
                if isinstance(token, ttype):
                    self.children.append(token)
                    return retval
        return False

    def oneof(self, tokenlist):
        return self.oneofdict({x : True for x in tokenlist})

    def push(self):
        self.mark = len(self.children)
        self.seq.push()

    def pop(self):
        self.seq.pop()

    def rollback(self):
        self.seq.rollback()
        self.children = self.children[:self.mark]

    def parseadd(self, nodetype):
        node = nodetype(self.seq)
        if node.parse():
            self.children.append(node)
            return True
        return False

    def nlist(self, childtype, delimiters, assoc, minel):
        self.push()
        if self.parseadd(childtype):
            i = 1
            while True:
                self.push()
                if self.oneof(delimiters) and self.parseadd(childtype):
                    self.pop()
                    i += 1
                    continue
                self.rollback()
                break
            self.pop()
            if i < minel:
                return False
            if assoc in {ASSOC_LEFT, ASSOC_RIGHT}:
                start, end = {ASSOC_LEFT:  (0, 3), 
                              ASSOC_RIGHT: (-3, len(self.children))}[assoc]
                while len(self.children) > 3:
                    left = type(self)(self.seq)
                    left.children = self.children[start:end]
                    self.children[start:end] = [left]
            return True
        else:
            self.rollback()
            return minel == 0

    def alternative(self, alternatives):
        for ntype in alternatives:
            self.push()
            if self.parseadd(ntype):
                self.pop()
                return True
            else:
                self.rollback()
        return False

    def longest(self, alternatives):
        longest = None
        maxlen  = -1
        index   = self.seq.index
        for ntype in alternatives:
            self.push()
            if self.parseadd(ntype):
                if self.seq.index - index > maxlen:
                    maxlen  = self.seq.index - index
                    longest = ntype
            self.rollback()
        if longest:
            self.parseadd(longest)
        return longest != None

    def blockchain(self):
        block = self.block
        while block != None:
            yield block
            block = block.block

    def boundchain(self, name):
        return [b.lookup(name) for b in self.blockchain() if b.bound(name)]

ASSOC_LEFT  = 1
ASSOC_RIGHT = 2
ASSOC_NONE  = 3

class pushstream(object):
    def __init__(self, it):
        self.it    = it.__iter__()
        self.marks = []
        self.saved = []
        self.index = 0
        self.start = -1

    def __iter__(self):
        return self

    def push(self):
        if self.start == -1:
            self.start = self.index
        self.marks.append(self.index)

    def pop(self):
        self.marks.pop()

    def rollback(self):
        self.index = self.marks.pop()

    def next(self):
        if self.start <= self.index < self.start + len(self.saved):
            o = self.saved[self.index - self.start]
        else:
            o = self.it.next()
            if not self.marks:
                self.saved = []
                self.start = -1
            if self.start >= 0:
                self.saved.append(o)
        self.index += 1
        return o

    def nextsafe(self):
        try:
            o = self.next()
        except StopIteration:
            o = None
        return o

class languageerror(Exception):
    def __init__(self, token, msg):
        self.token = token
        self.msg   = msg

    def __str__(self):
        return "at {}: {}".format(str(self.token), self.msg)

class parseerror(languageerror):
    pass

class semanticserror(languageerror):
    pass

def istoken(node, body):
    return isinstance(node, lex.token) and node.body == body

import lex
