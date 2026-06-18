"""
Modulo: main.py
Entry point principale del compilatore del linguaggio roboLang.
Gestisce file IO e l'orchestrazione delle varie fasi architetturali.
"""
import sys
from lark import Lark
from src.grammar import grammar
from src.transformer import ASTTransformer
from src.semantic import SemanticAnalyzer
from src.codegen import CGenerator

if __name__ == '__main__':
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = 'examples/example.robo'

    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Errore: impossibile trovare il file '{input_file}'")
        sys.exit(1)

    print(f"--- Sorgente roboLang ({input_file}) ---")
    print(source_code)

    parser = Lark(grammar, parser='lalr')
    tree = parser.parse(source_code)
    ast = ASTTransformer().transform(tree)

    print("\n--- Analisi Semantica ---")
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    print("Analisi semantica completata con successo.")

    print("\n--- Generazione Codice C ---")
    generator = CGenerator()
    c_code = generator.generate(ast)
    print(c_code)

    # Determina il nome del file di output (.c)
    if input_file.endswith('.robo'):
        output_file = input_file[:-5] + '.c'
    elif input_file.endswith('.txt'):
        output_file = input_file[:-4] + '.c'
    else:
        output_file = "output.c"

    with open(output_file, "w") as f:
        f.write(c_code)
    print(f"\nCodice salvato in '{output_file}'.")
