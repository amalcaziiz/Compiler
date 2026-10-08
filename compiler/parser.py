class ASTNode:
    def to_dict(self):
        raise NotImplementedError()

class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

    def to_dict(self):
        return {
            "name": "Program",
            "children": [s.to_dict() for s in self.statements]
        }

class VarDeclNode(ASTNode):
    def __init__(self, var_type, name, initializer, line, col):
        self.var_type = var_type
        self.name = name
        self.initializer = initializer
        self.line = line
        self.col = col

    def to_dict(self):
        children = [
            {"name": f"Type: {self.var_type}"},
            {"name": f"Name: {self.name}"}
        ]
        if self.initializer:
            children.append({
                "name": "Initializer",
                "children": [self.initializer.to_dict()]
            })
        return {
            "name": "VarDecl",
            "children": children
        }

class AssignmentNode(ASTNode):
    def __init__(self, name, value, line, col):
        self.name = name
        self.value = value
        self.line = line
        self.col = col

    def to_dict(self):
        return {
            "name": f"Assign: {self.name}",
            "children": [self.value.to_dict()]
        }

class PrintStmtNode(ASTNode):
    def __init__(self, expression, line, col):
        self.expression = expression
        self.line = line
        self.col = col

    def to_dict(self):
        return {
            "name": "Print",
            "children": [self.expression.to_dict()]
        }

class IfStmtNode(ASTNode):
    def __init__(self, condition, then_branch, else_branch, line, col):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch
        self.line = line
        self.col = col

    def to_dict(self):
        children = [
            {
                "name": "Condition",
                "children": [self.condition.to_dict()]
            },
            {
                "name": "Then",
                "children": [self.then_branch.to_dict()]
            }
        ]
        if self.else_branch:
            children.append({
                "name": "Else",
                "children": [self.else_branch.to_dict()]
            })
        return {
            "name": "IfStatement",
            "children": children
        }

class WhileStmtNode(ASTNode):
    def __init__(self, condition, body, line, col):
        self.condition = condition
        self.body = body
        self.line = line
        self.col = col

    def to_dict(self):
        return {
            "name": "WhileStatement",
            "children": [
                {
                    "name": "Condition",
                    "children": [self.condition.to_dict()]
                },
                {
                    "name": "Body",
                    "children": [self.body.to_dict()]
                }
            ]
        }

class BlockNode(ASTNode):
    def __init__(self, statements, line, col):
        self.statements = statements
        self.line = line
        self.col = col

    def to_dict(self):
        return {
            "name": "Block",
            "children": [s.to_dict() for s in self.statements]
        }

class BinaryOpNode(ASTNode):
    def __init__(self, left, op, right, line, col):
        self.left = left
        self.op = op
        self.right = right
        self.line = line
        self.col = col

    def to_dict(self):
        return {
            "name": f"Op: {self.op}",
            "children": [self.left.to_dict(), self.right.to_dict()]
        }

class UnaryOpNode(ASTNode):
    def __init__(self, op, expression, line, col):
        self.op = op
        self.expression = expression
        self.line = line
        self.col = col

    def to_dict(self):
        return {
            "name": f"UnaryOp: {self.op}",
            "children": [self.expression.to_dict()]
        }

class LiteralNode(ASTNode):
    def __init__(self, value, val_type, line, col):
        self.value = value
        self.val_type = val_type
        self.line = line
        self.col = col

    def to_dict(self):
        return {
            "name": f"Literal ({self.val_type}): {self.value}"
        }

class IdentifierNode(ASTNode):
    def __init__(self, name, line, col):
        self.name = name
        self.line = line
        self.col = col

    def to_dict(self):
        return {
            "name": f"ID: {self.name}"
        }


class ParserError(Exception):
    def __init__(self, message, line, col):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col

class Parser:
    def __init__(self, tokens):
        self.tokens = [t for t in tokens if t.type != "COMMENT"]
        self.current = 0
        self.errors = []

    def is_at_end(self):
        return self.current >= len(self.tokens)

    def peek(self):
        if self.is_at_end():
            # Return a special EOF token at the correct position
            if len(self.tokens) > 0:
                last = self.tokens[-1]
                return Token("EOF", "", last.line, last.column + len(last.value))
            return Token("EOF", "", 1, 1)
        return self.tokens[self.current]

    def previous(self):
        return self.tokens[self.current - 1]

    def advance(self):
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def check(self, type_):
        if self.is_at_end():
            return False
        return self.peek().type == type_

    def match(self, *types):
        for type_ in types:
            if self.check(type_):
                self.advance()
                return True
        return False

    def consume(self, type_, message):
        if self.check(type_):
            return self.advance()
        token = self.peek()
        raise ParserError(f"Syntax Error: {message} (found '{token.value}' instead)", token.line, token.column)

    def parse(self):
        statements = []
        while not self.is_at_end():
            try:
                stmt = self.statement()
                if stmt:
                    statements.append(stmt)
            except ParserError as e:
                self.errors.append({
                    "message": e.message,
                    "line": e.line,
                    "column": e.col
                })
                self.synchronize()
        return ProgramNode(statements), self.errors

    def synchronize(self):
        self.advance()
        while not self.is_at_end():
            if self.previous().type == "SEMI":
                return
            if self.peek().type in ("KEYWORD", "LBRACE", "RBRACE"):
                # If we hit keyword (like int, float, if, while) or block start/end, we start parsing statement
                # Wait, if keyword is one of the data types or control structures:
                if self.peek().value in ("int", "float", "char", "bool", "if", "while", "print"):
                    return
            self.advance()

    def statement(self):
        # We peek to decide the statement type
        token = self.peek()
        
        # Block Statement
        if self.match("LBRACE"):
            return self.block_statement()

        # Variable Declaration Statement or other Keyword statements
        if token.type == "KEYWORD":
            if token.value in ("int", "float", "char", "bool"):
                return self.declaration_statement()
            elif token.value == "if":
                return self.if_statement()
            elif token.value == "while":
                return self.while_statement()
            elif token.value == "print":
                return self.print_statement()
            else:
                raise ParserError(f"Unexpected keyword '{token.value}'", token.line, token.column)
        
        # Assignment Statement (must start with identifier)
        if token.type == "ID":
            return self.assignment_statement()

        raise ParserError(f"Unexpected token '{token.value}'", token.line, token.column)

    def block_statement(self):
        line, col = self.previous().line, self.previous().column
        statements = []
        while not self.check("RBRACE") and not self.is_at_end():
            try:
                stmt = self.statement()
                if stmt:
                    statements.append(stmt)
            except ParserError as e:
                self.errors.append({
                    "message": e.message,
                    "line": e.line,
                    "column": e.col
                })
                self.synchronize()
        self.consume("RBRACE", "Expected '}' to close block")
        return BlockNode(statements, line, col)

    def declaration_statement(self):
        type_token = self.advance() # consume type keyword
        var_type = type_token.value
        line, col = type_token.line, type_token.column

        id_token = self.consume("ID", "Expected identifier after type name")
        name = id_token.value

        initializer = None
        if self.match("ASSIGN"):
            initializer = self.expression()

        self.consume("SEMI", "Expected ';' at the end of declaration")
        return VarDeclNode(var_type, name, initializer, line, col)

    def assignment_statement(self):
        id_token = self.advance()
        name = id_token.value
        line, col = id_token.line, id_token.column

        self.consume("ASSIGN", "Expected '=' in assignment")
        expr = self.expression()
        self.consume("SEMI", "Expected ';' at the end of assignment")
        return AssignmentNode(name, expr, line, col)

    def print_statement(self):
        print_token = self.advance()
        line, col = print_token.line, print_token.column

        self.consume("LPAREN", "Expected '(' after print")
        expr = self.expression()
        self.consume("RPAREN", "Expected ')' after print expression")
        self.consume("SEMI", "Expected ';' at the end of print statement")
        return PrintStmtNode(expr, line, col)

    def if_statement(self):
        if_token = self.advance()
        line, col = if_token.line, if_token.column

        self.consume("LPAREN", "Expected '(' after if")
        cond = self.expression()
        self.consume("RPAREN", "Expected ')' after condition")
        
        then_branch = self.statement()
        else_branch = None
        if self.match("KEYWORD") and self.previous().value == "else":
            else_branch = self.statement()

        return IfStmtNode(cond, then_branch, else_branch, line, col)

    def while_statement(self):
        while_token = self.advance()
        line, col = while_token.line, while_token.column

        self.consume("LPAREN", "Expected '(' after while")
        cond = self.expression()
        self.consume("RPAREN", "Expected ')' after condition")
        body = self.statement()

        return WhileStmtNode(cond, body, line, col)

    # Expression parsing hierarchy
    def expression(self):
        return self.logical_or()

    def logical_or(self):
        expr = self.logical_and()
        while self.match("OR"):
            op = self.previous().value
            line, col = self.previous().line, self.previous().column
            right = self.logical_and()
            expr = BinaryOpNode(expr, op, right, line, col)
        return expr

    def logical_and(self):
        expr = self.relational()
        while self.match("AND"):
            op = self.previous().value
            line, col = self.previous().line, self.previous().column
            right = self.relational()
            expr = BinaryOpNode(expr, op, right, line, col)
        return expr

    def relational(self):
        expr = self.additive()
        if self.match("LT", "GT", "LE", "GE", "EQ", "NE"):
            op = self.previous().value
            line, col = self.previous().line, self.previous().column
            right = self.additive()
            expr = BinaryOpNode(expr, op, right, line, col)
        return expr

    def additive(self):
        expr = self.multiplicative()
        while self.match("ADD", "SUB"):
            op = self.previous().value
            line, col = self.previous().line, self.previous().column
            right = self.multiplicative()
            expr = BinaryOpNode(expr, op, right, line, col)
        return expr

    def multiplicative(self):
        expr = self.primary()
        while self.match("MUL", "DIV", "MOD"):
            op = self.previous().value
            line, col = self.previous().line, self.previous().column
            right = self.primary()
            expr = BinaryOpNode(expr, op, right, line, col)
        return expr

    def primary(self):
        if self.match("INTEGER"):
            token = self.previous()
            return LiteralNode(int(token.value), "int", token.line, token.column)
        if self.match("FLOAT"):
            token = self.previous()
            return LiteralNode(float(token.value), "float", token.line, token.column)
        if self.match("CHAR"):
            token = self.previous()
            # Strip quotes
            val = token.value[1:-1]
            return LiteralNode(val, "char", token.line, token.column)
        if self.match("STRING"):
            token = self.previous()
            # Strip quotes
            val = token.value[1:-1]
            return LiteralNode(val, "string", token.line, token.column)
        if self.match("BOOL_LIT"):
            token = self.previous()
            val = True if token.value == "true" else False
            return LiteralNode(val, "bool", token.line, token.column)
        if self.match("ID"):
            token = self.previous()
            return IdentifierNode(token.value, token.line, token.column)
        if self.match("LPAREN"):
            expr = self.expression()
            self.consume("RPAREN", "Expected ')' to match '('")
            return expr
        if self.match("NOT"):
            token = self.previous()
            expr = self.primary()
            return UnaryOpNode("!", expr, token.line, token.column)

        token = self.peek()
        raise ParserError(f"Expected expression, found '{token.value}'", token.line, token.column)

# Reimport Token for tests / imports
from compiler.lexer import Token
