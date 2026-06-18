"""
Modulo: grammar.py
Definisce la grammatica formale del linguaggio roboLang in notazione EBNF di Lark.
Lark usa questa stringa per generare automaticamente il parser LALR(1).
"""

grammar = """
# Regola radice: un programma è una sequenza di dichiarazioni di task e/o statement
start: (task_decl | stmt)*

# Dichiarazione di funzione (task): nome, parametri opzionali, tipo di ritorno opzionale, corpo
task_decl: "task" CNAME "(" param_list? ")" ("->" TYPE)? "{" stmt* "}"
param_list: param ("," param)*
param: CNAME ":" TYPE

# Il "?" dice a Lark di fare inlining: se c'è un solo figlio, lo promuove al posto del nodo stmt
# (evita nodi intermedi inutili nel Parse Tree)
?stmt: var_decl
     | set_stmt
     | when_stmt
     | while_stmt
     | call_stmt
     | return_stmt
     | log_stmt

# Statement del linguaggio roboLang
var_decl: "var" CNAME ":" TYPE "=" expr ";"       // Dichiarazione variabile con tipo e valore iniziale
set_stmt: "set" CNAME "=" expr ";"                 // Assegnazione a variabile già dichiarata
when_stmt: "when" "(" expr ")" "{" stmt* "}"       // Blocco condizionale reattivo (tradotto in if in C)
while_stmt: "while" "(" expr ")" "{" stmt* "}"     // Ciclo iterativo con condizione booleana
call_stmt: CNAME "(" expr_list? ")" ";"            // Chiamata a funzione come statement (ignora il ritorno)
return_stmt: "return" expr? ";"                    // Ritorno da un task (con o senza valore)
log_stmt: "log" "(" expr ")" ";"                   // Stampa di debug a console

# Tipi di dato supportati dal linguaggio
TYPE: "int" | "real" | "bool" | "string"

# --- ESPRESSIONI ---
# La struttura a cascata definisce le PRECEDENZE degli operatori:
# comp_expr (priorità più bassa) -> arith_expr -> term -> factor (priorità più alta)
# Questo garantisce che * e / vengano valutati prima di + e -

?expr: comp_expr                                   // Un'espressione è una comparazione (o meno)
expr_list: expr ("," expr)*                        // Lista di espressioni separate da virgola

?comp_expr: arith_expr (OP_REL arith_expr)*        // Confronto relazionale (>, <, ==, ecc.)
?arith_expr: term (OP_ADD term)*                   // Addizione e sottrazione (priorità bassa)
?term: factor (OP_MUL factor)*                     // Moltiplicazione e divisione (priorità alta)

# Factor: l'unità atomica di un'espressione
# Le frecce "->" mappano i token a nomi di regola usati dal Transformer
?factor: NUMBER          -> number                 // Numero intero o decimale
       | call_expr                                 // Chiamata a funzione come espressione (usa il ritorno)
       | CNAME           -> var                    // Riferimento a variabile
       | ESCAPED_STRING  -> string                 // Stringa letterale tra virgolette
       | "true"          -> true_val               // Letterale booleano true
       | "false"         -> false_val              // Letterale booleano false
       | "(" expr ")"                              // Espressione tra parentesi (forza la priorità)

call_expr: CNAME "(" expr_list? ")"                // Chiamata a funzione dentro un'espressione

# Operatori raggruppati per livello di precedenza
OP_ADD: "+" | "-"                                  // Operatori additivi
OP_MUL: "*" | "/"                                  // Operatori moltiplicativi
OP_REL: ">" | "<" | ">=" | "<=" | "==" | "!="     // Operatori relazionali (producono bool)

# Importazioni dai token comuni di Lark
%import common.CNAME                               // Nomi di identificatori (lettere, cifre, underscore)
%import common.SIGNED_NUMBER -> NUMBER              // Numeri con segno (interi e decimali)
%import common.ESCAPED_STRING                       // Stringhe con escape tra virgolette doppie
%import common.WS                                   // Whitespace (spazi, tab, newline)
%ignore WS                                          // Ignora gli spazi bianchi nel parsing
"""
