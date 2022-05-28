import struct
from lark import Transformer


instructions = {
    "nop": 0x00,
    "dump": 0xfd,
    "terminate": 0xfe,
    "illegal": 0xff,

    "input": 0x01,
    "output": 0x02,

    "inc_wp": 0x10,

    "add": 0x20,
}


def aligned(address, alignment):
    return (address + alignment - 1) // alignment * alignment


class VmForthAssembler(Transformer):
    def __init__(self, load_address=0):
        self.previous_word_start = load_address
        self.binary_code = b""

    def _append_uint32(self, number):
        self.binary_code += struct.pack("<I", number)

    def _macro_next(self):
        result = b""
        # TODO: get cfa from current wp
        result += struct.pack("B", instructions["inc_wp"])
        # TODO: jump to address given in cfa determined from previous wp
        return result

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

        # Append NEXT instructions
        self.binary_code += self._macro_next()

    def instruction(self, arg):
        mnemonic = str(arg[0])
        if not mnemonic in instructions:
            raise ValueError(f"Unknown instruction: '{mnemonic}'")
        return struct.pack("B", instructions[mnemonic])

    def word(self, arg):
        return f"Got {arg}"