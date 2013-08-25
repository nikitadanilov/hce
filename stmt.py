import parser
import lex

class stmts(parser.node):
    def parse(self):
        return self.nlist(stmt, [lex.semicolon], parser.ASSOC_NONE, 0)

class stmt(parser.node):
    def parse(self):
        return self.alternative([assgn, block.block])

class assgn(parser.node):
    def parse(self):
        return self.oneof([lex.identifier]) and self.oneof([lex.assignment]) and \
            self.parseadd(exp.exp)

import block
import exp
