import reader

class repreader(reader.reader):
    def __init__(self, prompt):
        reader.reader.__init__(self, "<rep>")
        self.prompt = prompt
        self.buf    = ""
        self.count  = 0

    def get(self):
        if len(self.buf) <= self.count:
            c = self.count > 0 and not self.buf[:self.count].isspace()
            inp = input(self.prompt[c])
            if inp[:1] == "~":
                eval(inp[1:])
                inp = ""
            # add some white space at the end to satisfy lexer token
            # look-ahead.
            self.buf += inp + 2 * " "
        ch = self.buf[self.count : self.count + 1]
        self.count += 1
        return ch

    def rest(self):
        return self.buf[self.count:]

import readline

if __name__ == "__main__":
    import proarkhe
    import grammar
    import parser
    import block
    import exp
    import lex

    while True:
        rep = repreader(["; ", "+ "])
        e   = grammar.S(parser.pushstream(lex.lex(rep)))

        try:
            parsed = e.parse()
        except EOFError:
            break
        except lex.lex.lexerror as lexexp:
            continue

        if not parsed:
            print("Cannot parse: '{}'@{} '{}'".format(rep.buf, 
                                                      rep.count, rep.rest()))
        elif rep.rest() and not rep.rest().isspace():
            # for whatever reason "".isspace() is False
            print("Garbage after S: '{}' ({})".format(rep.buf, len(rep.buf)))
        else:
            print(e.pprint())
            print(e.printexp())

            try:
                e.block = proarkhe.proarkhe()
                e.visit(grammar.parentset)
                e.walk(grammar.tokenset)
                e.reform([exp.simplify_depth], [exp.simplify_arith])
                e.visit(grammar.parentset)
                e.visit(block.blockset)
                e.visit(block.declsset)
                e.visit(block.namecheck)
                print(e.pprint())
                print(e.printexp())
            except parser.languageerror as langexp:
                print(str(langexp))
                continue
