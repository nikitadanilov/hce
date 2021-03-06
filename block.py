import parser
import lex

class block(parser.node):
    def __init__(self, seq):
        parser.node.__init__(self, seq)
        self.decls = {}

    def parse0(self):
        return self.oneof([lex.left_bracket]) and \
            self.parseadd(decls) and self.oneof([lex.bar]) and \
            self.parseadd(stmt.stmts) and self.oneof([lex.right_bracket])

    def lookup(self, name):
        return self.decls[name]

    def bound(self, name):
        return name in self.decls


class decls(parser.node):
    def parse0(self):
        return self.nlist(decl, [lex.semicolon], parser.ASSOC_NONE, 0)

class decl(parser.node):
    def parse0(self):
        return self.oneof([lex.identifier]) and \
            self.oneof([lex.colon]) and self.oneof([lex.identifier])

class duplicatename(parser.semanticserror):
    def __init__(self, token, name, orig):
        parser.languageerror.__init__(self, token, "duplicate name: " + \
                                      name + ", orig: " + str(orig.pos()))

class unknownname(parser.semanticserror):
    def __init__(self, token, name):
        parser.languageerror.__init__(self, token, "unknown name: " + name)

def blockset(node, parent):
    if parent:
        if isinstance(parent, block):
            node.block = parent
        else:
            node.block = parent.block
    return True

def declsset(node, parent):
    if isinstance(node, decl):
        v = node.children[0]
        name = v.body
        chain = node.boundchain(name)
        if chain:
            raise duplicatename(v.start, v.name(), chain[0])
        node.block.decls[name] = node
    return True

def allnames(node):
    names = {}
    for b in node.blockchain():
        names.update(b.decls) 
    return names

def namecheck(node, parent):
    if isinstance(node, lex.identifier):
        chain = node.boundchain(node.body)
        if chain:
            node.decl = chain[0]
        else:
            raise unknownname(node.start, node.name())
    return True

import stmt

