import parser
import lex

class exp(parser.node):
    def parse(self):
        return self.parseadd(logic)

class logic(parser.node):
    def parse(self):
        return self.nlist(order, [lex.land, lex.lor, lex.lergo], 
                          parser.ASSOC_LEFT, 1) 

class order(parser.node):
    def parse(self):
        return self.nlist(add, [lex.lt, lex.gt, lex.le, 
                                lex.ge, lex.eq, lex.ne], parser.ASSOC_LEFT, 1)

class add(parser.node):
    def parse(self):
        return self.nlist(mul, [lex.plus, lex.minus], parser.ASSOC_LEFT, 1)

class mul(parser.node):
    def parse(self):
        return self.nlist(unary, [lex.asterisk, 
                                  lex.divide, lex.mod], parser.ASSOC_LEFT, 1)

class unary(parser.node):
    def parse(self):
        self.push()
        if self.oneof([lex.plus, lex.minus, lex.lnot]): 
            self.pop()
        else: 
            self.rollback()
        return self.parseadd(atom)

class atom(parser.node):
    def parse(self):
        next = self.oneofdict({lex.number : True, lex.identifier : True,
                               lex.stringliteral : True, lex.left_paren : +2})
        if next == +2:
            return self.parseadd(exp) and self.oneof([lex.right_paren])
        else:
            return next


def simplify_depth(node):
    if len(node.children) == 1 and \
       any([isinstance(node, ntype) for ntype in [exp, logic, order, add, mul, 
                                                  unary, atom, stmt.stmt, 
                                                  stmt.stmts, block.decls]]):
        return [node.children[0]]
    elif any([parser.istoken(node, t) for t in ["[", "]", "(", ")", ";", "|",
                                                ":", ":="]]):
        return []
    else:
        return [node]

import trex
import reader

identities = [trex.trex(parser.pushstream(
    lex.lex(reader.stringreader(s)))) for s in 
              ['"0";"+";x:.;^>add>',     # 0 + x == x
               'x:.;"+";"0";^>add>',     # x + 0 == x
               'x:.;"-";"0";^>add>',     # x - 0 == x
               'x:"OMEGA";"+";.;^>add>', # OMEGA + x == OMEGA
               'x:"OMEGA";"-";.;^>add>', # OMEGA - x == OMEGA
               '.;"+";x:"OMEGA";^>add>', # x + OMEGA == OMEGA

               '"1";"*";x:.;^>mul>',     # 1 * x == x
               'x:.;"*";"1";^>mul>',     # x * 1 == x
               'x:.;"/";"1";^>mul>',     # x / 1 == x
               'x:"0";"*";.;^>mul>',     # 0 * x == 0
               'x:"0";"/";.;^>mul>',     # 0 / x == 0
               '.;"*";x:"0";^>mul>',     # x * 0 == 0
           ]]

assert all(i.parse() for i in identities)

def simplify_arith(node):
    c = node.children
    if not (type(node) in {add, mul}) or len(c) < 3:
        return False

    for i in identities:
        ctx = trex.context([node], 0, {})
        if i.match(ctx):
            assert "x" in ctx.out
            node.children = [ctx.out["x"]]
            return True
    return False
        
def tmp(node):
    def eq(pos, val):
        return parser.istoken(c[pos], val)

    assert len(c) == 3
    if isinstance(node, add):
        if eq(0, "0") and eq(1, "+"):                       # 0 + x == x
            c[0:2] = []
        elif eq(2, "0") and (eq(1, "+") or eq(1, "-")):     # x + 0 == x
            c[1:3] = []                                     # x - 0 == x
        elif eq(0, "OMEGA") and (eq(1, "+") or eq(1, "-")): # O + x == O
            c[1:3] = []                                     # O - x == O
        elif eq(2, "OMEGA") and eq(1, "+"):                 # x + O == O
            c[0:2] = []
    elif isinstance(node, mul):
        if eq(0, "1") and eq(1, "*"):                       # 1 * x == x
            c[0:2] = []
        elif eq(2, "1") and (eq(1, "*") or eq(1, "/")):     # x * 1 == x
            c[0:3] = []                                     # x / 1 == x
        elif eq(0, "0") and (eq(1, "*") or eq(1, "/")):     # 0 * x == 0
            c[0:3] = []                                     # 0 / x == 0
        elif eq(2, "0") and eq(1, "*"):                     # x * 0 == 0
            c[0:2] = []
    return len(c) != 3

import stmt
import block
