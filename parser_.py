class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0
        self.errors = []

    # -------------------------
    # Utility
    # -------------------------
    def cur(self):
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        return ("EOF", "")

    def eat(self, expected_type, expected_value=None):
        tok_type, tok_val = self.cur()

        if tok_type == expected_type:
            if expected_value is None or tok_val == expected_value:
                self.i += 1
                return tok_val

        self.errors.append(
            f"Syntax error: expected {expected_type} but got {tok_type} ({tok_val})"
        )
        self.i += 1
        return None

    # -------------------------
    # PROGRAM
    # -------------------------
    def parse(self):
        while self.i < len(self.tokens):
            self.statement()

        if self.errors:
            print("\nSYNTAX ERRORS:")
            for e in self.errors:
                print(e)
        else:
            print("Parse successful (no syntax errors).")

    # -------------------------
    # STATEMENT
    # -------------------------
    def statement(self):
        # IDENTIFIER = expr
        if self.cur()[0] == "IDENTIFIER":
            name = self.eat("IDENTIFIER")

            # assignment
            if self.cur()[1] == "=":
                self.eat("OPERATOR")  # '=' treated as operator
                self.expr()
            else:
                self.errors.append("Expected '=' after identifier")

    # -------------------------
    # EXPRESSION
    # -------------------------
    def expr(self):
        self.term()

        while self.i < len(self.tokens) and self.cur()[1] in ["+", "-"]:
            op = self.eat("OPERATOR")
            self.term()

    # -------------------------
    # TERM
    # -------------------------
    def term(self):
        tok_type, tok_val = self.cur()

        if tok_type == "IDENTIFIER":
            self.eat("IDENTIFIER")

        elif tok_type == "INTEGER":
            self.eat("INTEGER")

        else:
            self.errors.append(f"Invalid term: {tok_val}")
            self.i += 1