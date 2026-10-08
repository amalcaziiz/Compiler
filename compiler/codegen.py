class CodeGenerator:
    def __init__(self, instrs):
        self.instrs = instrs
        self.assembly = []
        # Register tracker: maps variable name -> register name
        self.reg_map = {}
        # List of available registers
        self.registers = ["R1", "R2", "R3", "R4", "R5"]
        self.reg_pool = list(self.registers)

    def allocate_register(self, var_name):
        # If already allocated, return it
        if var_name in self.reg_map:
            return self.reg_map[var_name]
        
        # If pool has registers, pop one
        if self.reg_pool:
            reg = self.reg_pool.pop(0)
            self.reg_map[var_name] = reg
            return reg
        
        # Spilling (re-use first register to keep it simple)
        reg = self.registers[0]
        self.reg_map[var_name] = reg
        return reg

    def free_register_for_var(self, var_name):
        if var_name in self.reg_map:
            reg = self.reg_map.pop(var_name)
            if reg not in self.reg_pool:
                self.reg_pool.append(reg)
                self.reg_pool.sort() # keep R1, R2 order

    def generate(self):
        for i, instr in enumerate(self.instrs):
            self.translate_instruction(instr, i)
        return self.assembly

    def emit(self, text):
        self.assembly.append(text)

    def translate_instruction(self, instr, index):
        op = instr.op

        if op == "label":
            self.emit(f"{instr.result}:")
            # Reset registers on label boundaries to keep assembly blocks clean
            self.reg_map.clear()
            self.reg_pool = list(self.registers)
            return

        if op == "goto":
            self.emit(f"JMP {instr.result}")
            return

        if op == "ifFalse":
            cond = instr.arg1
            label = instr.result
            if cond in self.reg_map:
                reg = self.reg_map[cond]
                self.emit(f"CMP {reg}, 0")
                self.emit(f"JE {label}")
                self.free_register_for_var(cond)
            else:
                # If literal boolean or variable not loaded
                self.emit(f"MOV R1, {cond}")
                self.emit(f"CMP R1, 0")
                self.emit(f"JE {label}")
            return

        if op == "print":
            arg = instr.arg1
            if arg in self.reg_map:
                reg = self.reg_map[arg]
                self.emit(f"PRINT {reg}")
                self.free_register_for_var(arg)
            else:
                self.emit(f"PRINT {arg}")
            return

        # Binary Arithmetic and Relational Operations
        if op in ("+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">="):
            left = instr.arg1
            right = instr.arg2
            dest = instr.result

            # Check if left operand is already in a register
            if left in self.reg_map:
                reg = self.reg_map[left]
                # We can reuse this register for the destination
                del self.reg_map[left]
                self.reg_map[dest] = reg
            else:
                reg = self.allocate_register(dest)
                self.emit(f"MOV {reg}, {left}")

            # Map op to assembly mnemonic
            op_map = {
                "+": "ADD",
                "-": "SUB",
                "*": "MUL",
                "/": "DIV",
                "%": "MOD",
            }

            if op in op_map:
                mnemonic = op_map[op]
                # If right is in a register, use it, else use raw value
                right_val = self.reg_map.get(right, right)
                self.emit(f"{mnemonic} {reg}, {right_val}")
            else:
                # Relational operations: CMP followed by conditional set or just CMP
                right_val = self.reg_map.get(right, right)
                self.emit(f"CMP {reg}, {right_val}")
                # For relational, set register value: 1 if condition met, 0 otherwise
                cond_set_map = {
                    "==": "SETE",
                    "!=": "SETNE",
                    "<": "SETL",
                    ">": "SETG",
                    "<=": "SETLE",
                    ">=": "SETGE"
                }
                self.emit(f"{cond_set_map[op]} {reg}")

            # Free right operand register if it was a temp
            if right in self.reg_map and right.startswith("t"):
                self.free_register_for_var(right)
            return

        # Unary Not
        if op == "!":
            arg = instr.arg1
            dest = instr.result
            if arg in self.reg_map:
                reg = self.reg_map[arg]
                del self.reg_map[arg]
                self.reg_map[dest] = reg
            else:
                reg = self.allocate_register(dest)
                self.emit(f"MOV {reg}, {arg}")
            self.emit(f"NOT {reg}")
            return

        # Copy Assignment
        if op == "=":
            src = instr.arg1
            dest = instr.result

            # E.g. x = y
            if src in self.reg_map:
                src_reg = self.reg_map[src]
                # If destination is a temporary, we just map it to the same register
                if dest.startswith("t"):
                    self.reg_map[dest] = src_reg
                    # Remove old association if src was a temp
                    if src.startswith("t"):
                        del self.reg_map[src]
                else:
                    # User variable: we must write to memory/variable location
                    self.emit(f"MOV {dest}, {src_reg}")
                    if src.startswith("t"):
                        self.free_register_for_var(src)
            else:
                # src is a literal or variable not in register
                if dest.startswith("t"):
                    reg = self.allocate_register(dest)
                    self.emit(f"MOV {reg}, {src}")
                else:
                    self.emit(f"MOV {dest}, {src}")
            return
