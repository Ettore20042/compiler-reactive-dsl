"""
Modulo: main.py
Entry point principale del compilatore del linguaggio roboLang.
Orchestrare le 4 fasi della compilazione: Parsing → AST → Semantica → Codegen.
"""

import sys                              # Per leggere gli argomenti da riga di comando e uscire in caso di errore
from lark import Lark                   # Libreria esterna che genera il parser dalla grammatica EBNF
from src.grammar import grammar         # Stringa contenente la grammatica formale di roboLang
from src.transformer import ASTTransformer  # Trasforma il Parse Tree di Lark nel nostro AST personalizzato
from src.semantic import SemanticAnalyzer   # Coordina l'analisi semantica (scope + tipi)
from src.codegen import CGenerator          # Visita l'AST e produce il codice sorgente C
from src.errors import CompilerError        # Errori custom per il compilatore

if __name__ == '__main__':

    # --- FASE 0: Lettura del file sorgente ---
    # Se l'utente passa un file come argomento (es. python main.py miofile.robo), usa quello.
    # Altrimenti compila il file di esempio predefinito.
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'examples/example.robo'

    # Ap
    # re il file sorgente e ne legge l'intero contenuto come stringa
    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Errore: impossibile trovare il file '{input_file}'")
        sys.exit(1)  # Termina il programma con codice di errore

    print(f"--- Sorgente roboLang ({input_file}) ---")
    print(source_code)

    # --- FASE 1: Parsing (Analisi Sintattica) ---
    # Crea un parser LALR(1) a partire dalla grammatica EBNF definita in grammar.py
    # propagate_positions=True permette al transformer di leggere le linee e le colonne
    parser = Lark(grammar, parser='lalr', propagate_positions=True)
    
    try:
        # Analizza il codice sorgente e produce un Parse Tree (albero sintattico grezzo di Lark)
        tree = parser.parse(source_code)
        # print("\n--- Parse Tree ---")
        # print(tree.pretty())
        # Converte il Parse Tree in un AST (Abstract Syntax Tree) composto dai nostri nodi tipizzati
        ast = ASTTransformer().transform(tree)

        # --- FASE 2: Analisi Semantica ---
        # Esegue in sequenza: 1) Scope Analysis (dichiarazioni e visibilità)
        #                      2) Type Checking (compatibilità dei tipi)
        # Se trova errori (variabile non dichiarata, tipo incompatibile, ecc.) lancia un'eccezione
        print("\n--- Analisi Semantica ---")
        analyzer = SemanticAnalyzer()      #Creo un oggetto
        analyzer.analyze(ast)               #Chiamo il metodo dell'oggetto
        print("Analisi semantica completata con successo.")
        
    except CompilerError as e:
        print(f"\n[ERRORE DI COMPILAZIONE] {e}")
        sys.exit(1)

    # --- FASE 3: Generazione del Codice C ---
    # Il CGenerator visita ogni nodo dell'AST e lo traduce nella corrispondente istruzione C
    print("\n--- Generazione Codice C ---")
    generator = CGenerator()
    c_code = generator.generate(ast)  # Restituisce l'intero file C come stringa
    print(c_code)

    # --- FASE 4: Salvataggio su file ---
    # Sostituisce l'estensione del file di input (.robo o .txt) con .c per il file di output
    if input_file.endswith('.robo'):
        output_file = input_file[:-5] + '.c'   # Rimuove ".robo" (5 caratteri) e aggiunge ".c"
    elif input_file.endswith('.txt'):
        output_file = input_file[:-4] + '.c'    # Rimuove ".txt" (4 caratteri) e aggiunge ".c"
    else:
        output_file = "output.c"                # Fallback generico

    # Scrive il codice C generato nel file di output
    with open(output_file, "w") as f:
        f.write(c_code)
    print(f"\nCodice salvato in '{output_file}'.")
