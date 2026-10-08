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

print("--- RAW TAC ---")
for i in instrs:
    print(i)

opt = Optimizer(instrs)
# Trace propagate_and_fold
print("\n--- AFTER PROPAGATE & FOLD (Pass 1) ---")
p1_instrs, changed = opt.propagate_and_fold(instrs)
for i in p1_instrs:
    print(i)
print("Changed:", changed)

# Trace eliminate_dead_code
print("\n--- AFTER DCE (Pass 1) ---")
dce1_instrs, changed_dce = opt.eliminate_dead_code(p1_instrs)
for i in dce1_instrs:
    print(i)
print("Changed:", changed_dce)
