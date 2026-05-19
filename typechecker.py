"""
Modulo: typechecker.py
Esegue il type checking: verificare compatibilita' di tipi, cast impliciti, coercion.
"""
from ast_nodes import *


class TypeChecker:
    """Visitor che verifica la compatibilita' dei tipi su tutto l'AST."""

    def __init__(self, scope_analyzer):
        """scope_analyzer contiene gia' la symbol_table e le funzioni."""
        self.symbol_table = scope_analyzer.symbol_table
        self.functions = scope_analyzer.functions
        self.current_func_ret_type = None

    def check(self, ast):
        """Esegue type checking su tutto l'AST."""
        for stmt in ast:
            stmt.accept(self)

    def visit(self, node):
        """Dispatch dinamico visitor pattern."""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: nodo non gestito in type checking: {type(node).__name__}")
        return method(node)

    def visit_TaskDecl(self, node):
        """Visita il body della funzione mantenendo il contesto del return type."""
        # Salva lo scope attuale e aggiungi i parametri
        old_table = self.symbol_table.copy()
        old_ret_type = self.current_func_ret_type
        self.current_func_ret_type = node.ret_type

        # Registra i parametri nello scope locale
        for p in node.params:
            self.symbol_table[p.name] = p.type

        # Visita il body
        for s in node.body:
            s.accept(self)

        # Ripristina lo scope globale
        self.symbol_table = old_table
        self.current_func_ret_type = old_ret_type

    def visit_VarDecl(self, node):
        """Verifica che il tipo dell'inizializzatore sia compatibile con la dichiarazione."""
        expr_type = self.get_expr_type(node.value)
        if not self._is_compatible(node.type, expr_type):
            raise Exception(
                f"Errore di tipo: '{node.name}' attende '{node.type}', ottenuto '{expr_type}'."
            )

    def visit_SetStmt(self, node):
        """Verifica che il tipo assegnato sia compatibile con il tipo della variabile."""
        var_type = self.symbol_table[node.name]
        expr_type = self.get_expr_type(node.value)
        if not self._is_compatible(var_type, expr_type):
            raise Exception(
                f"Errore di tipo in assegnazione: '{node.name}' attende '{var_type}', ottenuto '{expr_type}'."
            )

    def visit_CallStmt(self, node):
        """Verifica i tipi degli argomenti passati alla funzione."""
        self._check_function_call(node.name, node.args)

    def visit_ReturnStmt(self, node):
        """Verifica che il tipo del return sia compatibile con il return type della funzione."""
        if node.value is None:
            if self.current_func_ret_type != "void":
                raise Exception(
                    f"Errore: la funzione attende un ritorno di tipo '{self.current_func_ret_type}'."
                )
            return

        ret_type = self.get_expr_type(node.value)
        if not self._is_compatible(self.current_func_ret_type, ret_type):
            raise Exception(
                f"Errore di tipo: return attende '{self.current_func_ret_type}', ottenuto '{ret_type}'."
            )

    def visit_LogStmt(self, node):
        """Calcola il tipo dell'espressione loggata (viene usato dal codegen)."""
        node.expr_type = self.get_expr_type(node.expr)

    def _visit_conditional_loop(self, node):
        """Verifica che la condizione sia booleana e visita il body."""
        cond_type = self.get_expr_type(node.condition)
        if cond_type != 'bool':
            raise Exception(f"Errore: condizione deve essere 'bool', ottenuto '{cond_type}'.")
        for stmt in node.body:
            stmt.accept(self)

    def visit_WhenStmt(self, node):
        self._visit_conditional_loop(node)

    def visit_WhileStmt(self, node):
        self._visit_conditional_loop(node)

    def _is_compatible(self, target_type, source_type):
        """Verifica se source_type puo' essere assegnato a target_type."""
        if target_type == source_type:
            return True
        # Cast implicito: int -> real
        if target_type == 'real' and source_type == 'int':
            return True
        return False

    def _check_function_call(self, func_name, args):
        """Verifica la compatibilita' dei tipi degli argomenti."""
        if func_name not in self.functions:
            raise Exception(f"Errore: funzione '{func_name}' non dichiarata.")
        func = self.functions[func_name]
        if len(args) != len(func.params):
            raise Exception(
                f"Errore: funzione '{func_name}' aspetta {len(func.params)} argomenti, ottenuti {len(args)}."
            )
        for i, arg in enumerate(args):
            arg_type = self.get_expr_type(arg)
            param_type = func.params[i].type
            if not self._is_compatible(param_type, arg_type):
                raise Exception(
                    f"Errore di tipo nell'argomento {i+1} di '{func_name}': atteso '{param_type}', ottenuto '{arg_type}'."
                )
        return func.ret_type

    def get_expr_type(self, node):
        """Dispatch dinamico per il calcolo del tipo di un'espressione."""
        method_name = f"expr_type_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: espressione non gestita: {type(node).__name__}")
        return method(node)

    def expr_type_Literal(self, node):
        return node.type

    def expr_type_CallExpr(self, node):
        return self._check_function_call(node.name, node.args)

    def expr_type_VarMatch(self, node):
        return self.symbol_table[node.name]

    def expr_type_BinOp(self, node):
        l_type = self.get_expr_type(node.left)
        r_type = self.get_expr_type(node.right)
        if node.op in ['>', '<', '>=', '<=', '==', '!=']:
            return 'bool'
        if l_type == 'real' or r_type == 'real':
            return 'real'
        return 'int'


