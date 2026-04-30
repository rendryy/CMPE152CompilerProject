class CodeGen:
    def __init__(self):
        self.code = []

    def emit(self, instruction):
        self.code.append(instruction)

    def print_code(self):
        for line in self.code:
            print(line)