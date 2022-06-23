import pathlib
import struct
from lark import Lark, Transformer


reg_encoding = {
    "ip": 0x0,
    "wp": 0x1,
    "rsp": 0x2,
    "dsp": 0x3,
    "acc1": 0x4,
    "acc2": 0x5,
    "pc": 0x7,
}


MOVR_W = 0x20
MOVR_B = 0x21
MOVS_ID_W = 0x22    # indirect <-- direct move
MOVS_ID_B = 0x23    # CURRENTLY NOT SUPPORTED/IMPLEMENTED
MOVS_DI_W = 0x24    # direct <-- indirect move
MOVS_DI_B = 0x25    # CURRENTLY NOT SUPPORTED/IMPLEMENTED
JMPI_IP = 0x60
JMPI_WP = 0x61
JMPI_ACC1 = 0x62
JMPI_ACC2 = 0x63
JMPD = 0x64

JUMP_MARKER = b"\x64\xff\xaa"


instructions = {
    "nop": 0x00,

    "inc_wp": 0x10,

    "add": 0x30,

    "ifkt": 0xfe,
    "illegal": 0xff,
}


def aligned(address, alignment):
    return (address + alignment - 1) // alignment * alignment


class RegisterOperand:
    def __init__(self, mnemonic_name, *args):
        if type(mnemonic_name)!=str:
            mnemonic_name=str(mnemonic_name)
        self.mnemonic_name = mnemonic_name
        self.name = mnemonic_name[1:]
        self.encoding = reg_encoding[self.name]
        self.args = args
        self.is_indirect = "indirect" in self.args

    def is_(self, property):
        return property in self.args

    def __str__(self):
        s = f"Register {self.mnemonic_name}"
        if self.is_indirect:
            s += " (indirect)"
        return s


class JumpOperand:
    def __init__(self, jump_target):
        self.jump_target = jump_target


class VmForthAssembler(Transformer):
    def __init__(self, load_address=0):
        self.macros = {}
        self.constants = {}
        self.jump_targets = {}
        self.jumps = []

        self.previous_word_start = load_address
        self.binary_code = b""

    def _append_uint32(self, number):
        self.binary_code += struct.pack("<I", number)

    def start(self, arg):
        new_code = b""
        old_code = self.binary_code
        start_of_jump = old_code.find(JUMP_MARKER)
        while start_of_jump >= 0:
            new_code += old_code[:start_of_jump+1]  # +1 to keep the 0x64
            jmp_index = struct.unpack("<H", old_code[start_of_jump+3:start_of_jump+5])[0]
            jump_target = self.jumps[jmp_index]
            new_code += struct.pack("<I", self.jump_targets[jump_target])
            old_code = old_code[start_of_jump+5:]
            start_of_jump = old_code.find(JUMP_MARKER)
        new_code += old_code
        self.binary_code = new_code

        return self.binary_code

    def code_block(self, args):
        code = b"".join(args)
        start_of_jump = code.find(b"``")
        while start_of_jump >= 0:
            self.binary_code += code[:start_of_jump]
            code = code[start_of_jump+2:]
            end_of_jump = code.find(b"``")
            jump_target = code[:end_of_jump].decode("utf-8")
            self.jump_targets[jump_target] = len(self.binary_code)
            code = code[end_of_jump+2:]
            start_of_jump = code.find(b"``")
        self.binary_code += code

    def code_definition(self, args):
        current_position = len(self.binary_code)
        # Append back-link
        self._append_uint32(self.previous_word_start)
        self.previous_word_start = current_position

        word_name = str(args[0])

        # Append length and word text
        self.binary_code += struct.pack("B", len(word_name))
        self.binary_code += bytes(word_name, encoding="utf-8")

        # Append CFA field which is just the current address +4 for code words
        current_position = len(self.binary_code)
        self._append_uint32(current_position+4)

        # Append the byte code of the code word definition
        self.binary_code += b"".join(args[1:])

    def macro_definition(self, args):
        macro_name = str(args[0])
        macro_code = b"".join(args[1:])
        self.macros[macro_name] = macro_code

    def constant_definition(self, args):
        constant_name = str(args[0])
        constant_value = args[1]
        self.constants[constant_name] = constant_value

    def code_line(self, args):
        return args[0]

    def instruction(self, args):
        mnemonic = str(args[0])
        if mnemonic == "ifkt":
            code = struct.pack("B", instructions[mnemonic])
            code += struct.pack("<H", args[1][0])
        elif mnemonic == "jmp":
            operand = args[1][0]
            if isinstance(operand, JumpOperand):
                next_jumps_index = len(self.jumps)
                self.jumps.append(operand.jump_target)
                code = JUMP_MARKER + struct.pack("<H", next_jumps_index)
            elif operand.name == "ip":
                code = b"\x60"
            elif operand.name == "wp":
                code = b"\x61"
            elif operand.name == "acc1":
                code = b"\x62"
            elif operand.name == "acc2":
                code = b"\x63"
            else:
                raise ValueError(f"Unsupported operand for register indirect jump on line {args[0].line}: {register_operand.mnemonic_name}; must be one of %ip, %wp, %acc1 or %acc2")
        elif mnemonic == "movr":
            opcode = MOVR_W
            if len(args)==3 and str(args[1])=="b":
                opcode = MOVR_B
            indirect_target = 0x0
            indirect_source = 0x0
            reg_target = args[-1][0]
            reg_source = args[-1][1]
            if reg_target.is_("increment") or reg_target.is_("decrement") or \
                reg_source.is_("increment") or reg_source.is_("decrement"):
                raise ValueError(f"movr doesn't support any increment or decrement operations on line {args[0].line}")
            if reg_target.is_indirect:
                indirect_target = 0x8
            if reg_source.is_indirect:
                indirect_source = 0x8
            code = struct.pack("BB", opcode,
                (reg_source.encoding | indirect_source) | (reg_target.encoding | indirect_target) << 4)
        elif mnemonic == "movs":
            operand = 0x0
            reg_target = args[-1][0]
            reg_source = args[-1][1]
            if reg_target.is_indirect:
                if reg_source.is_indirect:
                    raise ValueError(f"only one argument can be register indirect for movs on line {args[0].line}")
                opcode = MOVS_ID_W
                if reg_target.is_("decrement"):
                    operand |= 0x80
                if reg_target.is_("prefix"):
                    operand |= 0x40
                elif not reg_target.is_("postfix"):
                    raise ValueError(f"movs indirect target requires a pre- or post- increment or decrement on line {args[0].line}")
            else:
                if not reg_source.is_indirect:
                    raise ValueError(f"only one argument can be register direct for movs on line {args[0].line}")
                opcode = MOVS_DI_W
                if reg_source.is_("decrement"):
                    operand |= 0x80
                if reg_source.is_("prefix"):
                    operand |= 0x40
                elif not reg_source.is_("postfix"):
                    raise ValueError(f"movs indirect source requires a pre- or post- increment or decrement on line {args[0].line}")
            operand |= (reg_target.encoding << 3)
            operand |= reg_source.encoding
            code = struct.pack("BB", opcode, operand)
        else:
            if not mnemonic in instructions:
                raise ValueError(f"Unknown instruction '{mnemonic}' on line {args[0].line}")
            code = struct.pack("B", instructions[mnemonic])
        return code

    def macro_call(self, args):
        macro_name = str(args[0])
        if not macro_name in self.macros:
            raise ValueError(f"Undefined Macro: '{macro_name}' on line {args[0].line}")
        return self.macros[macro_name]

    def paramlist(self, args):
        return args

    def param(self, args):
        return args[0]

    def word(self, args):
        return str(args[0])

    def register(self, args):
        return RegisterOperand(args[0])

    def register_indirect(self, args):
        return args[0]

    def register_plain_indirect(self, args):
        return RegisterOperand(args[0], "indirect")

    def register_indirect_prefix(self, args):
        operation = "increment"
        if str(args[0]) == "--":
            operation = "decrement"
        return RegisterOperand(args[1], "indirect", "prefix", operation)

    def register_indirect_postfix(self, args):
        operation = "increment"
        if str(args[1]) == "--":
            operation = "decrement"
        return RegisterOperand(args[0], "indirect", "postfix", operation)

    def immediate_number(self, args):
        number = args[0]
        if number.__class__.__name__=="Token":
            return self.constants[str(number)]
        else:
            return number

    def label(self, args):
        return b"``"+bytes(str(args[0]), encoding="utf-8")+b"``"

    def jump_target(self, args):
        return JumpOperand(args[0])

    def decrement_increment(self, args):
        return str(args[0])

    def number(self, arg):
        number_text = arg[0]
        if number_text.startswith("0x"):
            return int(number_text[2:], 16)
        else:
            return int(number_text)


def assemble(input_text):
    script_dir = pathlib.Path(__file__).parent
    lark_grammar_path = script_dir / "grammar.lark"
    grammar = lark_grammar_path.read_text()
    lark_parser = Lark(grammar, parser='lalr', transformer=VmForthAssembler())

    return lark_parser.parse(input_text)
