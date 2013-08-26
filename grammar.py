import parser
import lex

class S(parser.node):
    def parse(self):
        return self.parseadd(block.block)

'''
S     ::= block
block ::= '[' decls '|' stmts ']'
stmts ::= [ stmt { ';' stmt } ]
stmt  ::= assgn | block
assgn ::= identifier ':=' exp
decls ::= [ decl { ';' decl } ]
decl  ::= identifier ':' identifier
exp   ::= logic
logic ::= order { ('and'|'or'|'=>') order }
order ::= add { ('<'|'>'|'<='|'>='|'='|'!=') add }
add   ::= mul  { ('+'|'-') mul  }
mul   ::= unary { ('*'|'/'|'mod') unary  }
unary ::= ['+'|'-'|'not'] atom
atom  ::= number | identifier | string | '(' exp ')'
''' 

def parentset(node, parent):
    node.parent = parent
    return True

def tokenset(node, parent):
    if not node.start and node.children:
        node.start = node.children[0].start
        node.end   = node.children[-1].end
    return True

import block
import exp

if __name__ == "__main__":
    import sys
    import reader

    s = S(parser.pushstream(lex.lex(reader.filereader(sys.stdin))))
    parsed = s.parse()
    print("here")
    if not parsed:
        print("Cannot parse")
    elif not s.atend():
        print("Garbage after S")
    else:
        print(s.pprint())
        print(s.printexp())

        s.visit(parentset)
        s.visit(tokenset)
        s.reform([exp.simplify_depth], [exp.simplify_arith])
        s.visit(parentset)
        s.visit(block.blockset)
        s.visit(block.declsset)
        s.visit(block.namecheck)
        print(s.pprint())
        print(s.printexp())


'''
[   c: c; (# not very well-founded #)
    a: c;
    OMEGA : OMEGA
| 
    a := a + 1 * c; 
    c := 6 - a + c + a * 0 + OMEGA; 
    a := (a) + 1 + c; 
    [|
         [   y  : a; 
             z  : c; 
             y1 : c |];
         [|
             [   y : c
             |
                 y := 2;
                 [   xx : y; 
                     z1 : xx | xx := 0t101010 + "432423\n"]]]]]
'''
#import cProfile
#cProfile.run('for x in xrange(0, 500): exp(pushstream(lex.lex(reader.stringreader("1-(+1/-c)*(+d mod 0) < (# here! #) x_3 and not (y * 3 < 1/z)")))).parse()')

