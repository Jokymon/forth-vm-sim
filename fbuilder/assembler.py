import struct
from lark import Transformer


instructions = {
    "nop": 0x00,

    "inc_wp": 0x10,

    "add": 0x20,

    "ifkt": 0xfe,
    "illegal": 0xff,
}


def aligned(address, alignment):
    return (address + alignment - 1) // alignment * alignment


class VmForthAssembler(Transformer):
    def __init__(self, load_address=0):
        self.macros = {}

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

    def code_line(self, args):
        return args[0]

    def instruction(self, args):
        mnemonic = str(args[0])
        if mnemonic == "ifkt":
            code = struct.pack("B", instructions[mnemonic])
            code += struct.pack("<H", args[1][0])
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

    def number(self, arg):
        (arg, ) = arg
        return int(arg[1:])