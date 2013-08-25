class reader(object):
    class pos(object):
        def __init__(self, reader):
            self.name = reader.name
            self.lineno = reader.lineno
            self.column = reader.column
            self.offset = reader.offset

        def __str__(self):
            return "{}:{}:{}".format(self.name,self.lineno, self.column)

    def __init__(self, name):
        self.name   = name
        self.lineno = 0
        self.column = 0
        self.offset = 0
        self.ahead  = ""
        self.eof    = False

    def posget(self):
        return reader.pos(self)

    def look(self, start, size):
        end = start + size
        while len(self.ahead) < end and not self.eof:
            ch = self.get()
            self.eof = (ch == "")
            self.ahead += ch
        return self.ahead[start : end]

    def move(self, count):
        count = min(count, len(self.ahead))
        for i in range(0, count):
            ch = self.ahead[i]
            if ch == "\n":
                self.lineno += 1
                self.column  = 0
            else:
                self.column += 1
        self.ahead = self.ahead[count:]
        self.offset += count
        return self.atend()

    def atend(self):
        return self.ahead == "" and self.eof

class filereader(reader):
    def __init__(self, file):
        reader.__init__(self, file.name)
        self.file = file

    def get(self):
        return self.file.read(1)

class stringreader(reader):
    def __init__(self, string):
        reader.__init__(self, "'" + string[:10] + "...'")
        self.string = string
        self.count  = 0

    def get(self):
        self.count += 1
        return self.string[self.count - 1 : self.count]

