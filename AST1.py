class ASTNode:
        pass

class Program(ASTNode):
    def __init__(self, body: 'Block'):
        self.body = body

class Block(ASTNode):
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements

    def visit(self, codegen: "CodeGenerator") -> None:
        for stmt in self.statements:
            codegen.visit(stmt)

class Assignment(ASTNode):
    def __init__(self, target: "Identifier", value: ASTNode):
        self.target = target
        self.value = value

class Print(ASTNode):
    def __init__(self, expr: ASTNode):
        self.expr = expr

class If(ASTNode):
    def __init__(self, cond: ASTNode, then_branch: Block, else_branch: Optional[Block]):
        self.cond = cond
        self.then_branch = then_branch
        self.else_branch = else_branch

class While(ASTNode):
    def __init__(self, cond: ASTNode, body: Block):
        self.cond = cond
        self.body = body

class For(ASTNode):
    def __init__(self, var: "Identifier", iterable: ASTNode, body: Block):
        self.var = var
        self.iterable = iterable
        self.body = body

class FunctionDef(ASTNode):
    def __init__(self, name: str, params: List[str], body: Block):
        self.name = name
        self.params =  params
        self.body = body

class FunctionCall(ASTNode):
    def __init__(self, name: str, args: List[ASTNode]):
        self.name = name
        self.args = args

class Return(ASTNode):
    def __init__(self, expr: ASTNode):
        self.expr = expr

class BinOp(ASTNode):
    def __init__(self, left: ASTNode, op: str, right: ASTNode):
        self.left = left
        self.op = op
        self.right = right

class UnaryOp(ASTNode):
    def __init__(self, op: str, expr: ASTNode):
        self.op = op
        self.expr = expr

class Literal(ASTNode):
    def __init__(self, value: Union[int, str]):
        self.value = value

class Identifier(ASTNode):
    def __init__(self, name: str, line: int, col: int):
        self.name = name
        self.line = line
        self.col = col

class ArrayReference(ASTNode):
    def __init__(self, name: str, index: ASTNode):
        self.name = name
        self.index = index