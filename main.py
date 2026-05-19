"""
Modulo: main.py
Entry point principale del compilatore.
Gestisce file IO e l orchestrazione delle varie fasi architetturali.
"""
import sys
from lark import Lark
from grammar import grammar
from transformer import ASTTransformer
from semantic import SemanticAnalyzer
from codegen import CGenerator

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'example.txt'

    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Errore: impossibile trovare il file '{input_file}'")
        sys.exit(1)

    print(f"--- Sorgente DSL ({input_file}) ---")
    print(source_code)

    parser = Lark(grammar, parser='lalr')
    tree = parser.parse(source_code)
    ast = ASTTransformer().transform(tree)

    print("\\n--- Analisi Semantica ---")
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    print("Analisi semantica completata con successo.")

    print("\\n--- Generazione Codice C ---")
    generator = CGenerator()
    c_code = generator.generate(ast)
    print(c_code)

    # Salva il codice C in un file
    output_file = input_file.replace('.txt', '.c')
    if output_file == input_file:
        output_file = "output.c"

    with open(output_file, "w") as f:
        f.write(c_code)
    print(f"\\nCodice salvato in '{output_file}'.")
