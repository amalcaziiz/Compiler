class TACInstruction:
    def __init__(self, op, arg1, arg2, result, line=None):
        self.op = op          # '+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '!', '=', 'goto', 'ifFalse', 'label', 'print'
        self.arg1 = arg1      # First operand (or condition)
        self.arg2 = arg2      # Second operand
        self.result = result  # Destination variable or target label
        self.line = line

    def __repr__(self):
        if self.op == "label":
            return f"{self.result}:"
        elif self.op == "goto":
            return f"goto {self.result}"
        elif self.op == "ifFalse":
            return f"ifFalse {self.arg1} goto {self.result}"
        elif self.op == "print":
            return f"print {self.arg1}"
        elif self.op == "=":
            return f"{self.result} = {self.arg1}"
        elif self.op in ("+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||"):
            return f"{self.result} = {self.arg1} {self.op} {self.arg2}"
        elif self.op == "!":
            return f"{self.result} = !{self.arg1}"
        else:
            return f"{self.result} = {self.op} {self.arg1} {self.arg2}"

    def to_dict(self):
        return {
            "op": self.op,
            "arg1": str(self.arg1) if self.arg1 is not None else "",
            "arg2": str(self.arg2) if self.arg2 is not None else "",
            "result": str(self.result) if self.result is not None else "",
            "text": str(self)
        }

class TACGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def generate(self, ast_root):
        self.visit(ast_root)
        return self.instructions

    def emit(self, op, arg1, arg2, result, line=None):
        instr = TACInstruction(op, arg1, arg2, result, line)
        self.instructions.append(instr)
        return instr

    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No visit_{type(node).__name__} method defined in TACGenerator")

    def visit_ProgramNode(self, node):
        for stmt in node.statements:
            self.visit(stmt)
        return None

    def visit_BlockNode(self, node):
        for stmt in node.statements:
            self.visit(stmt)
        return None

    def visit_VarDeclNode(self, node):
        if node.initializer:
            expr_val = self.visit(node.initializer)
            self.emit("=", expr_val, None, node.name, node.line)
        return None

    def visit_AssignmentNode(self, node):
        expr_val = self.visit(node.value)
        self.emit("=", expr_val, None, node.name, node.line)
        return None

    def visit_PrintStmtNode(self, node):
        expr_val = self.visit(node.expression)
        self.emit("print", expr_val, None, None, node.line)
        return None

    def visit_IfStmtNode(self, node):
        cond_val = self.visit(node.condition)
        
        l_else = self.new_label()
        l_end = self.new_label()

        self.emit("ifFalse", cond_val, None, l_else, node.line)
        self.visit(node.then_branch)
        self.emit("goto", None, None, l_end, node.line)
        
        self.emit("label", None, None, l_else, node.line)
        if node.else_branch:
            self.visit(node.else_branch)
            
        self.emit("label", None, None, l_end, node.line)
        return None

    def visit_WhileStmtNode(self, node):
        l_start = self.new_label()
        l_end = self.new_label()

        self.emit("label", None, None, l_start, node.line)
        cond_val = self.visit(node.condition)
        self.emit("ifFalse", cond_val, None, l_end, node.line)
        self.visit(node.body)
        self.emit("goto", None, None, l_start, node.line)
        self.emit("label", None, None, l_end, node.line)
        return None

    def visit_BinaryOpNode(self, node):
        left_val = self.visit(node.left)
        right_val = self.visit(node.right)
        temp = self.new_temp()
        self.emit(node.op, left_val, right_val, temp, node.line)
        return temp

    def visit_UnaryOpNode(self, node):
        expr_val = self.visit(node.expression)
        temp = self.new_temp()
        self.emit(node.op, expr_val, None, temp, node.line)
        return temp

    def visit_LiteralNode(self, node):
        # Format true/false for TAC to be uniform
        if node.val_type == "bool":
            return "true" if node.value else "false"
        elif node.val_type == "char":
            return f"'{node.value}'"
        elif node.val_type == "string":
            return f'"{node.value}"'
        return str(node.value)

    def visit_IdentifierNode(self, node):
        return node.name
