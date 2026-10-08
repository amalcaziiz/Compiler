class Symbol:
    def __init__(self, name, type_, scope_level, initial_value=None, memory_address=None):
        self.name = name
        self.type = type_
        self.scope_level = scope_level
        self.initial_value = initial_value
        self.memory_address = memory_address

    def to_dict(self):
        return {
            "name": self.name,
            "type": self.type,
            "scope_level": self.scope_level,
            "initial_value": str(self.initial_value) if self.initial_value is not None else "-",
            "memory_address": self.memory_address if self.memory_address is not None else "-"
        }

class SymbolTable:
    def __init__(self):
        # Stack of dictionaries representing scopes
        self.scopes = [{}]
        self.current_scope_level = 0
        self.next_address = 0
        # A list to keep track of all symbols ever declared (useful for listing them in the GUI)
        self.all_symbols = []

    def enter_scope(self):
        self.scopes.append({})
        self.current_scope_level += 1

    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.current_scope_level -= 1

    def declare(self, name, type_, initial_value=None):
        # We assign an address like "0x" followed by the hexadecimal offset
        address_str = f"0x{self.next_address:04X}"
        self.next_address += 4 # 4 bytes per variable
        
        symbol = Symbol(
            name=name,
            type_=type_,
            scope_level=self.current_scope_level,
            initial_value=initial_value,
            memory_address=address_str
        )
        
        self.scopes[-1][name] = symbol
        self.all_symbols.append(symbol)
        return symbol

    def lookup(self, name):
        # Search from inner to outer scopes
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

    def lookup_current_scope(self, name):
        return self.scopes[-1].get(name)

    def update_initial_value(self, name, value):
        symbol = self.lookup(name)
        if symbol:
            symbol.initial_value = value

    def get_all_declared_symbols(self):
        return [sym.to_dict() for sym in self.all_symbols]
