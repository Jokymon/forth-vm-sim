import struct
from lark import Transformer


instructions = {
    "nop": 0x00,
    "terminate": 0xfe,
    "illegal": 0xff,

    "input": 0x01,
    "output": 0x02,

    "push_ds": 0x03,
    "pop_ds": 0x04,
    "push_rs": 0x05,
    "pop_rs": 0x06
}


def aligned(address, alignment):
    return (address + alignment - 1) // alignment * alignment


class VmForthAssembler(Transformer):
    def __init__(self, load_address=0):
        self.previous_word_start = load_address
        self.binary_code = b""

    def start(self, arg):
        return self.binary_code

    def code_definition(self, arg):
        current_position = len(self.binary_code)
        self.binary_code += struct.pack("<I", self.previous_word_start)
        self.previous_word_start = current_position

        word_name = str(arg[0])

        self.binary_code += struct.pack("B", len(word_name))
        self.binary_code += bytes(word_name, encoding="utf-8")

        self.binary_code += arg[1]

    def instruction(self, arg):
        mnemonic = str(arg[0])
        if not mnemonic in instructions:
            raise ValueError(f"Unknown instruction: '{mnemonic}'")
        return struct.pack("B", instructions[mnemonic])

    def word(self, arg):
        return f"Got {arg}"