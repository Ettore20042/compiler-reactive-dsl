"""
Modulo: test_compiler.py
Suite di test automatizzati per il compilatore del linguaggio roboLang.
Verifica le varie fasi: Parsing, Precedenza Operatori, Analisi Semantica, e Generazione Codice.
"""
import unittest
import sys
from lark import Lark
from src.grammar import grammar
from src.transformer import ASTTransformer
from src.semantic import SemanticAnalyzer
from src.codegen import CGenerator
from src.ast_nodes import *

class TestRoboLangCompiler(unittest.TestCase):

    def setUp(self):
        self.parser = Lark(grammar, parser='lalr')
        self.transformer = ASTTransformer()

    def parse_to_ast(self, source):
        tree = self.parser.parse(source)
        return self.transformer.transform(tree)

    def test_expression_folding(self):
        """Verifica che il folding sinistro-associativo delle espressioni lunghe funzioni."""
        source = "var a: int = 1 + 2 + 3;"
        ast = self.parse_to_ast(source)
        self.assertEqual(len(ast), 1)
        var_decl = ast[0]
        self.assertIsInstance(var_decl, VarDecl)
        
        expr = var_decl.value
        self.assertIsInstance(expr, BinOp)
        self.assertEqual(expr.op, "+")
        self.assertEqual(expr.right.value, "3")
        
        self.assertIsInstance(expr.left, BinOp)
        self.assertEqual(expr.left.op, "+")
        self.assertEqual(expr.left.left.value, "1")
        self.assertEqual(expr.left.right.value, "2")

    def test_operator_precedence(self):
        """Verifica che la precedenza degli operatori (* precede +) sia corretta."""
        source = "var a: int = 1 + 2 * 3;"
        ast = self.parse_to_ast(source)
        var_decl = ast[0]
        expr = var_decl.value
        
        # Dovrebbe essere parsed come: 1 + (2 * 3)
        self.assertIsInstance(expr, BinOp)
        self.assertEqual(expr.op, "+")
        self.assertEqual(expr.left.value, "1")
        
        self.assertIsInstance(expr.right, BinOp)
        self.assertEqual(expr.right.op, "*")
        self.assertEqual(expr.right.left.value, "2")
        self.assertEqual(expr.right.right.value, "3")

    def test_type_coercion_int_to_real(self):
        """Verifica che un valore int possa essere assegnato implicitamente a un tipo real (coercion)."""
        source = "var x: real = 5;"
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)  # Non deve sollevare eccezioni
        self.assertEqual(analyzer.symbol_table["x"], "real")

    def test_semantic_duplicate_var(self):
        """Verifica che la dichiarazione di variabili duplicate nello stesso scope sollevi errore."""
        source = """
        var x: int = 10;
        var x: bool = false;
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception) as ctx:
            analyzer.analyze(ast)
        self.assertIn("già dichiarata", str(ctx.exception))

    def test_semantic_undeclared_var(self):
        """Verifica che l'uso di una variabile non dichiarata sollevi un errore."""
        source = "set y = 20;"
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception) as ctx:
            analyzer.analyze(ast)
        self.assertIn("non dichiarata", str(ctx.exception))

    def test_semantic_type_mismatch(self):
        """Verifica che l'assegnazione di tipi incompatibili (es. string a int) fallisca."""
        source = """
        var x: int = 10;
        set x = "test_string";
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception) as ctx:
            analyzer.analyze(ast)
        self.assertIn("Errore di tipo", str(ctx.exception))

    def test_duplicate_function_parameter(self):
        """Verifica che parametri duplicati nella firma di una funzione sollevino un errore."""
        source = """
        task run(a: int, a: real) {
            log(a);
        }
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception) as ctx:
            analyzer.analyze(ast)
        self.assertIn("parametro 'a' duplicato", str(ctx.exception))

    def test_void_function_and_empty_return(self):
        """Verifica che un task void con return vuoto o senza return passi i controlli semantici."""
        source = """
        task logWarning() {
            log("Attenzione!");
            return;
        }
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        
        # Verifica il codice C generato
        generator = CGenerator()
        c_code = generator.generate(ast)
        self.assertIn("void logWarning(void)", c_code)

    def test_mismatch_return_type(self):
        """Verifica che restituire un tipo errato in una funzione sollevi errore."""
        source = """
        task getValue() -> int {
            return "non_un_intero";
        }
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception) as ctx:
            analyzer.analyze(ast)
        self.assertIn("return attende 'int', ottenuto 'string'", str(ctx.exception))

    def test_built_in_functions(self):
        """Verifica la corretta registrazione e risoluzione dei tipi per read_int e read_real."""
        source = """
        var x: int = read_int();
        var y: real = read_real();
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        self.assertEqual(analyzer.symbol_table["x"], "int")
        self.assertEqual(analyzer.symbol_table["y"], "real")

    def test_codegen_c_full(self):
        """Genera codice C da un programma roboLang completo e verifica la correttezza della sintassi generata."""
        source = """
        task calculatePower(base: real, exponent: int) -> real {
            var result: real = 1.0;
            var i: int = 0;
            while (i < exponent) {
                set result = result * base;
                set i = i + 1;
            }
            return result;
        }
        var p: real = calculatePower(2.5, 3);
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        
        generator = CGenerator()
        c_code = generator.generate(ast)
        self.assertIn("double calculatePower(double base, int exponent)", c_code)
        self.assertIn("double result = 1.0;", c_code)
        self.assertIn("while ((i < exponent))", c_code)
        self.assertIn("double p = calculatePower(2.5, 3);", c_code)

if __name__ == '__main__':
    unittest.main()
