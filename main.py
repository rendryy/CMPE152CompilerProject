from lexer import Lexer
from parser_ import Parser 

def main():
    # -------------------------
    # READ SOURCE FILE
    # -------------------------
    with open("sample.txt", "r") as f:
        code = f.read()

    print("===== SOURCE CODE =====")
    print(code)

    # -------------------------
    # LEXICAL ANALYSIS
    # -------------------------
    lexer = Lexer(code)
    tokens = lexer.tokenize()

    print("\n===== TOKENS =====")
    for t in tokens:
        print(t)

    # -------------------------
    # PARSING + CODE GENERATION
    # -------------------------
    parser = Parser(tokens)
    parser.parse()

    # -------------------------
    # OUTPUT ERRORS (if any)
    # -------------------------
    if parser.errors:
        print("\n===== SYNTAX ERRORS =====")
        for e in parser.errors:
            print(e)
    else:
        print("\n===== NO SYNTAX ERRORS =====")

    # -------------------------
    # GENERATED CODE
    # -------------------------
    print("\n===== INTERMEDIATE CODE =====")
    parser.codegen.print_code()


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    main()