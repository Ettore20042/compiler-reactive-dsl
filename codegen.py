"""
Modulo: codegen.py
Implementa il generatore di codice. Visita l AST validato semanticamente e genera il file in codice C.
"""
from ast_nodes import *

class CGenerator:
    def __init__(self):
        self.code = []
        self.indent_level = 1

    def indent(self):
        return "    " * self.indent_level

    def generate(self, ast):
        self.code.append("#include <stdio.h>")
        self.code.append("#include <stdbool.h>\n")

        # Forward declaration and implementation of tasks
        tasks = [n for n in ast if isinstance(n, TaskDecl)]
        for task in tasks:
            task.accept(self)
            self.code.append("")

        self.code.append("int main() {")
        for stmt in ast:
            if not isinstance(stmt, TaskDecl):
                stmt.accept(self)
        self.code.append("    return 0;")
        self.code.append("}\n")
        return "\n".join(self.code)

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: nodo non gestito in codegen: {type(node).__name__}")
        return method(node)

    def visit_TaskDecl(self, node):
        c_ret_type = self.map_type(node.ret_type)
        params_str = ", ".join([f"{self.map_type(p.type)} {p.name}" for p in node.params])
        if not params_str:
            params_str = "void"
        self.code.append(f"{c_ret_type} {node.name}({params_str}) {{")
        self.indent_level += 1
        for s in node.body:
            s.accept(self)
        self.indent_level -= 1
        self.code.append("}")

    def visit_CallStmt(self, node):
        args_str = ", ".join([self.expr_to_c(arg) for arg in node.args])
        self.code.append(f"{self.indent()}{node.name}({args_str});")

    def visit_ReturnStmt(self, node):
        if node.value:
            self.code.append(f"{self.indent()}return {self.expr_to_c(node.value)};")
        else:
            self.code.append(f"{self.indent()}return;")

    def visit_LogStmt(self, node):
        val = self.expr_to_c(node.expr)
        if node.expr_type == 'int' or node.expr_type == 'bool':
            fmt = "%d"
        elif node.expr_type == 'real':
            fmt = "%f"
        elif node.expr_type == 'string':
            fmt = "%s"
        else:
            fmt = "%d"
        self.code.append(f"{self.indent()}printf(\"{fmt}\\n\", {val});")

    def visit_VarDecl(self, node):
        c_type = self.map_type(node.type)
        val = self.expr_to_c(node.value)
        if c_type == "char*":
            self.code.append(f"{self.indent()}char* {node.name} = {val};")
        else:
            self.code.append(f"{self.indent()}{c_type} {node.name} = {val};")

    def visit_SetStmt(self, node):
        val = self.expr_to_c(node.value)
        self.code.append(f"{self.indent()}{node.name} = {val};")

    def _visit_conditional_loop(self, keyword, node):
        cond = self.expr_to_c(node.condition)
        self.code.append(f"{self.indent()}{keyword} ({cond}) {{")
        self.indent_level += 1
        for s in node.body:
            s.accept(self)
        self.indent_level -= 1
        self.code.append(f"{self.indent()}}}")

    def visit_WhenStmt(self, node):
        self._visit_conditional_loop("if", node)

    def visit_WhileStmt(self, node):
        self._visit_conditional_loop("while", node)

    def map_type(self, t):
        if t == "int": return "int"
        if t == "real": return "float"
        if t == "bool": return "bool"
        if t == "string": return "char*"
        if t == "void": return "void"
        return "void"

    def expr_to_c(self, node):
        method_name = f"expr_to_c_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: espressione non gestita in codegen: {type(node).__name__}")
        return method(node)

    def expr_to_c_Literal(self, node):
        return node.value

    def expr_to_c_CallExpr(self, node):
        args_str = ", ".join([self.expr_to_c(arg) for arg in node.args])
        return f"{node.name}({args_str})"

    def expr_to_c_VarMatch(self, node):
        return node.name

    def expr_to_c_BinOp(self, node):
        return f"({self.expr_to_c(node.left)} {node.op} {self.expr_to_c(node.right)})"
