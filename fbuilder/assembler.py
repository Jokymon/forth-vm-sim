import struct
from lark import Transformer


reg_encoding = {
    "ip": 0x0,
    "wp": 0x1,
    "rsp": 0x2,
    "dsp": 0x3,
    "acc1": 0x4,
    "acc2": 0x5,
}


MOVR_W = 0x20
MOVR_B = 0x21


instructions = {
    "nop": 0x00,

    "inc_wp": 0x10,

    "add": 0x30,

    "ifkt": 0xfe,
    "illegal": 0xff,
}


def aligned(address, alignment):
    return (address + alignment - 1) // alignment * alignment


class VmForthAssembler(Transformer):
    def __init__(self, load_address=0):
        self.macros = {}
        self.constants = {}

        self.previous_word_start = load_address
        self.binary_code = b""

    def _append_uint32(self, number):
        self.binary_code += struct.pack("<I", number)

    def start(self, arg):
        return self.binary_code

    def code_block(self, args):
        self.binary_code += b"".join(args)

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
        elif mnemonic == "movr":
            opcode = MOVR_W
            if len(args)==3 and str(args[1])=="b":
                opcode = MOVR_B
            indirect_target = 0x0
            indirect_source = 0x0
            reg_target = args[-1][0]
            reg_source = args[-1][1]
            if reg_target[0] == "%":
                reg_target = reg_target[1:]
            else:
                reg_target = reg_target[2:-1]
                indirect_target = 0x8
            if reg_source[0] == "%":
                reg_source = reg_source[1:]
            else:
                reg_source = reg_source[2:-1]
                indirect_source = 0x8
            reg_target = reg_encoding[reg_target]
            reg_source = reg_encoding[reg_source]
            code = struct.pack("BB", opcode,
                (reg_source | indirect_source) | (reg_target | indirect_target) << 4)
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
        return str(args[0])

    def register_indirect(self, args):
        return "["+str(args[0])+"]"

    def immediate_number(self, args):
        number = args[0]
        if number.__class__.__name__=="Token":
            return self.constants[str(number)]
        else:
            return number

    def number(self, arg):
        number_text = arg[0]
        if number_text.startswith("0x"):
            return int(number_text[2:], 16)
        else:
            return int(number_text)