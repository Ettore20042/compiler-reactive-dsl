"""
Modulo: codegen.py
Fase finale del compilatore: visita l'AST validato semanticamente e genera
il codice sorgente C corrispondente, pronto per essere compilato con gcc.
"""
from .ast_nodes import *


class CGenerator:
    """Visitor che traduce ogni nodo dell'AST nella corrispondente sintassi C."""

    def __init__(self):
        self.code = []              # Lista di stringhe: ogni elemento è una riga del file C, buffer generale
        self.indent_level = 1       # Livello di indentazione corrente (1 = dentro main)

    def indent(self):
        """Restituisce la stringa di indentazione corrente (4 spazi per livello)."""
        return "    " * self.indent_level

    def generate(self, ast):
        """Punto di ingresso: genera l'intero file C a partire dall'AST.
        Restituisce il codice C completo come stringa."""

        # Intestazione: include le librerie standard C necessarie
        self.code.append("#include <stdio.h>")       # Per printf e scanf
        self.code.append("#include <stdbool.h>\n")   # Per il tipo bool (true/false)

        # Implementazione C delle funzioni built-in di input di roboLang
        # read_int(): legge un intero da terminale usando scanf con formato %d
        self.code.append("int read_int() {")
        self.code.append("    int val;")
        self.code.append("    if (scanf(\"%d\", &val) != 1) return 0;")
        self.code.append("    return val;")
        self.code.append("}\n")

        # read_real(): legge un double da terminale usando scanf con formato %lf
        self.code.append("double read_real() {")
        self.code.append("    double val;")
        self.code.append("    if (scanf(\"%lf\", &val) != 1) return 0.0;")
        self.code.append("    return val;")
        self.code.append("}\n")

        # Raccoglie tutti i task dichiarati nel programma
        tasks = [n for n in ast if isinstance(n, TaskDecl)]

        # Emette le forward declaration (prototipi) per TUTTI i task.
        # Questo risolve il problema di un task che chiama un altro task definito più avanti
        # nel sorgente: senza prototipi, il compilatore C segnalerebbe "implicit declaration".
        if tasks:
            self.code.append("// Forward declarations")
            for task in tasks:
                c_ret_type = self.map_type(task.ret_type)
                params_str = ", ".join([f"{self.map_type(p.type)} {p.name}" for p in task.params])
                if not params_str:
                    params_str = "void"
                self.code.append(f"{c_ret_type} {task.name}({params_str});")
            self.code.append("")    # Riga vuota dopo i prototipi

        # Genera le implementazioni complete dei task
        for task in tasks:
            task.accept(self)       # Invoca visit_TaskDecl per ogni task------ Oggetto della classe TaskDecl, self è il CGenerator, vede accept e salta dentro task
            self.code.append("")    # Riga vuota tra le funzioni per leggibilità

        # Genera la funzione main() contenente gli statement globali
        self.code.append("int main() {")
        for stmt in ast:
            if not isinstance(stmt, TaskDecl):  # Salta i task (già generati sopra)
                stmt.accept(self)
        self.code.append("    return 0;")
        self.code.append("}\n")

        # Unisce tutte le righe in una singola stringa separata da newline
        return "\n".join(self.code)

    def visit(self, node):
        """Dispatch dinamico: chiama il metodo visit_NomeClasse appropriato."""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: nodo non gestito in codegen: {type(node).__name__}")
        return method(node)

    # --- GENERAZIONE DEI NODI PRINCIPALI ---

    def visit_TaskDecl(self, node):
        """Genera la definizione di una funzione C.
        Es: task sum(a: real, b: real) -> real  →  double sum(double a, double b)"""
        c_ret_type = self.map_type(node.ret_type)   # Converte il tipo roboLang in tipo C
        # Costruisce la lista dei parametri con i tipi C (es. "double a, double b")
        params_str = ", ".join([f"{self.map_type(p.type)} {p.name}" for p in node.params])    #Per ogni parametro converte il tipo da RoboLang in C , poi prende il nome e lo aggiunge alla lista, poi li mette insieme
        if not params_str:
            params_str = "void"     # In C le funzioni senza parametri usano (void)
        self.code.append(f"{c_ret_type} {node.name}({params_str}) {{")
        self.indent_level += 1      # Aumenta l'indentazione per il corpo
        for s in node.body:
            s.accept(self)          # Genera ogni statement del corpo
        self.indent_level -= 1      # Ripristina l'indentazione
        self.code.append("}")

    def visit_CallStmt(self, node):
        """Genera una chiamata a funzione C come statement.
        Es: printResult(42);"""
        args_str = ", ".join([self.expr_to_c(arg) for arg in node.args])    #per ogni argomento che gli passiamo alla funzione , viene chiamato lo smistatore di espressioni che traduce in C,prende i vari pezzi e li mette insieme
        self.code.append(f"{self.indent()}{node.name}({args_str});")   #inserisce spazi vuoti iniziali,nome funzione e argomenti interni

    def visit_ReturnStmt(self, node):
        """Genera un return C con o senza valore."""
        if node.value:
            self.code.append(f"{self.indent()}return {self.expr_to_c(node.value)};")
        else:
            self.code.append(f"{self.indent()}return;")

    def visit_LogStmt(self, node):
        """Genera una chiamata printf con il formato corretto in base al tipo dell'espressione.
        Il tipo (node.expr_type) è stato calcolato e salvato dal TypeChecker."""
        val = self.expr_to_c(node.expr)
        # Sceglie il formato printf in base al tipo dell'espressione
        if node.expr_type == 'int' or node.expr_type == 'bool':
            fmt = "%d"      # Interi e booleani stampati come numeri
        elif node.expr_type == 'real':
            fmt = "%f"      # Double stampati come floating point
        elif node.expr_type == 'string':
            fmt = "%s"      # Stringhe stampate come testo
        else:
            fmt = "%d"      # Fallback
        self.code.append(f"{self.indent()}printf(\"{fmt}\\n\", {val});")

    def visit_VarDecl(self, node):
        """Genera una dichiarazione di variabile C con inizializzazione.
        Es: var speed: int = 0;  →  int speed = 0;"""
        c_type = self.map_type(node.type)         #prende il tipo di variabile in roboLang e lo converte in tipo C utilizzando la map_type
        val = self.expr_to_c(node.value)          #prende la parte destra della variabile e la traduce in C usando lo smistatore delle espressioni
        if c_type == "char*":
            self.code.append(f"{self.indent()}char* {node.name} = {val};")        #separa il trattamento dei tipi primitivi con quelli puntatore
        else:
            self.code.append(f"{self.indent()}{c_type} {node.name} = {val};")

    def visit_SetStmt(self, node):
        """Genera un'assegnazione C. Es: set speed = 100;  →  speed = 100;"""
        val = self.expr_to_c(node.value)
        self.code.append(f"{self.indent()}{node.name} = {val};")

    def _visit_conditional_loop(self, keyword, node):
        """Metodo condiviso per when (→ if) e while (→ while):
        genera il blocco condizionale con parentesi graffe e indentazione."""
        cond = self.expr_to_c(node.condition)
        self.code.append(f"{self.indent()}{keyword} ({cond}) {{")
        self.indent_level += 1      # Indenta il corpo
        for s in node.body:
            s.accept(self)
        self.indent_level -= 1
        self.code.append(f"{self.indent()}}}")

    def visit_WhenStmt(self, node):
        """Traduce il costrutto reattivo 'when' di roboLang nell'istruzione 'if' di C."""
        self._visit_conditional_loop("if", node)

    def visit_WhileStmt(self, node):
        """Traduce il ciclo 'while' di roboLang nel ciclo 'while' di C."""
        self._visit_conditional_loop("while", node)

    # --- MAPPING DEI TIPI ---

    def map_type(self, t):
        """Converte un tipo roboLang nel tipo C corrispondente.
        Nota: 'real' viene mappato a 'double' (non float) per maggiore precisione."""
        if t == "int": return "int"
        if t == "real": return "double"     # real → double per precisione a 64 bit
        if t == "bool": return "bool"       # Richiede #include <stdbool.h>
        if t == "string": return "char*"    # Stringhe come puntatori a carattere
        if t == "void": return "void"
        return "void"                       # Fallback per tipi sconosciuti

    # --- TRADUZIONE DELLE ESPRESSIONI IN STRINGA C ---

    def expr_to_c(self, node):
        """Dispatch dinamico per tradurre un nodo espressione nella sua rappresentazione C."""
        method_name = f"expr_to_c_{type(node).__name__}"    #Guarda il nome della classe, se gli passo un nodo di tipo BinOP la riga genere expr_to_c_BinOP, poi il gettattr cerca all'interno della classe se esiste un metodo con quel nome esatto
        method = getattr(self, method_name, None)
        if method is None:
            raise Exception(f"Errore: espressione non gestita in codegen: {type(node).__name__}")
        return method(node)

    def expr_to_c_Literal(self, node):
        """Un letterale viene emesso così com'è (es. 42, 3.14, "ciao", true)."""
        return node.value

    def expr_to_c_CallExpr(self, node):
        """Genera una chiamata a funzione C come espressione.
        Es: calculateSpeed(10, 20)"""
        args_str = ", ".join([self.expr_to_c(arg) for arg in node.args])
        return f"{node.name}({args_str})"

    def expr_to_c_VarMatch(self, node):
        """Un riferimento a variabile viene emesso come il suo nome (identico in C)."""
        return node.name

    def expr_to_c_BinOp(self, node):
        """Genera un'operazione binaria C con parentesi per preservare la precedenza.
        Es: BinOp(speed, '+', 10)  →  (speed + 10)"""
        return f"({self.expr_to_c(node.left)} {node.op} {self.expr_to_c(node.right)})"
