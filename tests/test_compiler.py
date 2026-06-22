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
        self.parser = Lark(grammar, parser='lalr', propagate_positions=True)
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
        self.assertIn("Parametro 'a' duplicato", str(ctx.exception))

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

    # --- TEST PER I BUG FIX ---

    def test_undeclared_var_in_nested_expression(self):
        """BUG FIX 1: Variabili non dichiarate dentro espressioni annidate
        devono essere intercettate in Fase 1 (scope) con errore semantico pulito,
        non come KeyError generico in Fase 2."""
        source = """
        var x: int = 10;
        set x = x + ghost_var;
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        with self.assertRaises(Exception) as ctx:
            analyzer.analyze(ast)
        self.assertIn("non dichiarata", str(ctx.exception))
        self.assertIn("ghost_var", str(ctx.exception))

    def test_string_arithmetic_rejected(self):
        """BUG FIX 2: Espressioni come "abc" + 5 devono essere rifiutate
        dal type checker (operatore aritmetico su tipo non numerico)."""
        source = 'var x: int = 5 + 3;'  # questo va bene
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)  # Nessun errore

        # Ora testo un'espressione invalida in modo indiretto:
        # Costruisco manualmente un AST con "abc" + 5 per testare il type checker
        from src.typechecker import TypeChecker
        from src.scope import ScopeAnalyzer
        bad_expr = BinOp(Literal('string', '"abc"'), '+', Literal('int', '5'))
        scope = ScopeAnalyzer()
        tc = TypeChecker(scope)
        with self.assertRaises(Exception) as ctx:
            tc.get_expr_type(bad_expr)
        self.assertIn("non applicabile", str(ctx.exception))

    def test_parameter_shadowing_allowed(self):
        """BUG FIX 3: Un parametro di un task può avere lo stesso nome di una
        variabile globale (shadowing legittimo). Non deve dare errore."""
        source = """
        var x: int = 10;
        task double(x: int) -> int {
            return x + x;
        }
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)  # Non deve sollevare eccezioni

    def test_forward_declarations_in_c(self):
        """BUG FIX 4: Il codice C generato deve contenere forward declaration (prototipi)
        per permettere a un task di chiamare un altro task definito più avanti."""
        source = """
        task caller() {
            callee();
        }
        task callee() {
            log("called");
        }
        """
        ast = self.parse_to_ast(source)
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        generator = CGenerator()
        c_code = generator.generate(ast)
        # Verifica che i prototipi siano presenti PRIMA delle implementazioni
        proto_pos = c_code.find("void caller(void);")
        impl_pos = c_code.find("void caller(void) {")
        self.assertNotEqual(proto_pos, -1, "Prototipo di caller non trovato")
        self.assertLess(proto_pos, impl_pos, "Il prototipo deve precedere l'implementazione")

    def test_exponential_notation_is_real(self):
        """BUG FIX 5: Un numero in notazione esponenziale (es. 5e3) deve essere
        classificato come real, non come int."""
        source = "var x: real = 5e3;"
        ast = self.parse_to_ast(source)
        var_decl = ast[0]
        self.assertIsInstance(var_decl.value, Literal)
        self.assertEqual(var_decl.value.type, 'real')

        # Verifica anche che l'analisi semantica lo accetti come real
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        self.assertEqual(analyzer.symbol_table["x"], "real")

    def test_comments_supported(self):
        """Verifica che i commenti stile shell (#) vengano ignorati dal compilatore."""
        source = """
        # Questo è un commento iniziale
        var x: int = 42; # commento sulla riga di codice
        # un altro commento
        var y: real = 3.14;
        """
        ast = self.parse_to_ast(source)
        self.assertEqual(len(ast), 2)  # Solo le due dichiarazioni di variabili
        self.assertEqual(ast[0].name, 'x')
        self.assertEqual(ast[1].name, 'y')

        # Verifica che si compili senza problemi
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

if __name__ == '__main__':
    unittest.main()
