"""
Modulo: ast_nodes.py
Definisce le classi che rappresentano i nodi dell'Abstract Syntax Tree (AST).
Ogni nodo corrisponde a un costrutto del linguaggio roboLang.
Tutte le classi ereditano da ASTNode e supportano il Visitor Pattern tramite accept().
"""


class ASTNode:
    """Classe base di tutti i nodi dell'AST.
    Il metodo accept() implementa il Visitor Pattern: delega la logica
    al visitor (scope, typechecker, codegen) che sa come trattare ogni tipo di nodo."""
    line = None
    column = None

    def accept(self, visitor):
        return visitor.visit(self)
        
    def set_pos(self, line, column):
        self.line = line
        self.column = column
        return self


# --- NODI PER LE FUNZIONI ---

class TaskDecl(ASTNode):
    """Dichiarazione di una funzione (task) del linguaggio roboLang.
    Es: task sum(a: int, b: int) -> int { return a + b; }"""
    def __init__(self, name, params, ret_type, body):   # Salvato nell oggetto self
        self.name = name          # Nome della funzione (es. "sum")
        self.params = params      # Lista di oggetti Param (parametri formali)
        self.ret_type = ret_type  # Tipo di ritorno ("int", "real", "void", ecc.)
        self.body = body          # Lista di statement nel corpo della funzione


class Param(ASTNode):
    """Parametro formale di un task. Es: a: int"""
    def __init__(self, name, param_type):
        self.name = name          # Nome del parametro (es. "a")
        self.type = param_type    # Tipo del parametro (es. "int")


# --- NODI PER LE CHIAMATE ---

class CallExpr(ASTNode):
    """Chiamata a funzione DENTRO un'espressione (il valore di ritorno viene usato).
    Es: set x = calculateSpeed(10, 20);  <-- calculateSpeed(...) è un CallExpr"""
    def __init__(self, name, args):
        self.name = name          # Nome della funzione chiamata
        self.args = args          # Lista di espressioni passate come argomenti


class CallStmt(ASTNode):
    """Chiamata a funzione come STATEMENT autonomo (il valore di ritorno viene ignorato).
    Es: printResult(42);"""
    def __init__(self, name, args):
        self.name = name          # Nome della funzione chiamata
        self.args = args          # Lista di espressioni passate come argomenti


# --- NODI PER GLI STATEMENT ---

class ReturnStmt(ASTNode):
    """Statement di ritorno da un task. value è None se è un return vuoto (task void)."""
    def __init__(self, value):
        self.value = value        # Espressione da restituire (o None per void)


class LogStmt(ASTNode):
    """Stampa di debug a console. Es: log(speed);
    Il campo expr_type viene popolato dal TypeChecker e usato dal Codegen
    per scegliere il formato printf corretto (%d, %f, %s)."""
    def __init__(self, expr):
        self.expr = expr          # Espressione da stampare


class VarDecl(ASTNode):
    """Dichiarazione di variabile con tipo e valore iniziale.
    Es: var speed: int = 0;"""
    def __init__(self, name, var_type, value):
        self.name = name          # Nome della variabile (es. "speed")
        self.type = var_type      # Tipo dichiarato (es. "int")
        self.value = value        # Espressione di inizializzazione


class SetStmt(ASTNode):
    """Assegnazione a una variabile già dichiarata. Es: set speed = 100;"""
    def __init__(self, name, value):
        self.name = name          # Nome della variabile da modificare
        self.value = value        # Nuova espressione da assegnare


# --- NODI PER I COSTRUTTI DI CONTROLLO ---

class WhenStmt(ASTNode):
    """Blocco condizionale reattivo. Es: when (speed < max) { ... }
    Viene tradotto in 'if' nel codice C generato."""
    def __init__(self, condition, body):
        self.condition = condition  # Espressione booleana della condizione
        self.body = body            # Lista di statement nel corpo del blocco


class WhileStmt(ASTNode):
    """Ciclo iterativo. Es: while (running == true) { ... }"""
    def __init__(self, condition, body):
        self.condition = condition  # Espressione booleana della condizione
        self.body = body            # Lista di statement nel corpo del ciclo


# --- NODI PER LE ESPRESSIONI ---

class BinOp(ASTNode):
    """Operazione binaria tra due espressioni. Es: speed + 10, x == 5
    Strutturata ad albero: BinOp(BinOp(1, '+', 2), '+', 3) per 1+2+3"""
    def __init__(self, left, op, right):
        self.left = left          # Operando sinistro (un altro nodo AST)
        self.op = op              # Operatore come stringa ("+", "-", "*", "/", "==", ecc.)
        self.right = right        # Operando destro (un altro nodo AST)


class Literal(ASTNode):
    """Valore letterale costante. Es: 42, 3.14, "ciao", true"""
    def __init__(self, type, value):
        self.type = type          # Tipo del letterale ("int", "real", "string", "bool")
        self.value = value        # Valore come stringa (es. "42", "3.14", '"ciao"', "true")


class VarMatch(ASTNode):
    """Riferimento a una variabile usata in un'espressione. Es: speed in 'speed + 10'"""
    def __init__(self, name):
        self.name = name          # Nome della variabile referenziata
