"""
Modulo: typechecker.py
Seconda fase dell'analisi semantica: verifica la compatibilità dei tipi in tutto l'AST.
Controlla assegnazioni, chiamate a funzione, return, condizioni booleane e cast impliciti.
"""
from .ast_nodes import *
from .errors import RoboTypeError


class TypeChecker:
    """
    Il TypeChecker è un Visitor (visitatore) che percorre ricorsivamente l'AST
    (Abstract Syntax Tree) per verificare la compatibilità dei tipi di dati.
    Riceve i dati già raccolti dallo ScopeAnalyzer, ovvero la tabella dei simboli
    globale e il dizionario delle funzioni/task registrate.
    """

    def __init__(self, scope_analyzer):
        # Eredita la tabella dei simboli (symbol_table) dallo ScopeAnalyzer.
        # È un dizionario che mappa il nome di una variabile al suo tipo (es: {"x": "int"}).
        self.symbol_table = scope_analyzer.symbol_table
        
        # Eredita il dizionario delle funzioni/task registrate dallo ScopeAnalyzer.
        # Mappa il nome della funzione alla sua definizione/nodo AST (es: {"calcola": TaskDecl}).
        self.functions = scope_analyzer.functions
        
        # Memorizza il tipo di ritorno del task correntemente visitato.
        # È None quando ci troviamo a livello globale (fuori da qualsiasi task).
        self.current_func_ret_type = None

    def check(self, ast):
        """
        Punto di ingresso principale dell'analisi dei tipi.
        Scorre la lista di istruzioni (statement) al livello radice dell'AST
        e invoca il metodo accept su ciascuna, passandovi l'istanza corrente del TypeChecker.
        """
        for stmt in ast:
            # Ogni nodo dello statement accetta il visitatore e richiama visit_NomeClasse
            stmt.accept(self)

    def visit(self, node):
        """
        Meccanismo di dispatch dinamico (Pattern Visitor).
        Determina a tempo di esecuzione il nome della classe del nodo visitato (es: VarDecl)
        e cerca un metodo all'interno di questa classe chiamato 'visit_VarDecl'.
        Se lo trova, lo invoca passando il nodo come argomento.
        Se non lo trova, solleva un errore di tipo semantico.
        """
        # Genera il nome del metodo dinamicamente a partire dal tipo del nodo (es: "visit_VarDecl")
        method_name = f"visit_{type(node).__name__}"
        
        # Recupera il metodo corrispondente dall'oggetto TypeChecker (self)
        method = getattr(self, method_name, None)
        
        # Se il metodo non esiste nell'oggetto TypeChecker, solleva un'eccezione di tipo
        if method is None:
            raise RoboTypeError(
                f"Nodo non gestito in type checking: {type(node).__name__}",
                getattr(node, 'line', None),
                getattr(node, 'column', None)
            )
        
        # Esegue il metodo trovato e restituisce il suo risultato
        return method(node)

    # --- VISIT DEI NODI PRINCIPALI ---

    def visit_TaskDecl(self, node):
        """
        Visita la dichiarazione di un task (funzione).
        Crea uno scope locale duplicando la symbol table corrente (per supportare variabili locali),
        imposta il tipo di ritorno corrente per controllare le istruzioni 'return',
        registra i parametri della funzione come variabili locali,
        visita tutte le istruzioni all'interno del corpo del task,
        e infine ripristina lo scope globale originario all'uscita dal task.
        """
        # Crea una copia superficiale dello scope corrente per isolare le variabili locali del task
        old_table = self.symbol_table.copy()
        
        # Salva il tipo di ritorno del task precedentemente in esame (se annidati o globale)
        old_ret_type = self.current_func_ret_type
        
        # Imposta il tipo di ritorno atteso per il task corrente (es: 'int', 'real', 'void')
        self.current_func_ret_type = node.ret_type

        # Registra ciascun parametro del task nello scope locale (symbol_table)
        for p in node.params:
            # Associa il nome del parametro al suo tipo dichiarato (es: p.name='x', p.type='int')
            self.symbol_table[p.name] = p.type

        # Esegue il controllo dei tipi per ogni istruzione (statement) nel corpo del task
        for s in node.body:
            # Chiama accept su ogni statement per inviare il visitatore
            s.accept(self)

        # Ripristina la tabella dei simboli precedente per eliminare le variabili locali del task
        self.symbol_table = old_table
        
        # Ripristina il tipo di ritorno del contesto precedente
        self.current_func_ret_type = old_ret_type

    def visit_VarDecl(self, node):
        """
        Visita la dichiarazione di una nuova variabile.
        Verifica che il tipo dell'espressione di inizializzazione sia compatibile
        con il tipo esplicitamente dichiarato per la variabile.
        Se compatibile, aggiunge la variabile alla symbol table corrente.
        """
        # Calcola ricorsivamente il tipo dell'espressione assegnata come valore iniziale (es: node.value)
        expr_type = self.get_expr_type(node.value)
        
        # Controlla se il tipo dichiarato (node.type) è compatibile con quello dell'espressione (expr_type)
        if not self._is_compatible(node.type, expr_type):
            # Se incompatibili, solleva un errore di tipo fornendo riga e colonna dell'errore nell'editor
            raise RoboTypeError(
                f"Errore di tipo: '{node.name}' attende '{node.type}', ottenuto '{expr_type}'.",
                node.line, node.column
            )
        
        # Se il tipo è valido, inserisce la variabile con il suo tipo nella symbol table per gli usi futuri
        self.symbol_table[node.name] = node.type

    def visit_SetStmt(self, node):
        """
        Visita un'istruzione di assegnazione 'set' (es: set x = espressione).
        Verifica che la variabile sia già dichiarata e che il tipo del nuovo valore
        sia compatibile con il tipo originario della variabile recuperato dalla symbol table.
        """
        # Recupera il tipo originario con cui la variabile è stata registrata nello scope corrente
        var_type = self.symbol_table[node.name]
        
        # Calcola il tipo dell'espressione che si desidera assegnare alla variabile
        expr_type = self.get_expr_type(node.value)
        
        # Verifica se il tipo della variabile è compatibile con il tipo dell'espressione
        if not self._is_compatible(var_type, expr_type):
            # Solleva un errore di tipo se l'assegnazione viola le regole di tipo
            raise RoboTypeError(
                f"Errore di tipo in assegnazione: '{node.name}' attende '{var_type}', ottenuto '{expr_type}'.",
                node.line, node.column
            )

    def visit_CallStmt(self, node):
        """
        Visita una chiamata a funzione intesa come istruzione a sé stante (statement).
        Verifica la validità dei parametri e dei tipi ma ignora l'eventuale valore restituito.
        """
        # Chiama il metodo di supporto per convalidare nome, argomenti e tipi della chiamata
        self._check_function_call(node.name, node.args, node.line, node.column)

    def visit_ReturnStmt(self, node):
        """
        Visita un'istruzione di ritorno 'return'.
        Verifica che il valore restituito sia compatibile con il tipo di ritorno atteso
        dal task corrente in cui ci troviamo (current_func_ret_type).
        """
        # Caso 1: L'istruzione è un 'return' semplice senza valore (es: return;)
        if node.value is None:
            # Se non restituisce nulla, il task corrente deve avere come tipo di ritorno dichiarato 'void'
            if self.current_func_ret_type != "void":
                raise RoboTypeError(
                    f"La funzione attende un ritorno di tipo '{self.current_func_ret_type}'.",
                    node.line, node.column
                )
            return

        # Caso 2: C'è un'espressione nel return (es: return x + 1;)
        # Calcola il tipo dell'espressione restituita
        ret_type = self.get_expr_type(node.value)
        
        # Controlla se il tipo atteso del task è compatibile col tipo effettivo dell'espressione di ritorno
        if not self._is_compatible(self.current_func_ret_type, ret_type):
            raise RoboTypeError(
                f"Errore di tipo: return attende '{self.current_func_ret_type}', ottenuto '{ret_type}'.",
                node.line, node.column
            )

    def visit_LogStmt(self, node):
        """
        Visita un'istruzione di log 'log' (es: log(espressione)).
        Calcola il tipo dell'espressione loggata e lo salva direttamente nel nodo AST (node.expr_type).
        Questa annotazione serve al generatore di codice (Codegen) per sapere a compile-time
        se stampare una stringa (%s), un intero (%d), un reale (%f) o un booleano.
        """
        # Determina il tipo dell'espressione all'interno del log e lo memorizza sul nodo AST stesso
        node.expr_type = self.get_expr_type(node.expr)

    def _visit_conditional_loop(self, node):
        """
        Metodo helper condiviso per blocchi condizionali (when, while).
        Verifica che l'espressione di condizione produca un tipo booleano ('bool')
        e successivamente effettua il type checking di tutte le istruzioni all'interno del corpo.
        """
        # Determina il tipo dell'espressione di condizione (es: x > 5)
        cond_type = self.get_expr_type(node.condition)
        
        # La condizione per blocchi condizionali o cicli deve essere strettamente di tipo 'bool'
        if cond_type != 'bool':
            raise RoboTypeError(
                f"La condizione deve essere 'bool', ottenuto '{cond_type}'.",
                node.condition.line,
                node.condition.column
            )
        
        # Esegue il type check per ciascuna istruzione (statement) contenuta nel blocco
        for stmt in node.body:
            stmt.accept(self)

    def visit_WhenStmt(self, node):
        """
        Visita un'istruzione condizionale 'when' (simile a un if).
        Delega la verifica al metodo ausiliario _visit_conditional_loop.
        """
        self._visit_conditional_loop(node)

    def visit_WhileStmt(self, node):
        """
        Visita un ciclo iterativo 'while'.
        Delega la verifica al metodo ausiliario _visit_conditional_loop.
        """
        self._visit_conditional_loop(node)

    # --- METODI DI SUPPORTO ---

    def _is_compatible(self, target_type, source_type):
        """
        Verifica se un valore di tipo 'source_type' può essere assegnato a un contenitore
        (variabile, parametro o tipo di ritorno) di tipo 'target_type'.
        Gestisce anche la promozione implicita (widening): un 'int' può sempre essere promosso a 'real'.
        """
        # Se i tipi sono identici, sono sempre perfettamente compatibili (es: int -> int)
        if target_type == source_type:
            return True
        
        # Regola di cast implicito: consente di inserire un valore intero in una variabile float/real
        # (es: var r: real = 10; dove 10 è int ma viene promosso a 10.0 real)
        if target_type == 'real' and source_type == 'int':
            return True
        
        # In tutti gli altri casi, i tipi non sono compatibili (es: string -> int)
        return False

    def _check_function_call(self, func_name, args, line=None, column=None):
        """
        Verifica la validità di una chiamata a funzione (task).
        Controlla:
        1. Se la funzione chiamata esiste nel dizionario delle funzioni registrate.
        2. Se il numero di argomenti passati coincide con il numero di parametri definiti.
        3. Se il tipo di ciascun argomento passato è compatibile con il rispettivo parametro.
        Restituisce il tipo di ritorno della funzione convalidata.
        """
        # 1. Controlla se il nome della funzione è presente tra quelle registrate dal parser/scope analyzer
        if func_name not in self.functions:
            raise RoboTypeError(f"Funzione '{func_name}' non dichiarata.", line, column)
        
        # Recupera il nodo di dichiarazione del task associato (TaskDecl)
        func = self.functions[func_name]

        # 2. Verifica che il numero di argomenti forniti sia uguale al numero di parametri richiesti
        if len(args) != len(func.params):
            raise RoboTypeError(
                f"La funzione '{func_name}' aspetta {len(func.params)} argomenti, ottenuti {len(args)}.",
                line, column
            )
        
        # 3. Verifica, per ogni argomento, la compatibilità del tipo con il rispettivo parametro formale
        for i, arg in enumerate(args):
            # Calcola il tipo dell'argomento passato alla chiamata
            arg_type = self.get_expr_type(arg)
            
            # Recupera il tipo dichiarato del parametro corrispondente nella dichiarazione della funzione
            param_type = func.params[i].type
            
            # Controlla la compatibilità tra il tipo del parametro e il tipo dell'argomento fornito
            if not self._is_compatible(param_type, arg_type):
                raise RoboTypeError(
                    f"Errore di tipo nell'argomento {i+1} di '{func_name}': atteso '{param_type}', ottenuto '{arg_type}'.",
                    arg.line, arg.column
                )
        
        # Restituisce il tipo di ritorno originario del task (usato per inferire il tipo nelle espressioni)
        return func.ret_type

    # --- INFERENZA DEL TIPO DELLE ESPRESSIONI ---

    def get_expr_type(self, node):
        """
        Meccanismo di dispatch dinamico per ricavare il tipo di un'espressione (Pattern Visitor).
        Determina il tipo dell'espressione invocando il metodo 'expr_type_NomeClasse' opportuno.
        """
        # Genera il nome del metodo per determinare il tipo dell'espressione (es: "expr_type_Literal")
        method_name = f"expr_type_{type(node).__name__}"
        
        # Cerca il metodo nell'oggetto corrente
        method = getattr(self, method_name, None)
        
        # Se non esiste un gestore per questo tipo di espressione, solleva un errore semantico
        if method is None:
            raise RoboTypeError(
                f"Espressione non gestita: {type(node).__name__}",
                getattr(node, 'line', None),
                getattr(node, 'column', None)
            )
        
        # Esegue il metodo e restituisce il tipo inferito (stringa come 'int', 'real', 'bool', 'string')
        return method(node)

    def expr_type_Literal(self, node):
        """
        Determina il tipo di un valore letterale (es: 42, 3.14, "ciao", true).
        Restituisce semplicemente il tipo pre-compilato dal parser e salvato nel nodo (node.type).
        """
        return node.type

    def expr_type_CallExpr(self, node):
        """
        Determina il tipo di una chiamata a funzione usata all'interno di un'espressione (es: set x = calcola(5)).
        Verifica la validità della chiamata e restituisce il tipo di ritorno dichiarato per quel task.
        """
        return self._check_function_call(node.name, node.args, node.line, node.column)

    def expr_type_VarMatch(self, node):
        """
        Determina il tipo di un riferimento a variabile (es: l'uso di 'x' in un'espressione).
        Cerca e restituisce il tipo associato alla variabile all'interno della symbol table corrente.
        """
        return self.symbol_table[node.name]

    def expr_type_BinOp(self, node):
        """
        Determina il tipo risultante da un'operazione binaria (es: +, -, *, /, >, ==).
        Esegue il controllo di tipo sui sotto-nodi sinistro e destro:
        - Per operatori relazionali (confronti): verifica che siano confrontabili e restituisce 'bool'.
        - Per operatori aritmetici: verifica che siano entrambi numerici (int o real).
          Se almeno uno dei due è 'real', promuove il risultato a 'real'; altrimenti restituisce 'int'.
        """
        # Calcola ricorsivamente il tipo dell'operando sinistro
        l_type = self.get_expr_type(node.left)
        
        # Calcola ricorsivamente il tipo dell'operando destro
        r_type = self.get_expr_type(node.right)

        # Definisce i tipi considerati validi per le operazioni aritmetiche
        numeric_types = {'int', 'real'}

        # Caso 1: L'operatore è di tipo relazionale/confronto (>, <, >=, <=, ==, !=)
        if node.op in ['>', '<', '>=', '<=', '==', '!=']:
            # Se i tipi dei due operandi sono identici, il confronto è lecito (es: string == string, bool == bool)
            if l_type == r_type:
                pass
            # Se entrambi gli operandi sono numerici (anche diversi, es: int vs real), il confronto è valido
            elif l_type in numeric_types and r_type in numeric_types:
                pass
            # Altrimenti, solleva un errore di tipo perché i tipi non sono compatibili per il confronto
            else:
                raise RoboTypeError(
                    f"Impossibile confrontare '{l_type}' con '{r_type}' usando '{node.op}'.",
                    node.line, node.column
                )
            # Qualsiasi operazione di confronto valida restituisce sempre un booleano ('bool')
            return 'bool'

        # Caso 2: L'operatore è aritmetico (+, -, *, /)
        # L'operando sinistro deve essere obbligatoriamente numerico (int o real)
        if l_type not in numeric_types:
            raise RoboTypeError(
                f"Operatore '{node.op}' non applicabile al tipo '{l_type}'.",
                node.left.line, node.left.column
            )
        
        # L'operando destro deve essere obbligatoriamente numerico (int o real)
        if r_type not in numeric_types:
            raise RoboTypeError(
                f"Operatore '{node.op}' non applicabile al tipo '{r_type}'.",
                node.right.line, node.right.column
            )

        # Regola di promozione dei tipi numerici (coercion/widening):
        # Se uno dei due operandi è 'real', l'intero risultato dell'operazione viene promosso a 'real'
        if l_type == 'real' or r_type == 'real':
            return 'real'
        
        # Se entrambi gli operandi sono interi ('int'), il tipo risultante dell'operazione è 'int'
        return 'int'