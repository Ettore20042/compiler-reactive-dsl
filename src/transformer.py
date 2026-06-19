"""
Modulo: transformer.py
Converte il Parse Tree grezzo generato da Lark in un AST (Abstract Syntax Tree)
composto dalle classi tipizzate definite in ast_nodes.py.
Ogni metodo ha lo stesso nome della regola grammaticale corrispondente in grammar.py.
"""
from lark import Transformer, v_args
from .ast_nodes import *


@v_args(meta=True)
class ASTTransformer(Transformer):
    """Trasforma il Parse Tree di Lark nel nostro AST personalizzato.
    Lark chiama automaticamente il metodo con lo stesso nome della regola grammaticale
    (es. la regola 'var_decl' invoca il metodo var_decl())."""

    def start(self, meta, stmts):
        """Regola radice: restituisce la lista di tutti gli statement e task del programma."""
        return stmts

    # --- FUNZIONI (TASK) ---

    def task_decl(self, meta, args):
        """Costruisce un nodo TaskDecl dal parse di una dichiarazione di funzione.
        args contiene: [nome, (param_list?), (tipo_ritorno?), stmt1, stmt2, ...]
        Dobbiamo distinguere dinamicamente quali elementi sono presenti."""
        name = str(args[0])             # Primo elemento: nome del task
        idx = 1
        params = []
        # Se il secondo elemento è una lista, è la lista dei parametri
        if isinstance(args[idx], list):
            params = args[idx]
            idx += 1

        # Se l'elemento successivo è un tipo valido, è il tipo di ritorno (->)
        ret_type = "void"
        if idx < len(args) and isinstance(args[idx], str) and args[idx] in ["int", "real", "bool", "string"]:
            ret_type = str(args[idx])
            idx += 1

        # Tutto il resto sono gli statement del corpo della funzione
        body = args[idx:]
        return TaskDecl(name, params, ret_type, body).set_pos(meta.line, meta.column)

    def param_list(self, meta, args):
        """Restituisce la lista dei parametri così com'è."""
        return args

    def param(self, meta, args):
        """Crea un nodo Param da un parametro formale. Es: base: int -> Param("base", "int")"""
        return Param(str(args[0]), str(args[1])).set_pos(meta.line, meta.column)

    # --- CHIAMATE ---

    def expr_list(self, meta, args):
        """Restituisce la lista delle espressioni (argomenti di una chiamata)."""
        return args

    def call_expr(self, meta, args):
        """Chiamata a funzione usata come ESPRESSIONE (il valore di ritorno viene usato).
        Es: calculateSpeed(10, 20) dentro set x = calculateSpeed(10, 20);"""
        name = str(args[0])
        call_args = args[1] if len(args) > 1 and isinstance(args[1], list) else []
        return CallExpr(name, call_args).set_pos(meta.line, meta.column)

    def call_stmt(self, meta, args):
        """Chiamata a funzione usata come STATEMENT (il ritorno è ignorato).
        Es: printResult(42);"""
        name = str(args[0])
        call_args = args[1] if len(args) > 1 and isinstance(args[1], list) else []  #Nella lista dei figli c'è effettivamente un oggetto di tipo lista ?Se la risposta è si li assegna a call args,altrimenti (es.read_int()) assegna a call args una lista vuota
        return CallStmt(name, call_args).set_pos(meta.line, meta.column)

    # --- STATEMENT ---

    def return_stmt(self, meta, args):
        """Crea un nodo ReturnStmt. Se il return è vuoto (void), value sarà None."""
        value = args[0] if len(args) > 0 else None
        return ReturnStmt(value).set_pos(meta.line, meta.column)

    def log_stmt(self, meta, args):
        """Crea un nodo LogStmt con l'espressione da stampare."""
        return LogStmt(args[0]).set_pos(meta.line, meta.column)

    def var_decl(self, meta, args):
        """Crea un nodo VarDecl. args = [nome, tipo, espressione_iniziale]"""
        return VarDecl(str(args[0]), str(args[1]), args[2]).set_pos(meta.line, meta.column)

    def set_stmt(self, meta, args):
        """Crea un nodo SetStmt. args = [nome_variabile, espressione_valore]"""
        return SetStmt(str(args[0]), args[1]).set_pos(meta.line, meta.column)

    def when_stmt(self, meta, args):
        """Crea un nodo WhenStmt. args[0] è la condizione, args[1:] sono gli statement del corpo."""
        return WhenStmt(args[0], args[1:]).set_pos(meta.line, meta.column)

    def while_stmt(self, meta, args):
        """Crea un nodo WhileStmt. args[0] è la condizione, args[1:] sono gli statement del corpo."""
        return WhileStmt(args[0], args[1:]).set_pos(meta.line, meta.column)

    # --- ESPRESSIONI ---

    def _fold_binops(self, args, meta):
        """Metodo helper per costruire un albero BinOp sinistro-associativo.
        Lark restituisce una lista piatta: [operando, op, operando, op, operando, ...]
        Es: per "1 + 2 + 3" riceve [Literal(1), '+', Literal(2), '+', Literal(3)]
        e produce: BinOp(BinOp(Literal(1), '+', Literal(2)), '+', Literal(3))
        Senza questo metodo, il transformer considererebbe solo i primi 3 elementi."""
        left = args[0]                  # Parte dal primo operando
        i = 1
        while i < len(args):            # Consuma coppie (operatore, operando)
            op = str(args[i])           # Operatore (es. "+")
            right = args[i+1]           # Operando destro
            left = BinOp(left, op, right).set_pos(meta.line, meta.column)  # Crea un nuovo BinOp e lo usa come lato sinistro
            i += 2
        return left

    def comp_expr(self, meta, args):
        """Espressione di confronto (>, <, ==, ecc.). Usa il folding(ripiegamento) per gestire catene."""
        return self._fold_binops(args, meta)

    def arith_expr(self, meta, args):
        """Espressione additiva (+, -). Usa il folding per gestire catene come 1+2+3."""
        return self._fold_binops(args, meta)

    def term(self, meta, args):
        """Espressione moltiplicativa (*, /). Usa il folding per gestire catene come 2*3*4."""
        return self._fold_binops(args, meta)

    # --- LETTERALI E VARIABILI ---

    def number(self, meta, args):
        """Converte un token numerico in un Literal, distinguendo int da real.
        Controlla la presenza del punto decimale '.' O della notazione esponenziale 'e'/'E'.
        Es: 42 → int, 3.14 → real, 5e3 → real, 1.2e-4 → real"""
        val = str(args[0])
        is_real = '.' in val or 'e' in val or 'E' in val
        return Literal('real' if is_real else 'int', val).set_pos(meta.line, meta.column)

    def string(self, meta, args):
        """Converte un token stringa in un Literal di tipo string."""
        return Literal('string', str(args[0])).set_pos(meta.line, meta.column)

    def true_val(self, meta, args):
        """Converte il token 'true' in un Literal booleano."""
        return Literal('bool', 'true').set_pos(meta.line, meta.column)

    def false_val(self, meta, args):
        """Converte il token 'false' in un Literal booleano."""
        return Literal('bool', 'false').set_pos(meta.line, meta.column)

    def var(self, meta, args):
        """Converte un riferimento a variabile in un nodo VarMatch."""
        return VarMatch(str(args[0])).set_pos(meta.line, meta.column)
