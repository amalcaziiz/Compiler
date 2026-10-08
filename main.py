import sys
import os

# Add the current folder to sys.path to resolve imports cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic_analyzer import SemanticAnalyzer
from compiler.tac_generator import TACGenerator
from compiler.optimizer import Optimizer
from compiler.codegen import CodeGenerator

def compile_source(code, optimize=True):
    print("=" * 60)
    print(" STAGE 1: Lexical Analysis (Scanner)")
    print("=" * 60)
    lexer = Lexer(code)
    tokens, lex_errors = lexer.tokenize()
    
    if lex_errors:
        print("\n[!] Lexical Errors Found:")
        for err in lex_errors:
            print(f"  Line {err['line']}, Column {err['column']}: {err['message']}")
        return False

    print(f"Successfully scanned. Generated {len(tokens)} tokens.")
    # Show first 15 tokens
    for t in tokens[:15]:
        print(f"  {t}")
    if len(tokens) > 15:
        print(f"  ... and {len(tokens) - 15} more tokens.")

    print("\n" + "=" * 60)
    print(" STAGE 2: Syntax Analysis (Parser)")
    print("=" * 60)
    parser = Parser(tokens)
    ast, parse_errors = parser.parse()

    if parse_errors:
        print("\n[!] Syntax Errors Found:")
        for err in parse_errors:
            print(f"  Line {err['line']}, Column {err['column']}: {err['message']}")
        return False

    print("Successfully parsed. Abstract Syntax Tree (AST) generated.")

    print("\n" + "=" * 60)
    print(" STAGE 3: Semantic Analysis & Symbol Table")
    print("=" * 60)
    analyzer = SemanticAnalyzer()
    sem_errors, symbol_table = analyzer.analyze(ast)

    if sem_errors:
        print("\n[!] Semantic Errors Found:")
        for err in sem_errors:
            print(f"  Line {err['line']}, Column {err['column']}: {err['message']}")
        return False

    print("Successfully analyzed semantics. No semantic errors found.")
    print("\nActive Symbol Table:")
    print(f"  {'Variable':<12} {'Type':<8} {'Scope':<6} {'Initial':<10} {'Address':<8}")
    print("  " + "-" * 50)
    for sym in symbol_table.get_all_declared_symbols():
        print(f"  {sym['name']:<12} {sym['type']:<8} {sym['scope_level']:<6} {sym['initial_value']:<10} {sym['memory_address']:<8}")

    print("\n" + "=" * 60)
    print(" STAGE 4: Intermediate Code Generation (TAC)")
    print("=" * 60)
    tac_gen = TACGenerator()
    tac_instrs = tac_gen.generate(ast)
    
    print("Raw Three-Address Code:")
    for instr in tac_instrs:
        print(f"  {instr}")

    if optimize:
        print("\n" + "=" * 60)
        print(" STAGE 5: Code Optimization")
        print("=" * 60)
        optimizer = Optimizer(tac_instrs)
        opt_instrs = optimizer.optimize()
        
        print("Optimized Three-Address Code (Constant Propagation & Folding, DCE):")
        for instr in opt_instrs:
            print(f"  {instr}")
        
        final_tac = opt_instrs
    else:
        final_tac = tac_instrs

    print("\n" + "=" * 60)
    print(" STAGE 6 (Bonus): Target Code Generation (Assembly)")
    print("=" * 60)
    codegen = CodeGenerator(final_tac)
    assembly = codegen.generate()
    
    print("Generated Assembly Instructions:")
    for line in assembly:
        print(f"  {line}")

    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <source_file> [--no-optimize]")
        sys.exit(1)

    filepath = sys.argv[1]
    optimize = "--no-optimize" not in sys.argv

    if not os.path.exists(filepath):
        print(f"Error: Source file '{filepath}' not found.")
        sys.exit(1)

    with open(filepath, "r") as f:
        code = f.read()

    print(f"Compiling source file: {filepath}\n")
    success = compile_source(code, optimize)
    if success:
        print("\n[+] Compilation Completed Successfully!")
    else:
        print("\n[-] Compilation Failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
