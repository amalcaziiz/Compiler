from compiler.tac_generator import TACInstruction

def is_literal(val):
    if val is None:
        return False
    val = str(val)
    if val.startswith("'") and val.endswith("'"):
        return True
    if val.startswith('"') and val.endswith('"'):
        return True
    if val in ("true", "false"):
        return True
    try:
        float(val)
        return True
    except ValueError:
        return False

def parse_literal(val):
    val = str(val)
    if val == "true":
        return True
    if val == "false":
        return False
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1]
    if val.startswith('"') and val.endswith('"'):
        return val[1:-1]
    if "." in val:
        return float(val)
    return int(val)

def format_literal(val):
    if isinstance(val, bool):
        return "true" if val else "false"
    elif isinstance(val, str):
        if len(val) == 1:
            return f"'{val}'"
        return f'"{val}"'
    elif isinstance(val, float):
        # Keep float formatting clean
        return f"{val:.6f}".rstrip("0").rstrip(".") if not val.is_integer() else f"{int(val)}.0"
    return str(val)

def eval_op(op, arg1, arg2=None):
    try:
        val1 = parse_literal(arg1)
        val2 = parse_literal(arg2) if arg2 is not None else None
        
        if op == "+": return val1 + val2
        if op == "-": return val1 - val2
        if op == "*": return val1 * val2
        if op == "/": 
            if val2 == 0: return None
            return val1 / val2
        if op == "%": return val1 % val2
        if op == "<": return val1 < val2
        if op == ">": return val1 > val2
        if op == "<=": return val1 <= val2
        if op == ">=": return val1 >= val2
        if op == "==": return val1 == val2
        if op == "!=": return val1 != val2
        if op == "&&": return bool(val1 and val2)
        if op == "||": return bool(val1 or val2)
        if op == "!": return not val1
    except Exception:
        pass
    return None

class Optimizer:
    def __init__(self, instructions):
        self.instructions = instructions

    def optimize(self):
        # We perform iterative optimizations until no more changes occur
        # (Fixed-point iteration)
        current_instrs = self.instructions
        while True:
            changed = False
            
            # 1. Constant propagation and folding
            opt_instrs, prop_changed = self.propagate_and_fold(current_instrs)
            
            # 2. Dead code elimination
            opt_instrs, dce_changed = self.eliminate_dead_code(opt_instrs)
            
            if not prop_changed and not dce_changed:
                break
            current_instrs = opt_instrs
            
        return current_instrs

    def propagate_and_fold(self, instrs):
        optimized = []
        constants = {} # Map variable name -> constant string literal
        copies = {}    # Map variable name -> variable name (copy propagation)
        changed = False

        for instr in instrs:
            # If we encounter control flow, we reset constants and copies to remain safe
            if instr.op in ("label", "goto", "ifFalse"):
                constants.clear()
                copies.clear()
                
                # However, we still propagate if it's conditional check!
                if instr.op == "ifFalse":
                    cond = instr.arg1
                    if cond in constants:
                        new_cond = constants[cond]
                        optimized.append(TACInstruction("ifFalse", new_cond, None, instr.result, instr.line))
                        changed = True
                        continue
                    elif cond in copies:
                        new_cond = copies[cond]
                        optimized.append(TACInstruction("ifFalse", new_cond, None, instr.result, instr.line))
                        changed = True
                        continue
                
                optimized.append(instr)
                continue

            if instr.op == "print":
                arg = instr.arg1
                if arg in constants:
                    arg = constants[arg]
                    changed = True
                elif arg in copies:
                    arg = copies[arg]
                    changed = True
                optimized.append(TACInstruction("print", arg, None, None, instr.line))
                continue

            # Check operands and propagate
            arg1 = instr.arg1
            arg2 = instr.arg2
            
            if arg1 in constants:
                arg1 = constants[arg1]
                changed = True
            elif arg1 in copies:
                arg1 = copies[arg1]
                changed = True
                
            if arg2 in constants:
                arg2 = constants[arg2]
                changed = True
            elif arg2 in copies:
                arg2 = copies[arg2]
                changed = True

            # Perform folding if operands are literals
            if instr.op in ("+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||"):
                if is_literal(arg1) and is_literal(arg2):
                    folded_val = eval_op(instr.op, arg1, arg2)
                    if folded_val is not None:
                        folded_str = format_literal(folded_val)
                        new_instr = TACInstruction("=", folded_str, None, instr.result, instr.line)
                        optimized.append(new_instr)
                        constants[instr.result] = folded_str
                        if instr.result in copies:
                            del copies[instr.result]
                        changed = True
                        continue

            # Perform algebraic simplification
            if instr.op in ("+", "-", "*", "/"):
                simplified = False
                if instr.op == "+":
                    if arg1 in ("0", "0.0"):
                        new_instr = TACInstruction("=", arg2, None, instr.result, instr.line)
                        optimized.append(new_instr)
                        simplified = True
                    elif arg2 in ("0", "0.0"):
                        new_instr = TACInstruction("=", arg1, None, instr.result, instr.line)
                        optimized.append(new_instr)
                        simplified = True
                elif instr.op == "-":
                    if arg2 in ("0", "0.0"):
                        new_instr = TACInstruction("=", arg1, None, instr.result, instr.line)
                        optimized.append(new_instr)
                        simplified = True
                elif instr.op == "*":
                    if arg1 in ("0", "0.0") or arg2 in ("0", "0.0"):
                        new_instr = TACInstruction("=", "0", None, instr.result, instr.line)
                        optimized.append(new_instr)
                        simplified = True
                    elif arg1 in ("1", "1.0"):
                        new_instr = TACInstruction("=", arg2, None, instr.result, instr.line)
                        optimized.append(new_instr)
                        simplified = True
                    elif arg2 in ("1", "1.0"):
                        new_instr = TACInstruction("=", arg1, None, instr.result, instr.line)
                        optimized.append(new_instr)
                        simplified = True
                elif instr.op == "/":
                    if arg2 in ("1", "1.0"):
                        new_instr = TACInstruction("=", arg1, None, instr.result, instr.line)
                        optimized.append(new_instr)
                        simplified = True

                if simplified:
                    if is_literal(optimized[-1].arg1):
                        constants[instr.result] = optimized[-1].arg1
                        if instr.result in copies:
                            del copies[instr.result]
                    else:
                        copies[instr.result] = optimized[-1].arg1
                        if instr.result in constants:
                            del constants[instr.result]
                    changed = True
                    continue

            elif instr.op == "!":
                if is_literal(arg1):
                    folded_val = eval_op("!", arg1)
                    if folded_val is not None:
                        folded_str = format_literal(folded_val)
                        new_instr = TACInstruction("=", folded_str, None, instr.result, instr.line)
                        optimized.append(new_instr)
                        constants[instr.result] = folded_str
                        if instr.result in copies:
                            del copies[instr.result]
                        changed = True
                        continue

            elif instr.op == "=":
                if is_literal(arg1):
                    constants[instr.result] = arg1
                    if instr.result in copies:
                        del copies[instr.result]
                else:
                    copies[instr.result] = arg1
                    if instr.result in constants:
                        del constants[instr.result]
                
                # Invalidate any copies that point to this redefined variable
                if instr.result:
                    to_delete = [k for k, v in copies.items() if v == instr.result]
                    for k in to_delete:
                        del copies[k]
                
                new_instr = TACInstruction("=", arg1, None, instr.result, instr.line)
                optimized.append(new_instr)
                continue

            # Default fallback for other/complex assignments
            if instr.result:
                if instr.result in constants:
                    del constants[instr.result]
                if instr.result in copies:
                    del copies[instr.result]
                # Invalidate copies pointing to this variable
                to_delete = [k for k, v in copies.items() if v == instr.result]
                for k in to_delete:
                    del copies[k]
                    
            optimized.append(TACInstruction(instr.op, arg1, arg2, instr.result, instr.line))

        return optimized, changed

    def eliminate_dead_code(self, instrs):
        optimized = []
        changed = False
        live_vars = set()

        # Step 1: Scan backwards to check variable liveness
        # All user variables (variables not starting with 't') are treated as live by default at the end of the block
        # Jumps, prints, and conditional branches make their arguments live
        for instr in reversed(instrs):
            if instr.op in ("goto", "label"):
                optimized.append(instr)
                continue

            if instr.op == "ifFalse":
                live_vars.add(instr.arg1)
                optimized.append(instr)
                continue
                
            if instr.op == "print":
                live_vars.add(instr.arg1)
                optimized.append(instr)
                continue

            # Assignment instruction
            if instr.result:
                is_temp = instr.result.startswith("t")
                # If it's a compiler temporary and it is NOT live, we can eliminate it!
                if is_temp and instr.result not in live_vars:
                    changed = True
                    # Do not append this instruction (eliminate it!)
                    continue
                else:
                    # It is live. Mark it as no longer live (defined here)
                    if instr.result in live_vars:
                        live_vars.remove(instr.result)
                    
                    # Mark its operands as live
                    if instr.arg1 and not is_literal(instr.arg1):
                        live_vars.add(instr.arg1)
                    if instr.arg2 and not is_literal(instr.arg2):
                        live_vars.add(instr.arg2)
            
            optimized.append(instr)

        # Since we scanned backwards, we reverse the list back to normal order
        optimized.reverse()
        return optimized, changed
