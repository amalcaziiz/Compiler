import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic_analyzer import SemanticAnalyzer
from compiler.tac_generator import TACGenerator
from compiler.optimizer import Optimizer

code = """
int a = 10;
int b = 20;
int c;
c = a + b;

if (c > 20) {
    print(c);
}
"""

lexer = Lexer(code)
tokens, _ = lexer.tokenize()
parser = Parser(tokens)
ast, _ = parser.parse()
tac_gen = TACGenerator()
instrs = tac_gen.generate(ast)

opt = Optimizer(instrs)
p1_instrs, _ = opt.propagate_and_fold(instrs)

print("Tracing eliminate_dead_code backwards:")
live_vars = set()
for instr in reversed(p1_instrs):
    print(f"\nProcessing: {instr}")
    print(f"  Op: {repr(instr.op)}, Result: {repr(instr.result)}, Arg1: {repr(instr.arg1)}, Arg2: {repr(instr.arg2)}")
    if instr.op in ("goto", "label"):
        print("  SKIPPED because op in (goto, label)")
        continue

    if instr.op == "ifFalse":
        print(f"  Adding {instr.arg1} to live_vars")
        live_vars.add(instr.arg1)
        # Wait, does it append? Yes, it continues past other ifs!
        # Oh, wait! In optimizer.py:
        # if instr.op == "ifFalse":
        #     live_vars.add(instr.arg1)
        #     continue  <-- WAIT! DOES IT HAVE A CONTINUE HERE?
        # Let's check!
