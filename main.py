import sys
from lexer import Lexer, Token, TokenType
from parser_ import Parser, ErrorReporter
from CODEGEN1 import CodeGenerator

def run_file(filename, output_file):
    with open(filename, "r") as f:
        source = f.read()

    errors = ErrorReporter()

    # LEX
    lexer = Lexer()
    tokens = lexer.tokenize(source)

    # PARSE
    parser = Parser(tokens, errors)
    ast = parser.parse_program()

    # CODEGEN
    codegen = CodeGenerator()
    asm = codegen.generate(ast)

    with open(output_file, "w") as f:
        f.write("\n".join(asm))

if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[3] if len(sys.argv) > 3 else "out.asm"

    run_file(input_file, output_file)