# Mini Compiler for a Simple Programming Language - User Manual

This manual describes the architecture, grammar, usage, and compilation phases of the **Mini Compiler** project. 

---

## 1. Project Overview

The **Mini Compiler** is a fully functional, multi-stage compiler implemented in Python. It includes a command-line interface (CLI) and an interactive **Web-based IDE** that visualizes every step of compilation (Lexer, AST Parser, Symbol Table, Semantic Analyzer, TAC Generator, Optimizer, and Target Codegen) in real-time.

### Features Supported
* **Data Types**: `int`, `float`, `char`, `bool`
* **Control Structures**: Nested `if`, `if-else`, and `while` loops
* **Operators**:
  * *Arithmetic*: `+`, `-`, `*`, `/`, `%`
  * *Relational*: `<`, `>`, `<=`, `>=`, `==`, `!=`
  * *Logical*: `&&`, `||`, `!`
  * *Assignment*: `=`
* **System Functions**: `print(expression);`
* **Comments**: Single-line (`//...`) and Multi-line (`/*...*/`) comments are parsed and safely skipped.

---

## 2. Language Grammar (CFG)

The compiler uses a **Recursive Descent Parser** to enforce the following Context-Free Grammar (CFG):

```text
Program            -> StatementList
StatementList      -> Statement StatementList | ε
Statement          -> VarDecl | Assignment | PrintStmt | IfStmt | WhileStmt | Block
Block              -> '{' StatementList '}'
VarDecl            -> Type ID ';' | Type ID '=' Expression ';'
Type               -> 'int' | 'float' | 'char' | 'bool'
Assignment         -> ID '=' Expression ';'
PrintStmt          -> 'print' '(' Expression ')' ';'
IfStmt             -> 'if' '(' Expression ')' Statement ( 'else' Statement )?
WhileStmt          -> 'while' '(' Expression ')' Statement

Expression         -> LogicalOr
LogicalOr          -> LogicalAnd ( '||' LogicalAnd )*
LogicalAnd         -> Relational ( '&&' Relational )*
Relational         -> Additive ( RelationalOp Additive )*
RelationalOp       -> '<' | '>' | '<=' | '>=' | '==' | '!='
Additive           -> Multiplicative ( ('+' | '-') Multiplicative )*
Multiplicative     -> Primary ( ('*' | '/' | '%') Primary )*
Primary            -> ID | Constant | '(' Expression ')' | '!' Primary
Constant           -> INT_LIT | FLOAT_LIT | CHAR_LIT | BOOL_LIT
```

---

## 3. Getting Started & Installation

The compiler is designed to run out-of-the-box using only Python's standard library. **No external dependencies (no pip install) are required.**

### Prerequisites
* Python 3.8 or higher.

### Project Directory Layout
* `compiler/`: Submodules for each phase (Lexer, Parser, Symbol Table, Semantic Analyzer, TAC, Optimizer, Codegen).
* `web/`: Frontend static files (HTML, CSS, JS) for the Web IDE.
* `samples/`: Example source files for validation testing.
* `main.py`: Command Line Interface entrypoint.
* `server.py`: Local Web Server that hosts the Web IDE.
* `test_compiler.py`: Automated test suite.

---

## 4. How to Run the Web IDE (Recommended for Live Demo)

The Web IDE provides a state-of-the-art interactive playground to write code and visualize every compiler phase.

1. **Launch the server**:
   Run the following command in your terminal from the project root:
   ```bash
   python server.py
   ```
2. **Open the browser**:
   Navigate to [http://localhost:8000](http://localhost:8000).
3. **Select a preset**:
   Click on the sample buttons ("Valid Program", "Syntax Error", "Semantic Error") to load test cases, then click **Compile Code**.
4. **Inspect the results**:
   Click through the tabs:
   * **Lexer**: Visualizes tokens in a clean grid showing Lexeme, Token Type, and Line/Col.
   * **AST Parser**: Displays a nested tree view of the Abstract Syntax Tree.
   * **Symbol Table**: Displays name, type, scope level, constant initial values, and memory addresses.
   * **Semantics**: Displays semantic verification checkmarks or error reports.
   * **TAC Code**: Displays the raw intermediate Three-Address Code.
   * **Optimizer**: Shows a side-by-side comparison of Raw and Optimized TAC (featuring Constant Propagation, Constant Folding, and Dead Code Elimination).
   * **Assembly**: Displays the target machine instructions using virtual registers.

---

## 5. How to Run the CLI

For standard CLI compilation, run:
```bash
python main.py samples/valid_program.txt
```

### CLI Arguments
* `python main.py <source_file>`: Compiles the source file and displays all stages.
* `python main.py <source_file> --no-optimize`: Skips the intermediate optimization phase.

---

## 6. Detailed Compiler Phases

### Phase 1: Lexical Analyzer (Scanner)
Tokenizes the raw string sequence into structural Token records. Captures exact coordinate positions (Line/Column) for reporting. If a character mismatch is found, it creates an `INVALID` token and records it as a compilation error.

### Phase 2: Syntax Analyzer (Parser)
Verifies token sequences against grammar rules using recursive descent. Syntactic errors automatically trigger synchronization: the parser skips ahead to delimiters (like `;` or `}`) or control statement keywords to capture subsequent syntax errors rather than crashing immediately.

### Phase 3: Symbol Table Management
Tracks variables across nested scopes. Entering `{` pushes a new scope onto the stack, and exiting `}` pops it off. Variables are resolved from inside-out, and memory addresses are automatically allocated using virtual byte alignments (`0x0000`, `0x0004`, etc.).

### Phase 4: Semantic Analysis
Walks the AST to enforce runtime typing and scoping rules:
* **Undeclared Variable Error**: Verifies that every identifier is declared in the current or outer scopes before it is used. If a variable is read or assigned without a matching declaration, the compiler throws:
  `Semantic Error: Variable '<name>' is undeclared` (or `undeclared before assignment`).
* **Duplicate Declaration Error**: Prevents re-declaring the same variable within the same local scope level.
* **Type Mismatch Error**: Enforces compatible assignments (e.g. preventing assigning a string or char to an `int`) and compatible operation types (e.g., Modulo `%` requires both sides to be integers).
* **Control Conditions Check**: Enforces that condition expressions in `if` and `while` statement blocks must resolve to a boolean value.

### Phase 5: Intermediate Code Generation (TAC)
Translates nested arithmetic and logical expressions into simplified Three-Address Code instructions (e.g. `t1 = b + c`). Translates `if` and `while` control structures into conditional jump instructions (`ifFalse cond goto label`).

### Phase 6: Code Optimization
Optimizes the raw TAC sequence with a fixed-point iteration loop supporting:
1. **Constant Propagation**: Replaces variables bound to constants with their actual literals.
2. **Constant Folding**: Computes static arithmetic at compile-time (e.g. `t1 = 5 * 4` becomes `t1 = 20`).
3. **Algebraic Simplification**: Evaluates identity operations (e.g. `x + 0` -> `x`, `x * 0` -> `0`, `x * 1` -> `x`, `x - 0` -> `x`, `x / 1` -> `x`).
4. **Copy Propagation**: Replaces temporary reference copies with direct variables (e.g. replacing `t1 = a` and `x = t1` with `x = a`), eliminating intermediate load steps.
5. **Dead Code Elimination (DCE)**: Prunes unused temporary variables, streamlining register allocation.

### Phase 7: Target Code Generation (Bonus)
Translates optimized TAC into register-based assembly instructions (`MOV`, `ADD`, `MUL`, `CMP`, `JE`). Implements register tracking and allocation logic to map temporary computations into physical register sequences (e.g. `R1`, `R2`), minimizing register spills.

---

## 7. Automated Test Suite

A comprehensive test suite is included in `test_compiler.py`. It runs **13** rigorous unit tests asserting the behavior of each phase of the compiler, including comment handling, invalid tokens, floating-point numbers, and algebraic simplifications.

To execute the tests:
```bash
python test_compiler.py
```
