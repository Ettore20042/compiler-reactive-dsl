"""
Modulo: semantic.py
Orchestratore dell'analisi semantica: coordina in sequenza lo ScopeAnalyzer e il TypeChecker.
Viene chiamato da main.py dopo la costruzione dell'AST.
"""
from .scope import ScopeAnalyzer
from .typechecker import TypeChecker


class SemanticAnalyzer:
    """Coordina le due fasi dell'analisi semantica in sequenza:
    1) Scope Analysis — controlla dichiarazioni e visibilità
    2) Type Checking — controlla la compatibilità dei tipi"""

    def __init__(self):
        self.scope_analyzer = ScopeAnalyzer()   # Fase 1: gestore di scope e dichiarazioni
        self.type_checker = None                # Fase 2: creato dopo la scope analysis

    def analyze(self, ast):
        """Esegue l'intera analisi semantica sull'AST.
        Se trova errori (variabile non dichiarata, tipo incompatibile, ecc.) lancia un'eccezione."""

        # Fase 1: Scope Analysis — popola la symbol_table e registra le funzioni
        self.scope_analyzer.analyze(ast)

        # Fase 2: Type Checking — usa i dati raccolti dalla Fase 1
        # Il TypeChecker riceve lo scope_analyzer per accedere a symbol_table e functions
        self.type_checker = TypeChecker(self.scope_analyzer)
        self.type_checker.check(ast)

    # --- Accessor Properties ---
    # Espongono i dati interni per uso esterno (es. dal codegen o dai test)

    @property
    def symbol_table(self):
        """Restituisce la tabella dei simboli (dizionario {nome_var: tipo})."""
        return self.scope_analyzer.symbol_table

    @property
    def functions(self):
        """Restituisce il dizionario delle funzioni registrate {nome_func: TaskDecl}."""
        return self.scope_analyzer.functions
