from typing import List, Set, Dict, Optional
from AST1 import (
    Program, Block, Assignment, If, While, For,
    FunctionDef, FunctionCall, Return,
    BinOp, UnaryOp, Literal, Identifier, ExprStmt, ASTNode, Print
)


class CodeGenerator:
    def __init__(self):
        self.header: List[str] = []
        self.data: List[str] = []
        self.text: List[str] = []
        self.vars: Set[str] = set()          # global variables
        self.label_count = 0
        
        self.current_function: Optional[str] = None
        self.func_end_label: Dict[str, str] = {}
        self.param_offsets: Dict[str, Dict[str, int]] = {}

    def new_label(self, prefix: str = "L") -> str:
        lbl = f"{prefix}{self.label_count}"
        self.label_count += 1
        return lbl

    def generate(self, program: Program) -> List[str]:
        self.header = [
            ".686p",
            ".model flat, stdcall",
            ".stack 4096",
            "ExitProcess proto,dwExitCode:dword",
            "printf PROTO C, format:PTR BYTE, ..."
        ]

        global_stmts = []
        func_defs = []
        self._extract_functions(program.body, global_stmts, func_defs)

        self.text = [".code", "main proc"]
        self.text.append("\tpush ebp")
        self.text.append("\tmov ebp, esp")

        for stmt in global_stmts:
            self.visit(stmt)

        self.text.append("\tmov esp, ebp")
        self.text.append("\tpop ebp")
        self.text.append("\tinvoke ExitProcess, 0")
        self.text.append("main endp")

        for func in func_defs:
            self._emit_function(func)

        self.text.append("end main")
        data_lines = [".data"]
        data_lines.extend(self.data)

        for var in sorted(self.vars):
            data_lines.append(f"\t{var} dd 0")

        return self.header + data_lines + self.text

    def _extract_functions(self, node: ASTNode, globals: List, funcs: List):
        """Collect FunctionDef nodes; everything else goes to globals."""
        if isinstance(node, Block):
            for stmt in node.statements:
                if isinstance(stmt, FunctionDef):
                    funcs.append(stmt)
                else:
                    globals.append(stmt)
        else:
            if isinstance(node, FunctionDef):
                funcs.append(node)
            else:
                globals.append(node)

    def _emit_function(self, node: FunctionDef):
        """Generate assembly for a single function."""
        self.current_function = node.name
        end_lbl = self.new_label(f"{node.name}_end")
        self.func_end_label[node.name] = end_lbl

        self.param_offsets[node.name] = {}
        offset = 8
        for param in node.params:
            self.param_offsets[node.name][param] = offset
            offset += 4

        self.text.append(f"{node.name} proc")
        self.text.append("\tpush ebp")
        self.text.append("\tmov ebp, esp")

        self.visit(node.body)

        self.text.append(f"{end_lbl}:")
        self.text.append("\tmov esp, ebp")
        self.text.append("\tpop ebp")
        self.text.append("\tret")
        self.text.append(f"{node.name} endp")

        self.current_function = None

    def visit(self, node: ASTNode):
        method_name = f"visit_{node.__class__.__name__.lower()}"
        method = getattr(self, method_name, None)
        if not method:
            raise NotImplementedError(f"No visitor for {node.__class__.__name__}")
        return method(node)

    def visit_program(self, node: Program):
        self.visit(node.body)

    def visit_block(self, node: Block):
        for stmt in node.statements:
            self.visit(stmt)


    def visit_assignment(self, node: Assignment):
        if isinstance(node.target, Identifier):
            self.vars.add(node.target.name)
            self.visit(node.value)
            self.text.append(f"\tmov {node.target.name}, eax")
        else:
            raise NotImplementedError("Array assignment not yet supported")

    def visit_exprstmt(self, node: ExprStmt):
        self.visit(node.expr)

    def visit_if(self, node: If):
        else_lbl = self.new_label("else")
        end_lbl = self.new_label("endif")

        self.visit(node.cond)
        self.text.append("\tcmp eax, 0")
        self.text.append(f"\tje {else_lbl}")

        self.visit(node.then_branch)
        self.text.append(f"\tjmp {end_lbl}")

        self.text.append(f"{else_lbl}:")
        if node.else_branch:
            self.visit(node.else_branch)

        self.text.append(f"{end_lbl}:")

    def visit_while(self, node: While):
        start = self.new_label("while")
        end = self.new_label("endwhile")

        self.text.append(f"{start}:")
        self.visit(node.cond)
        self.text.append("\tcmp eax, 0")
        self.text.append(f"\tje {end}")

        self.visit(node.body)
        self.text.append(f"\tjmp {start}")
        self.text.append(f"{end}:")

    def visit_functiondef(self, node: FunctionDef):

        raise RuntimeError("FunctionDef should not appear inside main code")

    def visit_return(self, node: Return):
        self.visit(node.expr)
        if self.current_function:
            self.text.append(f"\tjmp {self.func_end_label[self.current_function]}")
        else:
            self.text.append("\tret")

    def visit_functioncall(self, node: FunctionCall):
        # push arguments right to left
        for arg in reversed(node.args):
            self.visit(arg)
            self.text.append("\tpush eax")
        self.text.append(f"\tcall {node.name}")
        if node.args:
            self.text.append(f"\tadd esp, {len(node.args) * 4}")


    def visit_literal(self, node: Literal):
        self.text.append(f"\tmov eax, {node.value}")

    def visit_identifier(self, node: Identifier):
        # Check if it's a function parameter
        if self.current_function and node.name in self.param_offsets.get(self.current_function, {}):
            offset = self.param_offsets[self.current_function][node.name]
            self.text.append(f"\tmov eax, [ebp+{offset}]")
        else:
            self.text.append(f"\tmov eax, {node.name}")

    def visit_binop(self, node: BinOp):
        self.visit(node.left)
        self.text.append("\tpush eax")
        self.visit(node.right)
        self.text.append("\tmov ebx, eax")
        self.text.append("\tpop eax")

        if node.op == "+":
            self.text.append("\tadd eax, ebx")
        elif node.op == "-":
            self.text.append("\tsub eax, ebx")
        elif node.op == "*":
            self.text.append("\timul eax, ebx")
        elif node.op == "/":
            self.text.append("\tcdq")
            self.text.append("\tidiv ebx")
        elif node.op in ("==", "!=", "<", ">", "<=", ">="):
            set_map = {
                "==": "sete", "!=": "setne",
                "<": "setl", "<=": "setle",
                ">": "setg", ">=": "setge",
            }
            self.text.append("\tcmp eax, ebx")
            self.text.append("\tmov eax, 0")
            self.text.append(f"\t{set_map[node.op]} al")
            self.text.append("\tmovzx eax, al")
        elif node.op in ("and", "or"):
            self.text.append("\tcmp eax, 0")
            self.text.append("\tsetne al")
            self.text.append("\tmovzx eax, al")
            self.text.append("\tcmp ebx, 0")
            self.text.append("\tsetne bl")
            self.text.append("\tmovzx ebx, bl")
            if node.op == "and":
                self.text.append("\tand eax, ebx")
            else:
                self.text.append("\tor eax, ebx")
        else:
            raise NotImplementedError(f"Binary operator {node.op}")

    def visit_unaryop(self, node: UnaryOp):
        self.visit(node.expr)
        if node.op == "-":
            self.text.append("\tneg eax")
        elif node.op == "not":
            self.text.append("\tcmp eax, 0")
            self.text.append("\tsete al")
            self.text.append("\tmovzx eax, al")
        else:
            raise NotImplementedError(f"Unary operator {node.op}")

    def visit_print(self, node: Print):
        if not hasattr(self, '_printf_declared'):
            self._printf_declared = True
            if "printf PROTO" not in "\n".join(self.header):
                self.header.append("printf PROTO C, format:PTR BYTE, ...")

        expr = node.expr

        if isinstance(expr, Literal) and isinstance(expr.value, str):
            # Store string in .data with a label
            str_label = self.new_label("_str")
            escaped = expr.value.replace('"', '\\"')
            self.data.append(f'\t{str_label} db "{escaped}", 10, 0')
            self.text.append(f'\tinvoke printf, OFFSET {str_label}')
            return

        # Integer expression: evaluate, then print with "%d\n"
        self.visit(expr)          # result in eax
        # Create format string if not already created
        if not hasattr(self, '_fmt_int'):
            self._fmt_int = "_fmt_int"
            self.data.append(f'\t{self._fmt_int} db "%d", 10, 0')
        self.text.append(f'\tinvoke printf, OFFSET {self._fmt_int}, eax')



    def visit_arrayreference(self, node):
        raise NotImplementedError("ArrayReference not implemented")
    def visit_for(self, node):
        raise NotImplementedError("For loop not implemented")