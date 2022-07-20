import pathlib
import struct

from lark import Lark, Token, Transformer
from lark.visitors import Interpreter


reg_encoding = {
    "ip": 0x0,
    "wp": 0x1,
    "rsp": 0x2,
    "dsp": 0x3,
    "acc1": 0x4,
    "acc2": 0x5,
    "pc": 0x7,
}


NOP = 0x00
MOVR_W = 0x20
MOVR_B = 0x21
MOVS_ID_W = 0x22    # indirect <-- direct move
MOVS_ID_B = 0x23    # CURRENTLY NOT SUPPORTED/IMPLEMENTED
MOVS_DI_W = 0x24    # direct <-- indirect move
MOVS_DI_B = 0x25    # CURRENTLY NOT SUPPORTED/IMPLEMENTED
MOVI_ACC1 = 0x26
JMPI_IP = 0x60
JMPI_WP = 0x61
JMPI_ACC1 = 0x62
JMPI_ACC2 = 0x63
JMPD = 0x64
JZ = 0x65
IFTK = 0xfe
ILLEGAL = 0xff

LABEL_MARKER = b"\xff\xaa"


def aligned(address, alignment):
    return (address + alignment - 1) // alignment * alignment


class RegisterOperand:
    def __init__(self, mnemonic_name, *args):
        self.mnemonic_name = mnemonic_name
        self.name = mnemonic_name[1:]
        self.encoding = reg_encoding[self.name]
        self.args = args
        self.is_indirect = "indirect" in self.args

    def is_(self, property):
        return property in self.args

    def __repr__(self):
        s = f"Register {self.mnemonic_name}"
        if self.is_indirect:
            s += " (indirect)"
        return s


class JumpOperand:
    def __init__(self, jump_target):
        self.jump_target = jump_target

    def __repr__(self):
        return f"Jump to {self.jump_target}"


class NumberOperand:
    def __init__(self, number):
        self.number = number


class VmForthAssembler(Interpreter):
    def __init__(self):
        self.constants = {}
        self.macros = {}
        self.labels = {}
        self.jumps = []

        self.previous_word_start = 0x0
        self.binary_code = b""

    def _append_uint32(self, number):
        self.binary_code += struct.pack("<I", number)

    def _get_uint32_at(self, address):
        binary_code = self.binary_code[address:address+4]
        return struct.unpack("<I", binary_code)[0]

    def _get_cfa_from_word(self, word):
        word_len = len(word)
        current_lfa = self.previous_word_start
        while current_lfa != 0x0:
            if self.binary_code[current_lfa+4] == word_len:
                word_start = current_lfa+5
                current_word = self.binary_code[word_start:word_start+word_len].decode("utf-8")
                if current_word == word:
                    return current_lfa + 4 + 1 + word_len
            current_lfa = self._get_uint32_at(current_lfa)
        return 0x0

    def start(self, tree):
        self.visit_children(tree)

        new_code = b""
        old_code = self.binary_code
        start_of_jump = old_code.find(LABEL_MARKER)
        while start_of_jump >= 0:
            new_code += old_code[:start_of_jump]
            jmp_index = struct.unpack("<H", old_code[start_of_jump+2:start_of_jump+4])[0]
            jump_target = self.jumps[jmp_index]
            new_code += struct.pack("<I", self.labels[jump_target])
            old_code = old_code[start_of_jump+4:]
            start_of_jump = old_code.find(LABEL_MARKER)
        new_code += old_code
        self.binary_code = new_code

    def code_definition(self, tree):
        current_position = len(self.binary_code)
        # Append back-link
        self._append_uint32(self.previous_word_start)
        self.previous_word_start = current_position

        # Append length and word text
        word_name = str(tree.children[0])
        self.binary_code += struct.pack("B", len(word_name))
        self.binary_code += bytes(word_name, encoding="utf-8")

        # creating a label for the word
        label_text = word_name.lower() + "_cfa"
        self.labels[label_text] = len(self.binary_code)

        # Append CFA field which is just the current address +4 for code words
        if "__DEFCODE_CFA" in self.macros:
            for child in self.macros["__DEFCODE_CFA"]:
                self.visit(child)

        self.visit_children(tree)

    def word_definition(self, tree):
        current_position = len(self.binary_code)
        # Append back-link
        self._append_uint32(self.previous_word_start)
        self.previous_word_start = current_position

        # Append length and word text
        word_name = str(tree.children[0])
        self.binary_code += struct.pack("B", len(word_name))
        self.binary_code += bytes(word_name, encoding="utf-8")

        # Append CFA field which is just the current address +4 for code words
        if "__DEFWORD_CFA" in self.macros:
            for child in self.macros["__DEFWORD_CFA"]:
                self.visit(child)

        self.visit_children(tree)

    def macro_definition(self, tree):
        macro_name = str(tree.children[0])
        self.macros[macro_name] = tree.children[1:]  # macro_code

    def constant_definition(self, tree):
        constant_name = str(tree.children[0])
        constant_value = self.visit(tree.children[1])
        self.constants[constant_name] = constant_value

    def code_line(self, tree):
        return self.visit_children(tree)[0]

    def instruction(self, tree):
        mnemonic = str(tree.children[0])
        suffix = "w"
        if tree.children[1] is not None:
            if isinstance(tree.children[1], Token):
                suffix = str(tree.children[1])
                parameters = [self.visit(child) for child in tree.children[2:]][0]
            else:
                parameters = [self.visit(child) for child in tree.children[1:]][0]
        else:
            parameters = []
        if mnemonic == "dw":
            if isinstance(parameters[0], JumpOperand):
                next_jumps_index = len(self.jumps)
                self.jumps.append(parameters[0].jump_target)
                bytecode = LABEL_MARKER + struct.pack("<H", next_jumps_index)
            else:
                bytecode = struct.pack("<I", parameters[0].number)
        elif mnemonic == "ifkt":
            bytecode = struct.pack("B", IFTK)
            bytecode += struct.pack("<H", parameters[0].number)
        elif mnemonic == "jmp":
            operand = parameters[0]
            if isinstance(operand, JumpOperand):
                next_jumps_index = len(self.jumps)
                self.jumps.append(operand.jump_target)
                bytecode = b"\x64" + LABEL_MARKER + struct.pack("<H", next_jumps_index)
            elif operand.name == "ip":
                bytecode = struct.pack("B", JMPI_IP)
            elif operand.name == "wp":
                bytecode = struct.pack("B", JMPI_WP)
            elif operand.name == "acc1":
                bytecode = struct.pack("B", JMPI_ACC1)
            elif operand.name == "acc2":
                bytecode = struct.pack("B", JMPI_ACC2)
        elif mnemonic == "jz":
            operand = parameters[0]
            next_jumps_index = len(self.jumps)
            self.jumps.append(operand.jump_target)
            bytecode = b"\x65" + LABEL_MARKER + struct.pack("<H", next_jumps_index)
        elif mnemonic == "mov":
            operand = 0x0
            target_param = parameters[0]
            source_param = parameters[1]

            if isinstance(source_param, JumpOperand):
                if target_param.name != "acc1":
                    raise ValueError(f"label can only be moved to acc1 on line {tree.children[0].line}")
                next_jumps_index = len(self.jumps)
                self.jumps.append(source_param.jump_target)
                bytecode = struct.pack("<B2sH", MOVI_ACC1, LABEL_MARKER, next_jumps_index)
            elif target_param.is_("increment") or target_param.is_("decrement") or \
                source_param.is_("increment") or source_param.is_("decrement"):
                if target_param.is_indirect:
                    if source_param.is_indirect:
                        raise ValueError(f"only one argument can be register indirect for movs on line {tree.children[0].line}")
                    opcode = MOVS_ID_W
                    if target_param.is_("decrement"):
                        operand |= 0x80
                    if target_param.is_("prefix"):
                        operand |= 0x40
                else:
                    opcode = MOVS_DI_W
                    if source_param.is_("decrement"):
                        operand |= 0x80
                    if source_param.is_("prefix"):
                        operand |= 0x40
                operand |= (target_param.encoding << 3)
                operand |= source_param.encoding
                bytecode = struct.pack("BB", opcode, operand)
            else:
                if suffix == "b":
                    opcode = MOVR_B
                else:
                    opcode = MOVR_W
                indirect_target = 0x0
                indirect_source = 0x0
                if target_param.is_indirect:
                    indirect_target = 0x8
                if source_param.is_indirect:
                    indirect_source = 0x8
                bytecode = struct.pack("BB", opcode,
                    (source_param.encoding | indirect_source) | (target_param.encoding | indirect_target) << 4)
        elif mnemonic == "nop":
            bytecode = struct.pack("B", NOP)
        elif mnemonic == "illegal":
            bytecode = struct.pack("B", ILLEGAL)
        else:
            raise ValueError(f"Opcode '{mnemonic}' currently not implemented on line {tree.children[0].line}")

        self.binary_code += bytecode

    def macro_call(self, tree):
        macro_name = str(tree.children[0])
        if not macro_name in self.macros:
            raise ValueError(f"Undefined Macro: '{macro_name}' on line {tree.children[0].line}")
        for child in self.macros[macro_name]:
            self.visit(child)

    def paramlist(self, tree):
        return [ self.visit(child) for child in tree.children ]

    def param(self, tree):
        return self.visit(tree.children[0])

    def register(self, tree):
        return RegisterOperand(str(tree.children[0]))

    def register_indirect(self, tree):
        return self.visit(tree.children[0])

    def register_plain_indirect(self, tree):
        return RegisterOperand(str(tree.children[0]), "indirect")

    def register_indirect_prefix(self, tree):
        operation = "increment"
        if self.visit(tree.children[0]) == "--":
            operation = "decrement"
        return RegisterOperand(str(tree.children[1]), "indirect", "prefix", operation)

    def register_indirect_postfix(self, tree):
        operation = "increment"
        if self.visit(tree.children[1]) == "--":
            operation = "decrement"
        return RegisterOperand(str(tree.children[0]), "indirect", "postfix", operation)

    def immediate_number(self, tree):
        number_node = tree.children[0]
        if isinstance(number_node, Token):
            number = self.constants[str(number_node)]
            return NumberOperand(number)
        else:
            return NumberOperand(self.visit(number_node))

    def label(self, tree):
        label_text = str(tree.children[0])
        self.labels[label_text] = len(self.binary_code)

    def word(self, tree):
        word = str(tree.children[0])
        cfa = self._get_cfa_from_word(word)
        if cfa==0 and not word.endswith(":") and not word.startswith(":"):
            raise ValueError(f"Word '{word}' not found in current dictionary on line {tree.children[0].line}")
        if word.endswith(":"):
            label_text = word[:-1]
            self.labels[label_text] = len(self.binary_code)
        elif word.startswith(":"):
            label_text = word[1:]
            next_jumps_index = len(self.jumps)
            self.jumps.append(label_text)
            self.binary_code += LABEL_MARKER + struct.pack("<H", next_jumps_index)
        else:
            self._append_uint32(cfa)

    def jump_target(self, tree):
        return JumpOperand(tree.children[0])

    def current_address_expression(self, tree):
        value = self.visit(tree.children[0])
        expression_rest = tree.children[1:]
        for operator, value_node in zip(expression_rest[::2], expression_rest[1::2]):
            operand = self.visit(value_node)
            if str(operator)=="+":
                value.number += operand
            else:
                value.number -= operand
        return value

    def current_address(self, tree):
        return NumberOperand(len(self.binary_code))

    def decrement_increment(self, tree):
        return str(tree.children[0])

    def number(self, tree):
        number_text = tree.children[0]
        if number_text.startswith("0x"):
            return int(number_text[2:], 16)
        else:
            return int(number_text)


def assemble(input_text):
    script_dir = pathlib.Path(__file__).parent
    lark_grammar_path = script_dir / "grammar.lark"
    grammar = lark_grammar_path.read_text()
    lark_parser = Lark(grammar, parser='lalr')

    parse_tree = lark_parser.parse(input_text)

    assembler = VmForthAssembler()
    assembler.visit(parse_tree)
    return assembler.binary_code
