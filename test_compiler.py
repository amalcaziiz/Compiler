import unittest
import sys
import os

# Add current folder to sys.path to find compiler modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compiler.lexer import Lexer, Token
from compiler.parser import Parser
from compiler.semantic_analyzer import SemanticAnalyzer
from compiler.tac_generator import TACGenerator, TACInstruction
from compiler.optimizer import Optimizer
from compiler.codegen import CodeGenerator

class TestLexer(unittest.TestCase):
    def test_basic_tokens(self):
        code = "int x = 10; float y = 5.5;"
        lexer = Lexer(code)
        tokens, errors = lexer.tokenize()
        
        self.assertEqual(len(errors), 0)
        self.assertGreater(len(tokens), 0)
        
        # Check specific tokens
        self.assertEqual(tokens[0].type, "KEYWORD")
        self.assertEqual(tokens[0].value, "int")
        self.assertEqual(tokens[1].type, "ID")
        self.assertEqual(tokens[1].value, "x")
        self.assertEqual(tokens[2].type, "ASSIGN")
        self.assertEqual(tokens[3].type, "INTEGER")
        self.assertEqual(tokens[3].value, "10")
        self.assertEqual(tokens[4].type, "SEMI")

    def test_floating_point_scanning(self):
        code = "3.14 0.005 99.9"
        lexer = Lexer(code)
        tokens, errors = lexer.tokenize()
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0].type, "FLOAT")
        self.assertEqual(tokens[0].value, "3.14")
        self.assertEqual(tokens[1].type, "FLOAT")
        self.assertEqual(tokens[1].value, "0.005")
        self.assertEqual(tokens[2].type, "FLOAT")
        self.assertEqual(tokens[2].value, "99.9")
        
    def test_comments(self):
        code = "int a = 1; // this is inline comment\n/* block \n comment */ float b = 2.0;"
        lexer = Lexer(code)
        tokens, errors = lexer.tokenize()
        
        self.assertEqual(len(errors), 0)
        types = [t.type for t in tokens]
        self.assertIn("COMMENT", types)
        
        parser = Parser(tokens)
        ast, parse_errors = parser.parse()
        self.assertEqual(len(parse_errors), 0)

    def test_invalid_tokens(self):
        code = "int a = 10 @;"
        lexer = Lexer(code)
        tokens, errors = lexer.tokenize()
        
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["message"], "Lexical Error: Invalid character '@'")
        self.assertEqual(tokens[4].type, "INVALID")

class TestParser(unittest.TestCase):
    def test_valid_syntax(self):
        code = "int a = 10; if (a > 5) { print(a); }"
        lexer = Lexer(code)
        tokens, _ = lexer.tokenize()
        parser = Parser(tokens)
        ast, errors = parser.parse()
        
        self.assertEqual(len(errors), 0)
        self.assertIsNotNone(ast)

    def test_invalid_syntax(self):
        code = "int = a 10;"
        lexer = Lexer(code)
        tokens, _ = lexer.tokenize()
        parser = Parser(tokens)
        ast, errors = parser.parse()
        
        self.assertGreater(len(errors), 0)

class TestSymbolTableAndSemantics(unittest.TestCase):
    def test_undeclared_variable(self):
        # x is not declared
        code = "x = 10;"
        lexer = Lexer(code)
        tokens, _ = lexer.tokenize()
        parser = Parser(tokens)
        ast, _ = parser.parse()
        
        analyzer = SemanticAnalyzer()
        errors, _ = analyzer.analyze(ast)
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("undeclared" in e["message"] for e in errors))

    def test_duplicate_declarations(self):
        # Double declaration of x
        code = "int x = 10; float x = 20.0;"
        lexer = Lexer(code)
        tokens, _ = lexer.tokenize()
        parser = Parser(tokens)
        ast, _ = parser.parse()
        
        analyzer = SemanticAnalyzer()
        errors, _ = analyzer.analyze(ast)
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Duplicate declaration" in e["message"] for e in errors))

    def test_type_mismatch(self):
        # Assign char literal to int variable
        code = "int x; x = 'c';"
        lexer = Lexer(code)
        tokens, _ = lexer.tokenize()
        parser = Parser(tokens)
        ast, _ = parser.parse()
        
        analyzer = SemanticAnalyzer()
        errors, _ = analyzer.analyze(ast)
        
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Cannot assign expression of type 'char'" in e["message"] for e in errors))

class TestTACGenerator(unittest.TestCase):
    def test_tac_generation(self):
        code = "a = (b + c) * d;"
        lexer = Lexer(code)
        tokens, _ = lexer.tokenize()
        
        # We declare a, b, c, d to avoid semantic errors during manual testing if needed,
        # but TAC generator directly walks parser ast.
        parser = Parser(tokens)
        ast, _ = parser.parse()
        
        tac_gen = TACGenerator()
        instrs = tac_gen.generate(ast)
        
        # Should generate t1 = b + c, t2 = t1 * d, a = t2
        self.assertEqual(len(instrs), 3)
        self.assertEqual(instrs[0].op, "+")
        self.assertEqual(instrs[0].arg1, "b")
        self.assertEqual(instrs[0].arg2, "c")
        self.assertEqual(instrs[1].op, "*")
        self.assertEqual(instrs[1].result, "t2")
        self.assertEqual(instrs[2].op, "=")
        self.assertEqual(instrs[2].result, "a")

class TestOptimizer(unittest.TestCase):
    def test_constant_folding_and_propagation(self):
        # x = 5 * 4; y = x + 2; -> x = 20; y = 22;
        instrs = [
            TACInstruction("*", "5", "4", "t1"),
            TACInstruction("=", "t1", None, "x"),
            TACInstruction("+", "x", "2", "t2"),
            TACInstruction("=", "t2", None, "y")
        ]
        
        optimizer = Optimizer(instrs)
        opt_instrs = optimizer.optimize()
        
        # After full propagation and folding:
        # t1 = 20
        # x = 20
        # t2 = 22
        # y = 22
        # Wait, if dead-code elimination is run, since t1 and t2 are compiler temporaries
        # and are not live at the end of block (since they are only read inside the block and then overwritten/assigned),
        # they might be optimized away!
        # Let's inspect the remaining instructions. Only x = 20 and y = 22 should remain!
        self.assertEqual(len(opt_instrs), 2)
        self.assertEqual(opt_instrs[0].op, "=")
        self.assertEqual(opt_instrs[0].arg1, "20")
        self.assertEqual(opt_instrs[0].result, "x")
        self.assertEqual(opt_instrs[1].op, "=")
        self.assertEqual(opt_instrs[1].arg1, "22")
        self.assertEqual(opt_instrs[1].result, "y")

    def test_algebraic_simplification(self):
        # x = a + 0; y = b * 0; z = c * 1; w = d / 1;
        instrs = [
            TACInstruction("+", "a", "0", "t1"),
            TACInstruction("=", "t1", None, "x"),
            TACInstruction("*", "b", "0", "t2"),
            TACInstruction("=", "t2", None, "y"),
            TACInstruction("*", "c", "1", "t3"),
            TACInstruction("=", "t3", None, "z"),
            TACInstruction("/", "d", "1", "t4"),
            TACInstruction("=", "t4", None, "w"),
        ]
        optimizer = Optimizer(instrs)
        opt_instrs = optimizer.optimize()
        
        # After optimization:
        # x = a
        # y = 0
        # z = c
        # w = d
        self.assertEqual(len(opt_instrs), 4)
        self.assertEqual(opt_instrs[0].op, "=")
        self.assertEqual(opt_instrs[0].arg1, "a")
        self.assertEqual(opt_instrs[0].result, "x")
        self.assertEqual(opt_instrs[1].op, "=")
        self.assertEqual(opt_instrs[1].arg1, "0")
        self.assertEqual(opt_instrs[1].result, "y")
        self.assertEqual(opt_instrs[2].op, "=")
        self.assertEqual(opt_instrs[2].arg1, "c")
        self.assertEqual(opt_instrs[2].result, "z")
        self.assertEqual(opt_instrs[3].op, "=")
        self.assertEqual(opt_instrs[3].arg1, "d")
        self.assertEqual(opt_instrs[3].result, "w")

class TestCodegen(unittest.TestCase):
    def test_assembly_generation(self):
        instrs = [
            TACInstruction("+", "b", "c", "t1"),
            TACInstruction("*", "t1", "d", "t2"),
            TACInstruction("=", "t2", None, "a")
        ]
        codegen = CodeGenerator(instrs)
        assembly = codegen.generate()
        
        self.assertGreater(len(assembly), 0)
        # Should contain MOV, ADD, MUL, MOV
        joined = "\n".join(assembly)
        self.assertIn("MOV R1, b", joined)
        self.assertIn("ADD R1, c", joined)
        self.assertIn("MUL R1, d", joined)
        self.assertIn("MOV a, R1", joined)

if __name__ == "__main__":
    unittest.main()
