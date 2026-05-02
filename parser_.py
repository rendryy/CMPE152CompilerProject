from typing import List, Optional
from lexer import Token, TokenType
from AST1 import (
    ASTNode, Program, Block, Assignment, If, While, For,
    FunctionDef, FunctionCall, Return, BinOp, UnaryOp,
    Literal, Identifier, ExprStmt, Print
)

class ErrorReporter:
    def __init__(self):
        self.errors = []
    def add_error(self, line, msg):
        self.errors.append((line, msg))

class Parser:
    def __init__(self, tokens: List[Token], errors: ErrorReporter):
        self.tokens = tokens
        self.errors = errors
        self.pos = 0

    def current(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def advance(self) -> Token:
        self.pos += 1
        return self.tokens[self.pos - 1]

    def expect(self, typ: str, value: Optional[str] = None) -> Optional[Token]:
        tok = self.current()
        if tok.type != typ or (value is not None and tok.value != value):
            self.errors.add_error(tok.line_number, f"Expected {typ} {value if value else ''}, got {tok.type} {tok.value}")
            return None
        return self.advance()

    def skip_newlines(self):
        while self.current().type == 'NEWLINE':
            self.advance()

    # Program
    def parse_program(self) -> Program:
        stmts = []
        self.skip_newlines()
        while self.current().type != 'EOF':
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            self.skip_newlines()
        return Program(Block(stmts))

    # Statements
    def parse_statement(self) -> Optional[ASTNode]:
        self.skip_newlines()
        tok = self.current()
        if tok.type == 'KEYWORD':
            if tok.value == 'if': return self.parse_if()
            if tok.value == 'while': return self.parse_while()
            if tok.value == 'for': return self.parse_for()
            if tok.value == 'def': return self.parse_function_def()
            if tok.value == 'return':
                self.advance()
                expr = self.parse_expression()
                return Return(expr)
            if tok.value == 'print':
                self.advance()
                expr = self.parse_expression()
                return Print(expr)
        elif tok.type == 'IDENTIFIER':
            # look ahead to decide
            if self.pos + 1 < len(self.tokens):
                nxt = self.tokens[self.pos + 1]
                if nxt.type == 'OPERATOR' and nxt.value == '=':
                    return self.parse_assignment()
                if nxt.type == 'PUNCTUATION' and nxt.value == '(':
                    expr = self.parse_expression()
                    return ExprStmt(expr)
            self.errors.add_error(tok.line_number, f"Unexpected identifier {tok.value}")
            self.advance()
            return None
        else:
            self.errors.add_error(tok.line_number, f"Unexpected token {tok.type} {tok.value}")
            self.advance()
            return None

    def parse_assignment(self) -> Optional[Assignment]:
        ident = self.advance()  # IDENTIFIER
        if not self.expect('OPERATOR', '='):
            return None
        value = self.parse_expression()
        return Assignment(Identifier(ident.value, ident.line_number, ident.column), value)

    # Control flow
    def parse_if(self) -> If:
        self.advance()
        cond = self.parse_expression()
        self.expect('OPERATOR', ':')        
        then_block = self.parse_indented_block()
        else_block = None
        self.skip_newlines()
        if self.current().type == 'KEYWORD' and self.current().value == 'else':
            self.advance()
            self.expect('OPERATOR', ':')
            else_block = self.parse_indented_block()
        return If(cond, then_block, else_block)

    def parse_while(self) -> While:
        self.advance()
        cond = self.parse_expression()
        self.expect('OPERATOR', ':')
        body = self.parse_indented_block()
        return While(cond, body)

    def parse_for(self) -> For:
        self.advance()
        var_tok = self.expect('IDENTIFIER')
        if not var_tok:
            return For(Identifier("",0,0), Literal(0), Block([]))
        self.expect('KEYWORD', 'in')
        iterable = self.parse_expression()
        self.expect('OPERATOR', ':')
        body = self.parse_indented_block()
        return For(Identifier(var_tok.value, var_tok.line_number, var_tok.column), iterable, body)

    def parse_function_def(self) -> FunctionDef:
        self.advance()  # 'def'
        name_tok = self.expect('IDENTIFIER')
        if not name_tok:
            return FunctionDef("", [], Block([]))
        self.expect('PUNCTUATION', '(')
        params = []
        while not (self.current().type == 'PUNCTUATION' and self.current().value == ')'):
            param_tok = self.expect('IDENTIFIER')
            if param_tok:
                params.append(param_tok.value)
            # handle comma: skip if present
            if self.current().type == 'OPERATOR' and self.current().value == ',':
                self.advance()
            if self.current().type == 'EOF':
                break
        self.expect('PUNCTUATION', ')')
        self.expect('OPERATOR', ':')
        body = self.parse_indented_block()
        return FunctionDef(name_tok.value, params, body)

    def parse_indented_block(self) -> Block:
        self.skip_newlines()
        if not self.expect('INDENT'):
            return Block([])
        stmts = []
        self.skip_newlines()
        while self.current().type not in ('DEDENT', 'EOF'):
            stmt = self.parse_statement()
            if stmt:
                stmts.append(stmt)
            self.skip_newlines()
        if self.current().type == 'EOF':
            self.errors.add_error(self.current().line_number, "Missing DEDENT before EOF")
        else:
            self.expect('DEDENT')
        return Block(stmts)

    # Expressions (precedence)
    def parse_expression(self) -> ASTNode:
        return self.parse_logic_or()

    def parse_logic_or(self) -> ASTNode:
        node = self.parse_logic_and()
        while self.current().type == 'OPERATOR' and self.current().value == 'or':
            op = self.advance().value
            node = BinOp(node, op, self.parse_logic_and())
        return node

    def parse_logic_and(self) -> ASTNode:
        node = self.parse_comparison()
        while self.current().type == 'OPERATOR' and self.current().value == 'and':
            op = self.advance().value
            node = BinOp(node, op, self.parse_comparison())
        return node

    def parse_comparison(self) -> ASTNode:
        node = self.parse_arith_expr()
        while self.current().type == 'OPERATOR' and self.current().value in ('==','!=','<','>','<=','>='):
            op = self.advance().value
            node = BinOp(node, op, self.parse_arith_expr())
        return node

    def parse_arith_expr(self) -> ASTNode:
        node = self.parse_term()
        while self.current().type == 'OPERATOR' and self.current().value in ('+','-'):
            op = self.advance().value
            node = BinOp(node, op, self.parse_term())
        return node

    def parse_term(self) -> ASTNode:
        node = self.parse_unary()
        while self.current().type == 'OPERATOR' and self.current().value in ('*','/'):
            op = self.advance().value
            node = BinOp(node, op, self.parse_unary())
        return node

    def parse_unary(self) -> ASTNode:
        if self.current().type == 'OPERATOR' and self.current().value in ('-', 'not'):
            op = self.advance().value
            return UnaryOp(op, self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        tok = self.current()
        if tok.type == 'NUMBER':
            self.advance()
            return Literal(int(tok.value))
        if tok.type == 'STRING':
            self.advance()
            return Literal(tok.value)
        if tok.type == 'KEYWORD' and tok.value in ('True','False'):
            self.advance()
            return Literal(1 if tok.value == 'True' else 0)
        if tok.type == 'IDENTIFIER':
            ident = self.advance()
            if self.current().type == 'PUNCTUATION' and self.current().value == '(':
                self.advance()
                args = []
                if not (self.current().type == 'PUNCTUATION' and self.current().value == ')'):
                    args.append(self.parse_expression())
                    while self.current().type == 'OPERATOR' and self.current().value == ',':
                        self.advance()
                        args.append(self.parse_expression())
                self.expect('PUNCTUATION', ')')
                return FunctionCall(ident.value, args)
            return Identifier(ident.value, ident.line_number, ident.column)
        if tok.type == 'PUNCTUATION' and tok.value == '(':
            self.advance()
            expr = self.parse_expression()
            self.expect('PUNCTUATION', ')')
            return expr
        self.errors.add_error(tok.line_number, f"Unexpected token in primary: {tok.type} {tok.value}")
        self.advance()
        return Literal(0)