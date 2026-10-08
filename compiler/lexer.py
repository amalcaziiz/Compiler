import re

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, {self.line}:{self.column})"

    def to_dict(self):
        return {
            "type": self.type,
            "value": self.value,
            "line": self.line,
            "column": self.column
        }

class Lexer:
    # Token specification
    RULES = [
        ("COMMENT_BLOCK", r"/\*[\s\S]*?\*/"),
        ("COMMENT_LINE", r"//[^\n]*"),
        ("FLOAT", r"\d+\.\d+"),
        ("INTEGER", r"\d+"),
        ("STRING", r'"[^"\\]*(?:\\.[^"\\]*)*"'),
        ("CHAR", r"'[^'\\]'"),
        # Operators (longer ones first)
        ("EQ", r"=="),
        ("NE", r"!="),
        ("LE", r"<="),
        ("GE", r">="),
        ("AND", r"&&"),
        ("OR", r"\|\|"),
        ("ADD", r"\+"),
        ("SUB", r"-"),
        ("MUL", r"\*"),
        ("DIV", r"/"),
        ("MOD", r"%"),
        ("LT", r"<"),
        ("GT", r">"),
        ("ASSIGN", r"="),
        ("NOT", r"!"),
        # Delimiters
        ("SEMI", r";"),
        ("COMMA", r","),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("LBRACE", r"\{"),
        ("RBRACE", r"\}"),
        # Identifiers
        ("ID", r"[a-zA-Z_][a-zA-Z0-9_]*"),
        # Whitespace and Newlines
        ("NEWLINE", r"\n"),
        ("SKIP", r"[ \t\r]+"),
        # Catch-all for invalid tokens
        ("MISMATCH", r"."),
    ]

    KEYWORDS = {
        "int": "KEYWORD",
        "float": "KEYWORD",
        "char": "KEYWORD",
        "bool": "KEYWORD",
        "if": "KEYWORD",
        "else": "KEYWORD",
        "while": "KEYWORD",
        "print": "KEYWORD",
        "true": "BOOL_LIT",
        "false": "BOOL_LIT"
    }

    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.errors = []
        self.compile_rules()

    def compile_rules(self):
        parts = []
        for name, regex in self.RULES:
            parts.append(f"(?P<{name}>{regex})")
        self.master_regex = re.compile("|".join(parts))

    def tokenize(self):
        line = 1
        line_start = 0
        
        for m in self.master_regex.finditer(self.code):
            token_type = m.lastgroup
            token_value = m.group(token_type)
            column = m.start() - line_start + 1

            if token_type == "NEWLINE":
                line += 1
                line_start = m.end()
            elif token_type == "SKIP":
                continue
            elif token_type == "COMMENT_LINE":
                self.tokens.append(Token("COMMENT", token_value, line, column))
            elif token_type == "COMMENT_BLOCK":
                self.tokens.append(Token("COMMENT", token_value, line, column))
                newlines_count = token_value.count("\n")
                if newlines_count > 0:
                    line += newlines_count
                    line_start = m.start() + token_value.rfind("\n") + 1
            elif token_type == "MISMATCH":
                self.errors.append({
                    "message": f"Lexical Error: Invalid character '{token_value}'",
                    "line": line,
                    "column": column
                })
                self.tokens.append(Token("INVALID", token_value, line, column))
            else:
                if token_type == "ID" and token_value in self.KEYWORDS:
                    type_ = self.KEYWORDS[token_value]
                    self.tokens.append(Token(type_, token_value, line, column))
                else:
                    self.tokens.append(Token(token_type, token_value, line, column))

        return self.tokens, self.errors

if __name__ == "__main__":
    code = """
    int x = 10;
    float y = x + 5.5;
    if (x > 5) {
        print(y);
    }
    """
    lexer = Lexer(code)
    tokens, errors = lexer.tokenize()
    for t in tokens:
        print(t)
    print("Errors:", errors)
