from compiler.symbol_table import SymbolTable

class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.errors = []

    def get_expr_string(self, node):
        if not node:
            return ""
        node_name = type(node).__name__
        if node_name == "LiteralNode":
            return str(node.value)
        elif node_name == "IdentifierNode":
            return str(node.name)
        elif node_name == "BinaryOpNode":
            left = self.get_expr_string(node.left)
            right = self.get_expr_string(node.right)
            return f"{left} {node.op} {right}"
        elif node_name == "UnaryOpNode":
            expr = self.get_expr_string(node.expression)
            return f"{node.op}{expr}"
        return "expr"

    def analyze(self, ast_root):
        self.visit(ast_root)
        return self.errors, self.symbol_table

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    def visit_ProgramNode(self, node):
        for stmt in node.statements:
            self.visit(stmt)
        return None

    def visit_BlockNode(self, node):
        self.symbol_table.enter_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self.symbol_table.exit_scope()
        return None

    def visit_VarDeclNode(self, node):
        # 1. Check duplicate declaration in current scope
        if self.symbol_table.lookup_current_scope(node.name):
            self.errors.append({
                "message": f"Semantic Error: Duplicate declaration of variable '{node.name}' in the same scope",
                "line": node.line,
                "column": node.col
            })
            return None

        # 2. Check initializer type if exists
        init_type = None
        if node.initializer:
            init_type = self.visit(node.initializer)
            if init_type:
                # Type check rules
                if node.var_type == "int":
                    if init_type != "int":
                        self.errors.append({
                            "message": f"Semantic Error: Cannot initialize variable '{node.name}' of type 'int' with expression of type '{init_type}'",
                            "line": node.line,
                            "column": node.col
                        })
                elif node.var_type == "float":
                    # Implicit conversion from int to float is allowed
                    if init_type not in ("int", "float"):
                        self.errors.append({
                            "message": f"Semantic Error: Cannot initialize variable '{node.name}' of type 'float' with expression of type '{init_type}'",
                            "line": node.line,
                            "column": node.col
                        })
                elif node.var_type == "bool":
                    if init_type != "bool":
                        self.errors.append({
                            "message": f"Semantic Error: Cannot initialize variable '{node.name}' of type 'bool' with expression of type '{init_type}'",
                            "line": node.line,
                            "column": node.col
                        })
                elif node.var_type == "char":
                    if init_type != "char":
                        self.errors.append({
                            "message": f"Semantic Error: Cannot initialize variable '{node.name}' of type 'char' with expression of type '{init_type}'",
                            "line": node.line,
                            "column": node.col
                        })

        # 3. Declare symbol
        initial_val = self.get_expr_string(node.initializer) if node.initializer else None
        self.symbol_table.declare(node.name, node.var_type, initial_value=initial_val)
        return None

    def visit_AssignmentNode(self, node):
        symbol = self.symbol_table.lookup(node.name)
        if not symbol:
            self.errors.append({
                "message": f"Semantic Error: Variable '{node.name}' is undeclared before assignment",
                "line": node.line,
                "column": node.col
            })
            return None

        expr_type = self.visit(node.value)
        if expr_type:
            # Assignment check rules
            if symbol.type == "int":
                if expr_type != "int":
                    self.errors.append({
                        "message": f"Semantic Error: Cannot assign expression of type '{expr_type}' to variable '{node.name}' of type 'int'",
                        "line": node.line,
                        "column": node.col
                    })
            elif symbol.type == "float":
                if expr_type not in ("int", "float"):
                    self.errors.append({
                        "message": f"Semantic Error: Cannot assign expression of type '{expr_type}' to variable '{node.name}' of type 'float'",
                        "line": node.line,
                        "column": node.col
                    })
            elif symbol.type == "bool":
                if expr_type != "bool":
                    self.errors.append({
                        "message": f"Semantic Error: Cannot assign expression of type '{expr_type}' to variable '{node.name}' of type 'bool'",
                        "line": node.line,
                        "column": node.col
                    })
            elif symbol.type == "char":
                if expr_type != "char":
                    self.errors.append({
                        "message": f"Semantic Error: Cannot assign expression of type '{expr_type}' to variable '{node.name}' of type 'char'",
                        "line": node.line,
                        "column": node.col
                    })

        # Update symbol table initial/assigned value
        val_str = self.get_expr_string(node.value)
        self.symbol_table.update_initial_value(node.name, val_str)
        return None

    def visit_PrintStmtNode(self, node):
        self.visit(node.expression)
        return None

    def visit_IfStmtNode(self, node):
        cond_type = self.visit(node.condition)
        if cond_type and cond_type != "bool":
            self.errors.append({
                "message": f"Semantic Error: Condition in 'if' statement must be 'bool', found '{cond_type}'",
                "line": node.line,
                "column": node.col
            })
        
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)
        return None

    def visit_WhileStmtNode(self, node):
        cond_type = self.visit(node.condition)
        if cond_type and cond_type != "bool":
            self.errors.append({
                "message": f"Semantic Error: Condition in 'while' statement must be 'bool', found '{cond_type}'",
                "line": node.line,
                "column": node.col
            })
        self.visit(node.body)
        return None

    def visit_BinaryOpNode(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)

        if not left_type or not right_type:
            return None

        op = node.op

        # 1. Arithmetic Operators
        if op in ("+", "-", "*", "/", "%"):
            if op == "%":
                # Modulo is strict: int % int -> int
                if left_type != "int" or right_type != "int":
                    self.errors.append({
                        "message": f"Semantic Error: Modulo operator '%' is only valid for integers, found '{left_type}' % '{right_type}'",
                        "line": node.line,
                        "column": node.col
                    })
                    return "int"
                return "int"

            # Check if both are numeric (int/float)
            if left_type not in ("int", "float") or right_type not in ("int", "float"):
                self.errors.append({
                    "message": f"Semantic Error: Operator '{op}' is not supported between types '{left_type}' and '{right_type}'",
                    "line": node.line,
                    "column": node.col
                })
                return "int" # fallback

            # If either is float, the result is float
            if left_type == "float" or right_type == "float":
                return "float"
            return "int"

        # 2. Relational Operators
        elif op in ("<", ">", "<=", ">="):
            if left_type not in ("int", "float") or right_type not in ("int", "float"):
                self.errors.append({
                    "message": f"Semantic Error: Comparison operator '{op}' is only valid for numeric types, found '{left_type}' and '{right_type}'",
                    "line": node.line,
                    "column": node.col
                })
            return "bool"

        elif op in ("==", "!="):
            # Check compatible types (e.g. both numeric, both boolean, both char)
            is_numeric = left_type in ("int", "float") and right_type in ("int", "float")
            is_same = left_type == right_type
            if not (is_numeric or is_same):
                self.errors.append({
                    "message": f"Semantic Error: Equality operator '{op}' is not valid between types '{left_type}' and '{right_type}'",
                    "line": node.line,
                    "column": node.col
                })
            return "bool"

        # 3. Logical Operators
        elif op in ("&&", "||"):
            if left_type != "bool" or right_type != "bool":
                self.errors.append({
                    "message": f"Semantic Error: Logical operator '{op}' requires boolean operands, found '{left_type}' and '{right_type}'",
                    "line": node.line,
                    "column": node.col
                })
            return "bool"

        return None

    def visit_UnaryOpNode(self, node):
        expr_type = self.visit(node.expression)
        if not expr_type:
            return None

        if node.op == "!":
            if expr_type != "bool":
                self.errors.append({
                    "message": f"Semantic Error: Logical negation '!' is only valid for 'bool', found '{expr_type}'",
                    "line": node.line,
                    "column": node.col
                })
            return "bool"
        return None

    def visit_LiteralNode(self, node):
        return node.val_type

    def visit_IdentifierNode(self, node):
        symbol = self.symbol_table.lookup(node.name)
        if not symbol:
            self.errors.append({
                "message": f"Semantic Error: Variable '{node.name}' is undeclared",
                "line": node.line,
                "column": node.col
            })
            return None
        return symbol.type
