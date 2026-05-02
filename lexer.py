from typing import List


class TokenType:
    KEYWORD = 'KEYWORD'
    IDENTIFIER = 'IDENTIFIER'
    NUMBER = 'NUMBER'
    OPERATOR = 'OPERATOR'
    PUNCTUATION = 'PUNCTUATION'
    STRING = 'STRING'
    INDENT = 'INDENT'
    DEDENT = 'DEDENT'
    NEWLINE = 'NEWLINE'
    EOF = 'EOF'
    UNKNOWN = 'UNKNOWN'


class Token:
    def __init__(self, type_, value, line_number, column=0):
        self.type = type_
        self.value = value
        self.line_number = line_number
        self.column = column


class Lexer:
    def __init__(self):
        self.keywords = {
            "if", "else", "while", "for", "def", "return",
            "break", "continue", "import", "as", "from",
            "in", "range", "len", "True", "False", "not"
        }

        self.single_ops = {'+', '-', '*', '/', '=', '>', '<', '!', ',', ':'}
        self.double_ops = {'==', '>=', '<=', '!='}
        self.punctuations = {'(', ')', '{', '}'}

    def handle_indentation(self, lines: List[str]):
        tokens = []
        indent_stack = [0]
        line_number = 1

        for line in lines:
            stripped = line.lstrip()

            if stripped == '':
                line_number += 1
                continue

            indent = len(line) - len(stripped)

            if indent > indent_stack[-1]:
                indent_stack.append(indent)
                tokens.append(Token(TokenType.INDENT, '', line_number))

            while indent < indent_stack[-1]:
                indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, '', line_number))

            tokens.extend(self.tokenize_line(stripped, line_number))
            tokens.append(Token(TokenType.NEWLINE, '', line_number))

            line_number += 1

        # close remaining indents
        while len(indent_stack) > 1:
            indent_stack.pop()
            tokens.append(Token(TokenType.DEDENT, '', line_number))

        tokens.append(Token(TokenType.EOF, '', line_number))
        return tokens

    def tokenize(self, source_code: str):
        lines = source_code.split('\n')
        return self.handle_indentation(lines)

    def tokenize_line(self, line: str, line_number: int):
        tokens = []
        i = 0

        while i < len(line):
            ch = line[i]

            # skip whitespace
            if ch.isspace():
                i += 1
                continue
            if ch == '"' or ch == "'":
                quote = ch
                i += 1
                value = ''

                while i < len(line) and line[i] != quote:
                    value += line[i]
                    i += 1

                i += 1  # closing quote
                tokens.append(Token(TokenType.STRING, value, line_number))
                continue
            if ch.isdigit():
                num = ch
                i += 1

                while i < len(line) and line[i].isdigit():
                    num += line[i]
                    i += 1

                tokens.append(Token(TokenType.NUMBER, num, line_number))
                continue
            if ch.isalpha() or ch == '_':
                ident = ch
                i += 1

                while i < len(line) and (line[i].isalnum() or line[i] == '_'):
                    ident += line[i]
                    i += 1

                if ident in self.keywords:
                    tokens.append(Token(TokenType.KEYWORD, ident, line_number))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, ident, line_number))

                continue

            if i + 1 < len(line):
                pair = ch + line[i + 1]
                if pair in self.double_ops:
                    tokens.append(Token(TokenType.OPERATOR, pair, line_number))
                    i += 2
                    continue

            if ch in self.single_ops:
                tokens.append(Token(TokenType.OPERATOR, ch, line_number))
                i += 1
                continue
            if ch in self.punctuations:
                tokens.append(Token(TokenType.PUNCTUATION, ch, line_number))
                i += 1
                continue

            tokens.append(Token(TokenType.UNKNOWN, ch, line_number))
            i += 1

        return tokens