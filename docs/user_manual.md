# Mini Compiler for SimpleLang - User Manual

This document explains the architecture, language design, usage, and compilation pipeline of the **Mini Compiler for SimpleLang** project.

The project is a multi-stage educational compiler implemented in Python. It includes a command-line interface (CLI) and an interactive Web IDE that visualizes each compilation phase, including lexical analysis, parsing, semantic analysis, intermediate code generation, optimization, and target code generation.

---

# 1. Project Overview

The Mini Compiler translates programs written in **SimpleLang**, a custom programming language, through a complete compilation pipeline.

The compiler includes:

- A handwritten lexer for token generation
- A recursive descent parser for syntax analysis
- Abstract Syntax Tree (AST) construction
- Scoped symbol table management
- Semantic validation
- Three-Address Code (TAC) generation
- Basic block optimization
- Register-based target code generation
- Interactive Web IDE for visualizing compiler stages

## Supported Features

### Data Types
- `int`
- `float`
- `char`
- `bool`

### Control Structures
- Variable declarations
- Assignments
- Nested blocks
- `if`
- `if-else`
- `while` loops

### Operators

Arithmetic:
