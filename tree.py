class tnode(object):
    def __init__(self):
        self.children = []

    def name(self):
        return ""

    def pprint(self, start = 0, indent = 0):
        s = "".rjust(indent * 8 - start) + "(" + self.name()
        if self.children:
            s += ": "
            s += self.children[0].pprint(start + len(s), indent + 1)
            for c in self.children[1:]:
                s += "\n" + c.pprint(0, indent + 1)
        return s + ")"

    WALK_PRE  = 1
    WALK_IN   = 2
    WALK_POST = 3

    def walk(self, cb):
        cb(self, tnode.WALK_PRE)
        for c in self.children:
            c.walk(cb)
            cb(self, tnode.WALK_IN)
        cb(self, tnode.WALK_POST)

    def visit(self, cb):
        def visitnode(node, cb, parent):
            if cb(node, parent):
                for c in node.children:
                    visitnode(c, cb, node)
        visitnode(self, cb, None)

    def reform(self, mod, modchildren):
        def ref():
            for m in mod:
                reformed = [inner for outer in [m(c) for c in self.children] 
                            for inner in outer]
                if self.children != reformed:
                    self.children = reformed
                    return True
            return False

        def refchildren():
            return any([mc(self) for mc in modchildren])

        while True:
            for c in self.children:
                c.parent = self
                c.reform(mod, modchildren)
            if ref():
                continue
            if refchildren():
                continue
            break
        

