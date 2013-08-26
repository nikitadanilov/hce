import sys
import string
import unicodedata

import reader
import parser

class token(parser.node):
    def __init__(self, body, pos):
        self.body  = body
        self.pos   = pos
        self.start = self
        self.end   = self
        self.children = []

    def name(self):
        return '"' + self.body + '"'

    def printexp(self):
        return self.body

    def __str__(self):
        return "{}:{}@{}".format(type(self), self.body, self.pos)

class group(token):
    pass

class fixed(token):
    pass

class op(token):
    pass

class left_paren(group, fixed):
    pass

class right_paren(group, fixed):
    pass

class left_bracket(group, fixed):
    pass

class right_bracket(group, fixed):
    pass

class left_brace(group, fixed):
    pass

class right_brace(group, fixed):
    pass

class dot(group, fixed):
    pass

class comma(group, fixed):
    pass

class colon(group, fixed):
    pass

class semicolon(group, fixed):
    pass

class bar(group, fixed):
    pass

class caret(op, fixed):
    pass

class assignment(op, fixed):
    pass

class lt(op, fixed):
    pass

class gt(op, fixed):
    pass

class le(op, fixed):
    pass

class ge(op, fixed):
    pass

class eq(op, fixed):
    pass

class ne(op, fixed):
    pass

class plus(op, fixed):
    pass

class minus(op, fixed):
    pass

class asterisk(op, fixed):
    pass

class divide(op, fixed):
    pass

class mod(op, fixed):
    pass

class land(op, fixed):
    pass

class lor(op, fixed):
    pass

class lnot(op, fixed):
    pass

class lergo(op, fixed):
    pass

class valued(token):
    pass

class number(valued):
    def __init__(self, body, pos, radix, floated):
        token.__init__(self, body, pos)
        self.radix   = radix
        self.floated = floated
        if floated:
            self.value = float(body)
        else:
            self.value = int(body, base = 0)
        print(body, " -> ", self.value)

class stringliteral(valued):
    def __init__(self, body, pos):
        token.__init__(self, body, pos)
        import ast
        self.value = ast.literal_eval(body)

class identifier(token):
    pass

punctuation = [
    (":="  , assignment),
    ("=>"  , lergo),
    ("<="  , le),
    (">="  , ge),
    ("<"   , lt),
    (">"   , gt),
    ("="   , eq),
    ("!="  , ne),
    ("+"   , plus),
    ("-"   , minus),
    ("*"   , asterisk),
    ("/"   , divide),
    ("mod" , mod),
    ("and" , land),
    ("or"  , lor),
    ("not" , lnot),
    ("("   , left_paren),
    (")"   , right_paren),
    ("["   , left_bracket),
    ("]"   , right_bracket),
    ("{"   , left_brace),
    ("}"   , right_brace),
    ("."   , dot),
    (","   , comma),
    (":"   , colon),
    (";"   , semicolon),
    ("|"   , bar),
    ("^"   , caret)
]

COMMENT_START = "(#"
COMMENT_END   = "#)"

BASES = {
    "d" : [ 10, string.digits ],
    "x" : [ 16, string.hexdigits ],
    "o" : [  8, string.octdigits ],
    "b" : [  2, "01" ]
}

class lex(object):
    class lexerror(Exception):
        def __init__(self, lex, error):
            print("Lexical error: '{}' at {}".format(error, 
                                                     str(lex.reader.posget())))

    class notoken(lexerror):
        def __init__(self, lex):
            lex.lexerror.__init__(self, lex, "no token")

    class illnumber(lexerror):
        def __init__(self, lex):
            lex.lexerror.__init__(self, lex, "illformed number at")

    class illstring(lexerror):
        def __init__(self, lex, msg):
            lex.lexerror.__init__(self, lex, "illformed string: " + msg)

    def __init__(self, reader):
        self.reader = reader
        self.word   = ""

    def __iter__(self):
        return self

    def next(self):
        # skip whitespace and (nesting) comments
        cdepth = 0
        while True:
            if self.oneof(" \t\n\r\v"): # string.whitespace
                continue
            if self.accept(COMMENT_START):
                cdepth += 1
            elif cdepth > 0:
                if self.accept(COMMENT_END):
                    cdepth -= 1
                elif self.reader.atend():
                    raise lex.lexerror(self, "unterminated comment")
                else:
                    self.move(1)
                continue
            else:
                break

        if self.reader.atend():
            raise StopIteration

        # from now on, either return a token or raise an exception
        pos = self.reader.posget()

        count = 0
        self.word = ""

        # keyword or punctuation
        #
        # goes before number, because ".1" is *not* a valid number
        for word, ttype in punctuation:
            if self.accept(word):
                return ttype(word, pos)

        # number
        radix   = 0
        floated = False
        r_pos   = 0
        e_pos   = 0
        allowed = string.digits
        while True:
            ch = self.oneof(allowed)
            if ch == "":
                break
            count += 1
            if count == 1 and ch == "0":
                allowed = string.digits + "dxob.eE"
            elif ch in BASES:
                radix   = BASES[ch][0]
                allowed = BASES[ch][1]
                r_pos   = count
            elif ch in "eE":
                allowed = string.digits + "+-"
                floated = True
                e_pos   = count
            elif ch in "+-":
                assert floated
                allowed = string.digits
                e_pos   = count
            elif ch == ".":
                allowed = string.digits + "eE"
                floated = True
            elif count < 3:
                allowed = string.digits + ".eE"

        if count > 0:
            # "0t3" is invalid, but "0t13" is valid 
            # (parses as "0t1" followed by "3")
            # "1e+" and "1e" are invalid, but "1e+2" is valid
            if (r_pos != 0 and r_pos >= count) or \
               (e_pos != 0 and e_pos >= count):
                raise lex.illnumber(self)
            else:
                return number(self.word, pos, radix, floated)

        # string
        if self.oneof('"'):
            while True:
                if self.reader.atend():
                    raise lex.illstring(self, "unterminated string")
                ch = self.oneof('\\"')
                if ch == "\\":
                    ch = self.oneof('tnu\\"')
                    if ch == "u":
                        for _ in range(0, 4):
                            if not self.oneof(string.hexdigits):
                                raise lex.illstring(self, "invalid \\u escape")
                    elif not ch:
                        raise lex.illstring(self, "unrecognised escape")
                elif ch == '"':
                    break
                else:
                    self.word += self.reader.look(0, 1)
                    self.move(1)

        if self.word != "":
            return stringliteral(self.word, pos)

        # identifier
        while True:
            ch = self.reader.look(count, 1)
            if ch == "":
                break
            # unicode(ch) for Python2
            # s/unicode(ch)/ch/ for Python3
            uc = unicodedata.category(ch)[0]
            if ch == "_" or uc == "L" or (count > 0 and uc == "N"):
                count += 1
                self.word += ch
            else:
                break

        if count > 0:
            self.move(count)
            return identifier(self.word, pos)

        raise lex.notoken(self)
        
    def oneof(self, options):
        ch = self.reader.look(0, 1)
        if options.find(ch) != -1:
            self.word += ch
            self.move(1)
            return ch
        else:
            return ""
        
    def accept(self, word):
        nr = len(word)
        if self.reader.look(0, nr) == word:
            self.move(nr)
            return True
        else:
            return False

    def move(self, n):
        self.reader.move(n)

