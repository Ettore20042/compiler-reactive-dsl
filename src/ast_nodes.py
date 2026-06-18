"""
Modulo: ast_nodes.py
Contiene le definizioni delle classi che rappresentano i nodi dell'AST.
"""
class ASTNode:
    def accept(self, visitor):
        return visitor.visit(self)

class TaskDecl(ASTNode):
    def __init__(self, name, params, ret_type, body):
        self.name = name
        self.params = params
        self.ret_type = ret_type
        self.body = body

class Param(ASTNode):
    def __init__(self, name, param_type):
        self.name = name
        self.type = param_type

class CallExpr(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class CallStmt(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class ReturnStmt(ASTNode):
    def __init__(self, value):
        self.value = value

class LogStmt(ASTNode):
    def __init__(self, expr):
        self.expr = expr

class VarDecl(ASTNode):
    def __init__(self, name, var_type, value):
        self.name = name
        self.type = var_type
        self.value = value

class SetStmt(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class WhenStmt(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class WhileStmt(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class BinOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Literal(ASTNode):
    def __init__(self, type, value):
        self.type = type
        self.value = value

class VarMatch(ASTNode):
    def __init__(self, name):
        self.name = name
