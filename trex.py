import parser
import lex

'''
trex   ::= seq '>' seq '>' seq
seq    ::= [ term { '|' term } ]
term   ::= factor { ';' factor }
factor ::= unary [ '*' | '+' ]
unary  ::= [ identifier ':' ] atom
atom   ::= '.' | string | identifier | '^' | '(' trex ')'
'''

class trexnode(parser.node):
    def match(self, ctx):
        ctx.push()
        result = self.check(ctx)
        ctx.pop() if result else ctx.rollback()
        return result

class trex(trexnode):
    def parse(self):
        return self.parseadd(seq) and self.oneof([lex.gt]) and \
            self.parseadd(seq) and self.oneof([lex.gt]) and \
            self.parseadd(seq)

    def check(self, ctx):
        assert len(ctx.nodes) == 1
        node = ctx.nodes[0]
        parent = node.parent
        ancestors = []
        while parent != None:
            ancestors += [parent]
            parent = parent.parent

        return self.children[0].match(context(node.children, 0, ctx.out)) and \
            self.children[2].match(context([node], 0, ctx.out)) and \
            self.children[4].match(context(ancestors, 0, ctx.out))
            

class seq(trexnode):
    def parse(self):
        return self.nlist(term, [lex.bar], parser.ASSOC_LEFT, 0)

    def check(self, ctx):
        return not self.children or any(a.match(ctx) for a in self.children[0::2])

class term(trexnode):
    def parse(self):
        return self.nlist(factor, [lex.semicolon], parser.ASSOC_NONE, 1)

    def check(self, ctx):
        return all(a.match(ctx) for a in self.children[0::2])

class factor(trexnode):
    def parse(self):
        if self.parseadd(unary):
            self.push()
            if self.oneof([lex.asterisk, lex.plus]):
                self.pop()
            else:
                self.rollback()
            return True
        return False

    def check(self, ctx):
        if len(self.children) == 1:
            return self.children[0].match(ctx)
        else:
            i = 0
            while self.children[0].match(ctx):
                i += 1
            minnr = {"*" : 0, "+" : 1}[self.children[1].body]
            return i >= minnr

class unary(trexnode):
    def parse(self):
        self.push()
        if self.oneof([lex.identifier]) and self.oneof([lex.colon]):
            self.pop()
        else:
            self.rollback()
        return self.parseadd(atom)

    def check(self, ctx):
        pos = ctx.pos
        result = self.children[-1].match(ctx)
        if result and len(self.children) > 1 and pos < len(ctx.nodes):
            key = self.children[0].body
            assert not key in ctx.out
            ctx.out[key] = ctx.nodes[pos]
        return result

class atom(trexnode):
    def parse(self):
        next = self.oneofdict({lex.identifier : True, lex.dot : True,
                               lex.caret : True, lex.stringliteral : True, 
                               lex.left_paren : +2})
        if next == +2:
            return self.parseadd(trex) and self.oneof([lex.right_paren])
        else:
            return next

    def check(self, ctx):
        token = self.children[0]
        ttype = type(token)
        if ctx.pos == len(ctx.nodes):
            return ttype == lex.caret
        elif ttype == lex.left_paren:
            return self.children[1].match(context([ctx.nodes[ctx.pos]], 
                                                  0, ctx.out))
        else:
            node = ctx.nodes[ctx.pos]
            if (ttype == lex.dot or \
                (ttype == lex.stringliteral and \
                 parser.istoken(node, token.value)) or \
                (ttype == lex.identifier and \
                 node.__class__.__name__ == token.body)):
                ctx.pos += 1
                return True
        return False

class context(object):
    def __init__(self, nodes, pos, out):
        self.nodes = nodes
        self.pos   = pos
        self.out   = out
        self.marks = []

    def push(self):
        self.marks.append((self.pos, self.out.copy()))

    def pop(self):
        self.marks.pop()

    def rollback(self):
        self.pos, self.out = self.marks.pop()


if __name__ == "__main__":
    import sys
    import grammar
    import reader
    import exp
    import block

    te = trex(parser.pushstream(lex.lex(reader.filereader(sys.stdin))))
    assert te.parse()
    print(te.pprint())

    program = """
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
                     z1 : xx |]]]]]
"""
    
    s = grammar.S(parser.pushstream(lex.lex(reader.stringreader(program))))
    s.parse()
    assert s.atend() 
    s.visit(grammar.parentset)
    s.visit(grammar.tokenset)
    s.reform([exp.simplify_depth], [exp.simplify_arith])
    s.visit(grammar.parentset)
    s.visit(block.blockset)
    s.visit(block.declsset)
    s.visit(block.namecheck)
    print(s.pprint())

    def trymatch(node, parent):
        ctx = context([node], 0, {})
        if te.match(ctx):
            print("{}: {} ({})".format(node.printexp(), ctx.out, ctx.pos))
        return True

    s.visit(trymatch)
