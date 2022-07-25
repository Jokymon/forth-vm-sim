import pathlib

from operands import *
from emitter import *
from lark import Lark, Token, Transformer
from lark.visitors import Interpreter


def aligned(address, alignment):
    return (address + alignment - 1) // alignment * alignment


class VmForthAssembler(Interpreter):
    def __init__(self, emitter):
        self.constants = {}
        self.macros = {}

        self.word_addresses = {}
        self.previous_word_start = 0x0

        self.emitter = emitter

    def _get_cfa_from_word(self, word):
        if word in self.word_addresses:
            return self.word_addresses[word]
        else:
            return 0x0

    def start(self, tree):
        self.visit_children(tree)

        self.emitter.finalize()

    def code_definition(self, tree):
        current_position = self.emitter.get_current_code_address()
        # Append back-link
        self.emitter.emit_data_32(self.previous_word_start)
        self.previous_word_start = current_position

        # Append length and word text
        word_name = str(tree.children[0])
        self.emitter.emit_data_8(len(word_name))
        self.emitter.emit_data_string(word_name)

        # creating a label for the word
        self.emitter.mark_label(word_name.lower() + "_cfa")
        self.word_addresses[word_name] = self.emitter.get_current_code_address()

        # Append CFA field which is just the current address +4 for code words
        if "__DEFCODE_CFA" in self.macros:
            for child in self.macros["__DEFCODE_CFA"]:
                self.visit(child)

        self.visit_children(tree)

        # creating a label for address after word
        self.emitter.mark_label(word_name.lower() + "_end")
        self.word_addresses[word_name] = self.emitter.get_current_code_address()

    def word_definition(self, tree):
        current_position = self.emitter.get_current_code_address()
        # Append back-link
        self.emitter.emit_data_32(self.previous_word_start)
        self.previous_word_start = current_position

        # Append length and word text
        word_name = str(tree.children[0])
        self.emitter.emit_data_8(len(word_name))
        self.emitter.emit_data_string(word_name)

        # creating a label for the word
        self.emitter.mark_label(word_name.lower() + "_cfa")
        self.word_addresses[word_name] = self.emitter.get_current_code_address()

        # Append CFA field which is just the current address +4 for code words
        if "__DEFWORD_CFA" in self.macros:
            for child in self.macros["__DEFWORD_CFA"]:
                self.visit(child)

        self.visit_children(tree)

        # creating a label for address after word
        self.emitter.mark_label(word_name.lower() + "_end")
        self.word_addresses[word_name] = self.emitter.get_current_code_address()

    def macro_definition(self, tree):
        macro_name = str(tree.children[0])
        self.macros[macro_name] = tree.children[1:]  # macro_code

    def constant_definition(self, tree):
        constant_name = str(tree.children[0])
        constant_value = self.visit(tree.children[1])
        self.constants[constant_name] = constant_value

    def system_variable_definition(self, tree):
        current_position = self.emitter.get_current_code_address()
        # Append back-link
        self.emitter.emit_data_32(self.previous_word_start)
        self.previous_word_start = current_position

        # Append length and word text
        variable_name = str(tree.children[0])
        self.emitter.emit_data_8(len(variable_name))
        self.emitter.emit_data_string(variable_name)

        # Append CFA field
        if "__DEFVAR_CFA" in self.macros:
            for child in self.macros["__DEFVAR_CFA"]:
                self.visit(child)

        # create a label for the variable value
        self.emitter.mark_label(variable_name.lower() + "_var")
        # Append a default value
        default_value = 0x0
        if len(tree.children) > 1:
            default_value = self.visit(tree.children[1])
        self.emitter.emit_data_32(default_value)

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
        if mnemonic == "add":
            self.emitter.emit_add(parameters[0], parameters[1], parameters[2])
        elif mnemonic == "dw":
            self.emitter.emit_data_32(parameters[0])
        elif mnemonic == "ifkt":
            self.emitter.emit_ifkt(parameters[0])
        elif mnemonic == "jmp":
            self.emitter.emit_jump(parameters[0])
        elif mnemonic == "jz":
            self.emitter.emit_conditional_jump(parameters[0])
        elif mnemonic == "mov":
            self.emitter.emit_mov(suffix, parameters[0], parameters[1])
        elif mnemonic == "nop":
            self.emitter.emit_nop()
        elif mnemonic == "illegal":
            self.emitter.emit_illegal()
        else:
            raise ValueError(f"Opcode '{mnemonic}' currently not implemented on line {tree.children[0].line}")

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
        return RegisterOperand(tree.children[0])

    def register_indirect(self, tree):
        return self.visit(tree.children[0])

    def register_plain_indirect(self, tree):
        return RegisterOperand(tree.children[0], "indirect")

    def register_indirect_prefix(self, tree):
        operation = "increment"
        if self.visit(tree.children[0]) == "--":
            operation = "decrement"
        return RegisterOperand(tree.children[1], "indirect", "prefix", operation)

    def register_indirect_postfix(self, tree):
        operation = "increment"
        if self.visit(tree.children[1]) == "--":
            operation = "decrement"
        return RegisterOperand(tree.children[0], "indirect", "postfix", operation)

    def immediate_number(self, tree):
        number_node = tree.children[0]
        if isinstance(number_node, Token):
            number = self.constants[str(number_node)]
            return NumberOperand(number)
        else:
            return NumberOperand(self.visit(number_node))

    def label(self, tree):
        self.emitter.mark_label(str(tree.children[0]))

    def word(self, tree):
        word = str(tree.children[0])
        cfa = self._get_cfa_from_word(word)
        if cfa==0 and not word.endswith(":") and not word.startswith(":"):
            raise ValueError(f"Word '{word}' not found in current dictionary on line {tree.children[0].line}")
        if word.endswith(":"):
            self.emitter.mark_label(word[:-1])
        elif word.startswith(":"):
            self.emitter.emit_label_target(word[1:])
        else:
            self.emitter.emit_data_32(cfa)

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
        return NumberOperand(self.emitter.get_current_code_address())

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

    assembler = VmForthAssembler(MachineCodeEmitter())
    assembler.visit(parse_tree)
    return assembler.emitter.binary_code


def assemble_with_diassassembly(input_text):
    script_dir = pathlib.Path(__file__).parent
    lark_grammar_path = script_dir / "grammar.lark"
    grammar = lark_grammar_path.read_text()
    lark_parser = Lark(grammar, parser='lalr')

    parse_tree = lark_parser.parse(input_text)

    assembler = VmForthAssembler(DisassemblyEmitter())
    assembler.visit(parse_tree)
    return assembler.emitter.disassembly
