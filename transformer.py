"""
Modulo: transformer.py
Converte l albero di parsing in AST basandosi sulle classi definite in ast_nodes.py.
"""
from lark import Transformer
from ast_nodes import *

class ASTTransformer(Transformer):
    def start(self, stmts):
        return stmts

    def task_decl(self, args):
        name = str(args[0])
        idx = 1
        params = []
        if isinstance(args[idx], list): # param_list returns a list
            params = args[idx]
            idx += 1

        ret_type = "void"
        if idx < len(args) and isinstance(args[idx], str) and args[idx] in ["int", "real", "bool", "string"]:
            ret_type = str(args[idx])
            idx += 1

        body = args[idx:]
        return TaskDecl(name, params, ret_type, body)

    def param_list(self, args):
        return args

    def param(self, args):
        return Param(str(args[0]), str(args[1]))

    def expr_list(self, args):
        return args

    def call_expr(self, args):
        name = str(args[0])
        call_args = args[1] if len(args) > 1 and isinstance(args[1], list) else []
        return CallExpr(name, call_args)

    def call_stmt(self, args):
        name = str(args[0])
        call_args = args[1] if len(args) > 1 and isinstance(args[1], list) else []
        return CallStmt(name, call_args)

    def return_stmt(self, args):
        value = args[0] if len(args) > 0 else None
        return ReturnStmt(value)

    def log_stmt(self, args):
        return LogStmt(args[0])

    def var_decl(self, args):
        return VarDecl(str(args[0]), str(args[1]), args[2])

    def set_stmt(self, args):
        return SetStmt(str(args[0]), args[1])

    def when_stmt(self, args):
        return WhenStmt(args[0], args[1:])

    def while_stmt(self, args):
        return WhileStmt(args[0], args[1:])

    def _fold_binops(self, args):
        left = args[0]
        i = 1
        while i < len(args):
            op = str(args[i])
            right = args[i+1]
            left = BinOp(left, op, right)
            i += 2
        return left

    def comp_expr(self, args):
        return self._fold_binops(args)

    def arith_expr(self, args):
        return self._fold_binops(args)

    def term(self, args):
        return self._fold_binops(args)

    def number(self, args):
        val = str(args[0])
        return Literal('real' if '.' in val else 'int', val)

    def string(self, args):
        return Literal('string', str(args[0]))

    def true_val(self, args):
        return Literal('bool', 'true')

    def false_val(self, args):
        return Literal('bool', 'false')

    def var(self, args):
        return VarMatch(str(args[0]))
