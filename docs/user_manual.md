# Mini Compiler for SimpleLang - User Manual

This document explains the architecture, design, usage, and compilation pipeline of the Mini Compiler project.

The Mini Compiler is a multi-stage educational compiler written in Python. It translates programs written in a custom language called SimpleLang through several compiler phases, including lexical analysis, parsing, semantic analysis, intermediate code generation, optimization, and target code generation.

The project includes both a command-line interface (CLI) and an interactive Web IDE that allows users to visualize each stage of compilation.

---

## Project Features

### Supported Data Types
- int
- float
- char
- bool

### Supported Control Structures
- Variable declarations
- Assignments
- if statements
- if-else statements
- while loops
- Nested blocks

### Supported Operators

Arithmetic:
+, -, *, /, %

Relational:
<, >, <=, >=, ==, !=

Logical:
&&, ||, !

Assignment:
=

Built-in Function:

print(expression);

Comments:

- Single-line comments: //
- Multi-line comments: /* */

---

# Compiler Architecture

The compiler follows this pipeline:

Source Code

↓

Lexical Analysis

↓

Syntax Analysis

↓

Semantic Analysis

↓

Three-Address Code Generation

↓

Code Optimization

↓

Target Code Generation

↓

Assembly Output


---

# Compiler Components

## 1. Lexical Analysis

The lexer converts source code into tokens.

It identifies:

- Keywords
- Identifiers
- Operators
- Constants
- Comments

The lexer also tracks line and column positions for error reporting.

---

## 2. Syntax Analysis

The parser uses a handwritten Recursive Descent Parser.

It validates the program structure according to the SimpleLang grammar and generates an Abstract Syntax Tree (AST).

---

## 3. Symbol Table Management

The symbol table manages:

- Variable names
- Data types
- Scope levels
- Memory locations

Nested scopes are handled using a stack-based scope system.

---

## 4. Semantic Analysis

The semantic analyzer checks:

- Undeclared variables
- Duplicate declarations
- Type compatibility
- Invalid operations
- Boolean conditions for control statements

---

## 5. Intermediate Code Generation

The compiler converts the AST into Three-Address Code (TAC).

Example:

Source:

c = a + b;

Generated TAC:

t1 = a + b  
c = t1


---

## 6. Code Optimization

The optimizer improves intermediate code using:

- Constant Folding
- Constant Propagation
- Algebraic Simplification
- Copy Propagation
- Dead Code Elimination

Example:

Before:

x = 5 + 10

After:

x = 15


---

## 7. Target Code Generation

The final stage converts optimized TAC into register-based assembly instructions.

Generated instructions include:

- MOV
- ADD
- CMP
- JE

The compiler uses virtual registers to manage intermediate values.

---

# Interactive Web IDE

The project includes a browser-based IDE for demonstrating the compiler pipeline.

Features:

- Write SimpleLang programs
- Compile source code
- View tokens
- Explore AST structure
- Inspect symbol tables
- View semantic analysis results
- Compare raw and optimized TAC
- View generated assembly

Run the Web IDE:

```
python server.py
```

Then open:

```
http://localhost:8000
```

---

# Command Line Usage

Compile a program:

```
python main.py samples/valid_program.txt
```

---

# Project Structure

```
mini-compiler/

├── compiler/
│   ├── lexer.py
│   ├── parser.py
│   ├── symbol_table.py
│   ├── semantic_analyzer.py
│   ├── tac_generator.py
│   ├── optimizer.py
│   └── codegen.py

├── web/
│   ├── index.html
│   ├── styles.css
│   └── app.js

├── samples/
├── docs/
├── main.py
├── server.py
├── test_compiler.py
└── README.md
```

---

# Testing

The project includes automated tests covering:

- Lexer functionality
- Parser validation
- Symbol table operations
- Semantic checking
- TAC generation
- Optimization passes
- Code generation

Run:

```
python test_compiler.py
```

---

# Technical Highlights

- Built from scratch using Python
- Handwritten recursive descent parser
- Custom compiler pipeline
- Custom intermediate representation
- Multiple optimization techniques
- Interactive compiler visualization
- Zero external dependencies

---

# Project Purpose

This project demonstrates core compiler construction concepts, including language processing, parsing, intermediate representation design, optimization techniques, and code generation.
