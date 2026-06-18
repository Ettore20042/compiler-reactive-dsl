"""
Modulo: scope.py
Gestisce l'analisi degli scopi: dichiarazioni, visibilità variabili, registrazione funzioni.
"""
from .ast_nodes import *

class ScopeAnalyzer:
    """Visitor che analizza scope e dichiarazioni, popola symbol_table e functions."""

    def __init__(self):
        self.symbol_table = {}  # {var_name: type}
        # Registra le funzioni built-in per l'input utente di roboLang
        self.functions = {
            "read_int": TaskDecl("read_int", [], "int", []),
            "read_real": TaskDecl("read_real", [], "real", [])
        }     # {func_name: TaskDecl}
        self.current_func_ret_type = None

    def analyze(self, ast):
        """Prima passata: registra tutte le funzioni globalmente."""
        for stmt in ast:
            if isinstance(stmt, TaskDecl):
                if stmt.name in ["read_int", "read_real"]:
                    raise Exception(f"Errore: il nome '{stmt.name}' è riservato a una funzione built-in.")
                if stmt.name in self.functions:
                    raise Exception(f"Errore: funzione (task) '{stmt.name}' già definita.")
                self.functions[stmt.name] = stmt

        # Seconda passata: analizza scope per tutti gli statement
        for stmt in ast:
            stmt.accept(self)

    def visit(self, node):
        """Dispatch dinamico visitor pattern."""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: nodo non gestito in scope analysis: {type(node).__name__}")
        return method(node)

    def visit_TaskDecl(self, node):
        """Entra in scope locale della funzione."""
        old_table = self.symbol_table.copy()
        self.current_func_ret_type = node.ret_type

        # Registra i parametri come variabili locali
        for p in node.params:
            if p.name in self.symbol_table:
                raise Exception(f"Errore: parametro '{p.name}' duplicato.")
            self.symbol_table[p.name] = p.type

        # Visita il body della funzione
        for s in node.body:
            s.accept(self)

        # Ripristina lo scope globale
        self.symbol_table = old_table
        self.current_func_ret_type = None

    def visit_VarDecl(self, node):
        """Registra una variabile nello scope corrente."""
        if node.name in self.symbol_table:
            raise Exception(f"Errore: variabile '{node.name}' già dichiarata.")
        self.symbol_table[node.name] = node.type

    def visit_SetStmt(self, node):
        """Verifica che la variabile esista."""
        if node.name not in self.symbol_table:
            raise Exception(f"Errore: variabile '{node.name}' non dichiarata.")

    def visit_CallStmt(self, node):
        """Verifica che la funzione esista."""
        if node.name not in self.functions:
            raise Exception(f"Errore: funzione '{node.name}' non dichiarata.")

    def visit_ReturnStmt(self, node):
        """Verifica che il return sia dentro una funzione."""
        if self.current_func_ret_type is None:
            raise Exception("Errore: 'return' usato fuori da un task/funzione.")

    def visit_LogStmt(self, node):
        """Log statement: niente da verificare nello scope."""
        pass

    def _visit_conditional_loop(self, node):
        """Visita il corpo di when/while (mantiene lo stesso scope)."""
        for stmt in node.body:
            stmt.accept(self)

    def visit_WhenStmt(self, node):
        self._visit_conditional_loop(node)

    def visit_WhileStmt(self, node):
        self._visit_conditional_loop(node)

    def get_var_type(self, var_name):
        """Utility: restituisce il tipo di una variabile nello scope corrente."""
        if var_name in self.symbol_table:
            return self.symbol_table[var_name]
        raise Exception(f"Errore: variabile '{var_name}' non dichiarata.")
