"""
Modulo: typechecker.py
Seconda fase dell'analisi semantica: verifica la compatibilità dei tipi in tutto l'AST.
Controlla assegnazioni, chiamate a funzione, return, condizioni booleane e cast impliciti.
"""
from .ast_nodes import *


class TypeChecker:
    """Visitor che verifica la compatibilità dei tipi su ogni nodo dell'AST.
    Riceve i dati già raccolti dallo ScopeAnalyzer (symbol_table e functions)."""

    def __init__(self, scope_analyzer):
        # Eredita la tabella dei simboli e le funzioni registrate dallo scope analyzer
        self.symbol_table = scope_analyzer.symbol_table   # {nome_var: tipo}
        self.functions = scope_analyzer.functions           # {nome_func: TaskDecl}
        self.current_func_ret_type = None  # Tipo di ritorno del task corrente (None se globale)

    def check(self, ast):
        """Punto di ingresso: visita ogni statement dell'AST per controllarne i tipi."""
        for stmt in ast:
            stmt.accept(self)

    def visit(self, node):
        """Dispatch dinamico: chiama il metodo visit_NomeClasse appropriato per ogni nodo."""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: nodo non gestito in type checking: {type(node).__name__}")
        return method(node)

    # --- VISIT DEI NODI PRINCIPALI ---

    def visit_TaskDecl(self, node):
        """Entra nello scope locale di un task: salva lo stato, registra i parametri,
        visita il corpo, e poi ripristina lo scope originale."""
        old_table = self.symbol_table.copy()        # Salva lo scope corrente
        old_ret_type = self.current_func_ret_type
        self.current_func_ret_type = node.ret_type  # Memorizza il tipo di ritorno atteso

        # Registra i parametri come variabili locali per il type checking del corpo
        for p in node.params:
            self.symbol_table[p.name] = p.type

        # Visita ogni statement nel corpo del task
        for s in node.body:
            s.accept(self)

        # Ripristina lo scope e il contesto del return precedenti
        self.symbol_table = old_table
        self.current_func_ret_type = old_ret_type

    def visit_VarDecl(self, node):
        """Verifica che il tipo dell'espressione iniziale sia compatibile con il tipo dichiarato.
        Es: var x: int = 5;  → OK (int == int)
        Es: var x: int = "ciao";  → ERRORE (int != string)"""
        expr_type = self.get_expr_type(node.value)  # Calcola il tipo dell'espressione
        if not self._is_compatible(node.type, expr_type):
            raise Exception(
                f"Errore di tipo: '{node.name}' attende '{node.type}', ottenuto '{expr_type}'."
            )
        # Registra la variabile nella symbol table per le istruzioni successive
        self.symbol_table[node.name] = node.type

    def visit_SetStmt(self, node):
        """Verifica che il tipo del valore assegnato sia compatibile con il tipo della variabile.
        Es: set x = 10;  → controlla che 10 (int) sia compatibile con il tipo di x"""
        var_type = self.symbol_table[node.name]     # Recupera il tipo dichiarato della variabile
        expr_type = self.get_expr_type(node.value)  # Calcola il tipo dell'espressione assegnata
        if not self._is_compatible(var_type, expr_type):
            raise Exception(
                f"Errore di tipo in assegnazione: '{node.name}' attende '{var_type}', ottenuto '{expr_type}'."
            )

    def visit_CallStmt(self, node):
        """Verifica che i tipi degli argomenti passati corrispondano ai parametri formali."""
        self._check_function_call(node.name, node.args)

    def visit_ReturnStmt(self, node):
        """Verifica la compatibilità del tipo restituito con il tipo di ritorno del task.
        Se il return è vuoto (None), il task deve essere void."""
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
        """Calcola e salva il tipo dell'espressione nel nodo LogStmt.
        Questo valore (node.expr_type) verrà letto dal Codegen per scegliere
        il formato printf corretto (%d per int, %f per real, %s per string)."""
        node.expr_type = self.get_expr_type(node.expr)

    def _visit_conditional_loop(self, node):
        """Verifica che la condizione di when/while sia di tipo bool, poi visita il corpo."""
        cond_type = self.get_expr_type(node.condition)
        if cond_type != 'bool':
            raise Exception(f"Errore: condizione deve essere 'bool', ottenuto '{cond_type}'.")
        for stmt in node.body:
            stmt.accept(self)

    def visit_WhenStmt(self, node):
        """Type check del blocco when (condizione + corpo)."""
        self._visit_conditional_loop(node)

    def visit_WhileStmt(self, node):
        """Type check del ciclo while (condizione + corpo)."""
        self._visit_conditional_loop(node)

    # --- METODI DI SUPPORTO ---

    def _is_compatible(self, target_type, source_type):
        """Verifica se source_type può essere assegnato a target_type.
        Tipi uguali sono sempre compatibili. In più, consente il cast implicito int → real
        (es: var x: real = 5; è valido perché 5 (int) viene promosso a real)."""
        if target_type == source_type:
            return True
        if target_type == 'real' and source_type == 'int':
            return True     # Cast implicito: int → real (widening)
        return False

    def _check_function_call(self, func_name, args):
        """Verifica una chiamata a funzione: controlla che la funzione esista,
        che il numero di argomenti sia corretto, e che ogni tipo corrisponda."""
        if func_name not in self.functions:
            raise Exception(f"Errore: funzione '{func_name}' non dichiarata.")
        func = self.functions[func_name]

        # Controlla che il numero di argomenti passati corrisponda ai parametri formali
        if len(args) != len(func.params):
            raise Exception(
                f"Errore: funzione '{func_name}' aspetta {len(func.params)} argomenti, ottenuti {len(args)}."
            )
        # Controlla che ogni argomento abbia un tipo compatibile col parametro corrispondente
        for i, arg in enumerate(args):
            arg_type = self.get_expr_type(arg)
            param_type = func.params[i].type
            if not self._is_compatible(param_type, arg_type):
                raise Exception(
                    f"Errore di tipo nell'argomento {i+1} di '{func_name}': atteso '{param_type}', ottenuto '{arg_type}'."
                )
        return func.ret_type  # Restituisce il tipo di ritorno della funzione (usato da get_expr_type)

    # --- INFERENZA DEL TIPO DELLE ESPRESSIONI ---

    def get_expr_type(self, node):
        """Dispatch dinamico per calcolare il tipo di un'espressione.
        Chiama il metodo expr_type_NomeClasse corretto per ogni tipo di nodo."""
        method_name = f"expr_type_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: espressione non gestita: {type(node).__name__}")
        return method(node)

    def expr_type_Literal(self, node):
        """Un letterale ha il tipo esplicito salvato nel nodo (int, real, string, bool)."""
        return node.type

    def expr_type_CallExpr(self, node):
        """Il tipo di una chiamata a funzione è il tipo di ritorno della funzione stessa."""
        return self._check_function_call(node.name, node.args)

    def expr_type_VarMatch(self, node):
        """Il tipo di un riferimento a variabile si trova nella symbol table."""
        return self.symbol_table[node.name]

    def expr_type_BinOp(self, node):
        """Inferisce il tipo risultante di un'operazione binaria con validazione dei tipi:
        - Operatori aritmetici (+, -, *, /): entrambi gli operandi devono essere numerici (int o real)
        - Operatori relazionali (>, <, ==, ecc.): gli operandi devono essere dello stesso tipo
          o compatibili (int/real), e restituiscono sempre 'bool'"""
        l_type = self.get_expr_type(node.left)
        r_type = self.get_expr_type(node.right)

        # Insieme dei tipi numerici ammessi per le operazioni aritmetiche
        numeric_types = {'int', 'real'}

        if node.op in ['>', '<', '>=', '<=', '==', '!=']:
            # Operatori relazionali: gli operandi devono essere confrontabili
            # Ammettiamo confronti tra tipi uguali o tra int e real (promozione implicita)
            if l_type == r_type:
                pass  # Tipi uguali: sempre confrontabili (int==int, bool==bool, string==string)
            elif l_type in numeric_types and r_type in numeric_types:
                pass  # int vs real: confronto numerico valido
            else:
                raise Exception(
                    f"Errore di tipo: impossibile confrontare '{l_type}' con '{r_type}' usando '{node.op}'."
                )
            return 'bool'  # I confronti producono sempre un booleano

        # Operatori aritmetici (+, -, *, /): entrambi gli operandi devono essere numerici
        if l_type not in numeric_types:
            raise Exception(
                f"Errore di tipo: operatore '{node.op}' non applicabile al tipo '{l_type}'."
            )
        if r_type not in numeric_types:
            raise Exception(
                f"Errore di tipo: operatore '{node.op}' non applicabile al tipo '{r_type}'."
            )

        # Se almeno un operando è real, il risultato è real (promozione)
        if l_type == 'real' or r_type == 'real':
            return 'real'
        return 'int'
