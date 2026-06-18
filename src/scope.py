"""
Modulo: scope.py
Gestisce la prima fase dell'analisi semantica: controlla che ogni variabile e funzione
sia dichiarata correttamente, che non ci siano duplicati, e che gli identificatori
siano usati solo nei contesti in cui sono visibili (scope).
Visita anche le sotto-espressioni per intercettare variabili non dichiarate in fase 1.
"""
from .ast_nodes import *


class ScopeAnalyzer:
    """Visitor che percorre l'AST per analizzare scope e dichiarazioni.
    Popola la symbol_table (variabili) e il dizionario functions (task)."""

    def __init__(self):
        self.symbol_table = {}      # Dizionario {nome_variabile: tipo} per lo scope corrente

        # Pre-registra le funzioni built-in di I/O di roboLang.
        # Sono rappresentate come TaskDecl fittizi (senza corpo) per uniformità
        self.functions = {
            "read_int": TaskDecl("read_int", [], "int", []),
            "read_real": TaskDecl("read_real", [], "real", [])
        }                           # Dizionario {nome_funzione: TaskDecl}

        self.current_func_ret_type = None  # Tipo di ritorno del task in cui ci troviamo (None se globale)

    def analyze(self, ast):
        """Esegue l'analisi in DUE PASSATE:
        Passata 1: registra tutte le funzioni globalmente (permette la mutua ricorsione)
        Passata 2: visita ogni statement per controllare scope e dichiarazioni"""

        # --- PASSATA 1: Registra tutte le funzioni ---
        for stmt in ast:
            if isinstance(stmt, TaskDecl):
                # Impedisce la ridefinizione dei nomi built-in riservati
                if stmt.name in ["read_int", "read_real"]:
                    raise Exception(f"Errore: il nome '{stmt.name}' è riservato a una funzione built-in.")
                # Impedisce la dichiarazione duplicata di funzioni
                if stmt.name in self.functions:
                    raise Exception(f"Errore: funzione (task) '{stmt.name}' già definita.")
                self.functions[stmt.name] = stmt

        # --- PASSATA 2: Analisi di scope su ogni statement ---
        for stmt in ast:
            stmt.accept(self)  # Invoca il visit corretto tramite il Visitor Pattern

    def visit(self, node):
        """Dispatch dinamico: dato un nodo, trova e chiama il metodo visit_NomeClasse corretto.
        Es: per un nodo VarDecl chiama self.visit_VarDecl(node)"""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: nodo non gestito in scope analysis: {type(node).__name__}")
        return method(node)

    # --- VISITA RICORSIVA DELLE ESPRESSIONI ---

    def _check_expr(self, expr):
        """Percorre ricorsivamente un nodo espressione per verificare che ogni
        variabile e funzione referenziata sia effettivamente dichiarata.
        Senza questo metodo, variabili non dichiarate dentro espressioni annidate
        sfuggirebbero alla Fase 1 e causerebbero un KeyError generico in Fase 2."""
        if isinstance(expr, VarMatch):
            # Controlla che la variabile referenziata esista nello scope corrente
            if expr.name not in self.symbol_table:
                raise Exception(f"Errore: variabile '{expr.name}' non dichiarata.")
        elif isinstance(expr, CallExpr):
            # Controlla che la funzione chiamata esista
            if expr.name not in self.functions:
                raise Exception(f"Errore: funzione '{expr.name}' non dichiarata.")
            # Controlla ricorsivamente ogni argomento della chiamata
            for arg in expr.args:
                self._check_expr(arg)
        elif isinstance(expr, BinOp):
            # Controlla ricorsivamente entrambi gli operandi
            self._check_expr(expr.left)
            self._check_expr(expr.right)
        # Literal: niente da controllare (è un valore costante)

    def visit_TaskDecl(self, node):
        """Analizza lo scope di una funzione (task).
        Crea un contesto locale temporaneo per i parametri e le variabili del corpo."""
        old_table = self.symbol_table.copy()    # Salva lo scope globale prima di entrare
        self.current_func_ret_type = node.ret_type  # Memorizza il tipo di ritorno atteso

        # BUG FIX: controlla i parametri duplicati solo tra di loro (insieme locale),
        # NON contro self.symbol_table. Questo permette lo shadowing legittimo
        # di variabili globali da parte dei parametri del task.
        seen_params = set()
        for p in node.params:
            if p.name in seen_params:
                raise Exception(f"Errore: parametro '{p.name}' duplicato nel task '{node.name}'.")
            seen_params.add(p.name)
            self.symbol_table[p.name] = p.type  # Registra il parametro nello scope locale

        # Visita tutti gli statement nel corpo del task
        for s in node.body:
            s.accept(self)

        # Ripristina lo scope globale (le variabili locali del task vengono "dimenticate")
        self.symbol_table = old_table
        self.current_func_ret_type = None

    def visit_VarDecl(self, node):
        """Registra una nuova variabile nello scope corrente.
        Solleva errore se la variabile è già stata dichiarata.
        Controlla anche le sotto-espressioni del valore iniziale."""
        # Controlla le espressioni nell'inizializzatore PRIMA di registrare la variabile
        self._check_expr(node.value)
        if node.name in self.symbol_table:
            raise Exception(f"Errore: variabile '{node.name}' già dichiarata.")
        self.symbol_table[node.name] = node.type  # Aggiunge {nome: tipo} alla symbol table

    def visit_SetStmt(self, node):
        """Verifica che la variabile assegnata esista e controlla le sotto-espressioni."""
        if node.name not in self.symbol_table:
            raise Exception(f"Errore: variabile '{node.name}' non dichiarata.")
        # Controlla che tutte le variabili nell'espressione del valore siano dichiarate
        self._check_expr(node.value)

    def visit_CallStmt(self, node):
        """Verifica che la funzione chiamata esista e controlla le sotto-espressioni degli argomenti."""
        if node.name not in self.functions:
            raise Exception(f"Errore: funzione '{node.name}' non dichiarata.")
        # Controlla ricorsivamente ogni argomento
        for arg in node.args:
            self._check_expr(arg)

    def visit_ReturnStmt(self, node):
        """Verifica che il return sia dentro un task e controlla l'espressione di ritorno."""
        if self.current_func_ret_type is None:
            raise Exception("Errore: 'return' usato fuori da un task/funzione.")
        # Controlla l'espressione di ritorno se presente
        if node.value is not None:
            self._check_expr(node.value)

    def visit_LogStmt(self, node):
        """Controlla le sotto-espressioni dell'argomento di log."""
        self._check_expr(node.expr)

    def _visit_conditional_loop(self, node):
        """Metodo condiviso per when e while: controlla la condizione e visita il corpo.
        Lo scope NON cambia (when e while non creano un nuovo ambito di visibilità)."""
        # Controlla che tutte le variabili nella condizione siano dichiarate
        self._check_expr(node.condition)
        for stmt in node.body:
            stmt.accept(self)

    def visit_WhenStmt(self, node):
        """Visita il corpo di un blocco when e controlla la condizione."""
        self._visit_conditional_loop(node)

    def visit_WhileStmt(self, node):
        """Visita il corpo di un ciclo while e controlla la condizione."""
        self._visit_conditional_loop(node)

    def get_var_type(self, var_name):
        """Utility: restituisce il tipo di una variabile o solleva errore se non esiste."""
        if var_name in self.symbol_table:
            return self.symbol_table[var_name]
        raise Exception(f"Errore: variabile '{var_name}' non dichiarata.")
