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

import stmt
import block
