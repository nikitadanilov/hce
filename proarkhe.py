import parser
import reader
import block
import lex

class proarkhe(block.block):
    class illiterate(reader.reader):
        def __init__(self):
            self.name   = "προαρχη"
            self.lineno = 0
            self.column = 0
            self.offset = 0

    def decladd(self, name, texp):
        d = block.decl(self.seq)
        p = self.seq.it.reader.posget()
        d.children.append(lex.identifier(name, p))
        d.children.append(lex.identifier(texp, p))
        self.children.append(d)
        self.decls[name] = d

    def __init__(self):
        import grammar
        block.block.__init__(self, 
                             parser.pushstream(lex.lex(proarkhe.illiterate())))
        self.decladd("OMEGA", "ordinals")
        self.decladd("natural", "type")
        self.decladd("integer", "type")
        self.decladd("real", "type")
        self.decladd("Boolean", "type")
        self.decladd("true", "Boolean")
        self.decladd("false", "Boolean")
        self.visit(grammar.parentset)
        self.walk(grammar.tokenset)
