from typing import List, Optional


class Parser:
    def __init__(self, tokens: List[Token], errors: ErrorReporter):
        self.tokens = tokens
        self.errors = errors
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        self.pos += 1
        return self.tokens[self.pos - 1]

    def expect(self, type: str, value: Optional[str] = None) -> Optional[Token]:
        tok = self.current()
        if tok.type != type or (value is not None and tok.value != value):
            self.errors.add_error(tok.line, f"Expected {type} {value if value else ''}")
            return None
        return self.advance()


    def parse_program(self) -> Program:
        stmts: List[ASTNode] = []

        while self.current().type != 'EOF':
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            else:
                self.advance()

        return Program(Block(stmts))

    def parse_statement(self) -> Optional[ASTNode]:
        tok = self.current()

        if tok.type == 'KEYWORD':

            if tok.value == 'if':
                return self.parse_if()

            if tok.value == 'while':
                return self.parse_while()

            if tok.value == 'for':
                return self.parse_for()

            if tok.value == 'def':
                return self.parse_function_def()

            if tok.value == 'return':
                self.advance()
                expr = self.parse_expression()
                return Return(expr)

        elif tok.type == 'IDENTIFIER':

            next_tok = self.tokens[self.pos + 1]

            # assignment
            if next_tok.type == 'OPERATOR' and next_tok.value == '=':
                return self.parse_assignment()

            # function call expression statement
            if next_tok.type == 'PUNCTUATION' and next_tok.value == '(':
                _ = self.parse_expression()
                return None

            self.errors.add_error(tok.line, f"Unexpected token {tok.type} {tok.value}")
            self.advance()
            return None

        self.errors.add_error(tok.line, f"Unexpected token {tok.type} {tok.value}")
        self.advance()
        return None

    def parse_assignment(self) -> Assignment:
        target_token = self.advance()  # Identifier
        self.expect('OPERATOR', '=')
        value = self.parse_expression()

        return Assignment(
            Identifier(target_token.value, target_token.line, target_token.column),
            value
        )

    def parse_if(self) -> If:
        self.advance()
        cond = self.parse_expression()
        self.expect('PUNCTUATION', ':')
        then_block = self.parse_indented_block()

        else_block = None
        if self.current().type == 'KEYWORD' and self.current().value == 'else':
            self.advance()
            self.expect('PUNCTUATION', ':')
            else_block = self.parse_indented_block()

        return If(cond, then_block, else_block)

    def parse_for(self) -> For:
        self.advance()
        var_tok = self.expect('IDENTIFIER')
        self.expect('KEYWORD', 'in')
        iterable = self.parse_expression()
        self.expect('PUNCTUATION', ':')
        body = self.parse_indented_block()

        return For(
            Identifier(var_tok.value, var_tok.line, var_tok.column),
            iterable,
            body
        )

    def parse_while(self) -> While:
        self.advance()
        cond = self.parse_expression()
        self.expect('PUNCTUATION', ':')
        body = self.parse_indented_block()
        return While(cond, body)

    def parse_function_def(self) -> FunctionDef:
        self.advance()
        name_tok = self.expect('IDENTIFIER')

        self.expect('PUNCTUATION', '(')

        params: List[str] = []

        while self.current().type != 'PUNCTUATION' or self.current().value != ')':
            param_tok = self.expect('IDENTIFIER')
            params.append(param_tok.value)

            if self.current().value == ',':
                self.advance()

        self.expect('PUNCTUATION', ')')
        self.expect('PUNCTUATION', ':')

        body = self.parse_indented_block()

        return FunctionDef(name_tok.value, params, body)

    def parse_indented_block(self) -> Block:
        self.expect('IDENT')  # unchanged logic

        stmts: List[ASTNode] = []

        while self.current().type not in ('DEDENT', 'EOF'):
            stmt = self.parse_statement()

            if stmt:
                stmts.append(stmt)
            else:
                self.advance()

        if self.current().type == 'EOF':
            self.errors.add_error(self.current().line, 'Missing DEDENT before EOF')
        else:
            self.expect('DEDENT')

        return Block(stmts)


    def parse_expression(self) -> ASTNode:
        return self.parse_logic_or()

    def parse_logic_or(self) -> ASTNode:
        node = self.parse_logic_and()

        while self.current().type == 'OPERATOR' and self.current().value == 'or':
            op = self.advance().value
            right = self.parse_logic_and()
            node = BinOp(node, op, right)

        return node

    def parse_logic_and(self) -> ASTNode:
        node = self.parse_comparison()

        while self.current().type == 'OPERATOR' and self.current().value == 'and':
            op = self.advance().value
            right = self.parse_comparison()
            node = BinOp(node, op, right)

        return node

    def parse_comparison(self) -> ASTNode:
        node = self.parse_arith_expr()

        while (self.current().type == 'OPERATOR' and
               self.current().value in ('==', '!=', '<', '>', '<=', '>=')):
            op = self.advance().value
            right = self.parse_arith_expr()
            node = BinOp(node, op, right)

        return node

    def parse_arith_expr(self) -> ASTNode:
        node = self.parse_term()

        while self.current().type == 'OPERATOR' and self.current().value in ('+', '-'):
            op = self.advance().value
            right = self.parse_term()
            node = BinOp(node, op, right)

        return node

    def parse_term(self) -> ASTNode:
        node = self.parse_factor()

        while self.current().type == 'OPERATOR' and self.current().value in ('*', '/'):
            op = self.advance().value
            right = self.parse_factor()
            node = BinOp(node, op, right)

        return node

    def parse_factor(self) -> ASTNode:
        tok = self.current()

        if tok.type == 'OPERATOR' and tok.value in ('-', 'not'):
            op = self.advance().value
            expr = self.parse_factor()
            return UnaryOp(op, expr)

        if tok.type == 'PUNCTUATION' and tok.value == '(':
            self.advance()
            expr = self.parse_expression()
            self.expect('PUNCTUATION', ')')
            return expr

        if tok.type == 'NUMBER':
            val = int(self.advance().value)
            return Literal(val)

        if tok.type == 'STRING':
            val = self.advance().value
            return Literal(val)

        if tok.type == 'IDENTIFIER':
            ident_tok = self.advance()

            if self.current().type == 'PUNCTUATION' and self.current().value == '(':
                self.advance()

                args: List[ASTNode] = []

                while self.current().type != 'PUNCTUATION' or self.current().value != ')':
                    args.append(self.parse_expression())

                    if self.current().value == ',':
                        self.advance()

                self.expect('PUNCTUATION', ')')
                return FunctionCall(ident_tok.value, args)

            return Identifier(ident_tok.value, ident_tok.line, ident_tok.column)

        self.errors.add_error(tok.line, f"Unexpected token {tok.type} {tok.value} in factor")
        self.advance()
        return Literal(0)