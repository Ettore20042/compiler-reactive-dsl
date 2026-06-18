"""
Modulo: semantic.py
Orchestrazione dell'analisi semantica: coordina ScopeAnalyzer e TypeChecker.
"""
from .scope import ScopeAnalyzer
from .typechecker import TypeChecker

class SemanticAnalyzer:
    """Orchestrator che coordina scope analysis e type checking."""

    def __init__(self):
        self.scope_analyzer = ScopeAnalyzer()
        self.type_checker = None

    def analyze(self, ast):
        """Esegue prima lo scope analysis, poi il type checking."""
        # Fase 1: Scope Analysis
        self.scope_analyzer.analyze(ast)

        # Fase 2: Type Checking (il type checker accede ai dati della scope analysis)
        self.type_checker = TypeChecker(self.scope_analyzer)
        self.type_checker.check(ast)

    @property
    def symbol_table(self):
        return self.scope_analyzer.symbol_table

    @property
    def functions(self):
        return self.scope_analyzer.functions
