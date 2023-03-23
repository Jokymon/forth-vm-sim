import pathlib

from operands import *
from emitter import *
from lark import Token
from lark.visitors import Interpreter


def aligned(address, alignment):
    return (address + alignment - 1) // alignment * alignment


class MacroDefinition:
    def __init__(self, parameters, nodes):
        self.parameters = parameters
        self.nodes = nodes

    def evaluate(self, assembler):
        for node in self.nodes:
            assembler.visit(node)


class VmForthAssembler(Interpreter):
    def __init__(self, emitter, symbol_table):
        self.constants = {}
        self.macros = {}
        self.macro_scope = {}

        self.word_addresses = {}
        self.previous_word_start = 0x0

        self.emitter = emitter
        self.symbol_table = symbol_table

    def _get_cfa_from_word(self, word):
        if word in self.word_addresses:
            return self.word_addresses[word]
        else:
            return 0x0

    def start(self, tree):
        self.visit_children(tree)

        self.emitter.finalize()

    def assembly_definition(self, tree):
        custom_def = tree.children[0]

        current_position = self.emitter.get_current_code_address()
        # Append back-link
        self.emitter.emit_data_32(self.previous_word_start)
        self.previous_word_start = current_position

        # Append length and word text
        word_name = str(tree.children[1])
        self.emitter.emit_data_8(len(word_name))
        self.emitter.emit_data_string(word_name)

        # creating a label for the word
        self.emitter.mark_label(word_name.lower() + "_cfa")
        self.word_addresses[word_name] = self.emitter.get_current_code_address()

        # Append CFA field which is just the current address +4 for code words
        custom_type_macro = f"__DEF{custom_def.upper()}_CFA"
        if custom_type_macro in self.macros:
             self.macros[custom_type_macro].evaluate(self)

        self.visit_children(tree)

        # creating a label for address after word
        self.emitter.mark_label(word_name.lower() + "_end")

        # add symbol to symbol table
        self.symbol_table.add_word(word_name.lower(), current_position, self.emitter.get_current_code_address())

    def general_word_definition(self, tree):
        custom_def = tree.children[0]

        current_position = self.emitter.get_current_code_address()
        # Append back-link
        self.emitter.emit_data_32(self.previous_word_start)
        self.previous_word_start = current_position

        # Append length and word text
        word_name = str(tree.children[1])
        self.emitter.emit_data_8(len(word_name))
        self.emitter.emit_data_string(word_name)

        # creating a label for the word
        self.emitter.mark_label(word_name.lower() + "_cfa")
        self.word_addresses[word_name] = self.emitter.get_current_code_address()

        # Append CFA field which is just the current address +4 for code words
        custom_type_macro = f"__DEF{custom_def.upper()}_CFA"
        if custom_type_macro in self.macros:
             self.macros[custom_type_macro].evaluate(self)

        self.visit_children(tree)

        # creating a label for address after word
        self.emitter.mark_label(word_name.lower() + "_end")

        # add symbol to symbol table
        self.symbol_table.add_word(word_name.lower(), current_position, self.emitter.get_current_code_address())

    def macro_definition(self, tree):
        macro_name = str(tree.children[0])
        arguments = list(map(str, filter(lambda x: x is not None, tree.children[1].children)))
        macro_code = tree.children[2:]
        self.macros[macro_name] = MacroDefinition(arguments, macro_code)

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

        # creating a label for the word
        self.emitter.mark_label(variable_name.lower() + "_cfa")
        self.word_addresses[variable_name] = self.emitter.get_current_code_address()

        # Append CFA field
        if "__DEFVAR_CFA" in self.macros:
            self.macros["__DEFVAR_CFA"].evaluate(self)

        # create a label for the variable value
        self.emitter.mark_label(variable_name.lower() + "_var")

        # Append a default value
        default_value = 0x0
        if len(tree.children) > 1:
            default_value = self.visit(tree.children[1])
        self.emitter.emit_data_32(default_value)

        # creating a label for address after word
        self.emitter.mark_label(variable_name.lower() + "_end")

        # add symbol to symbol table
        self.symbol_table.add_word(variable_name.lower(), current_position, self.emitter.get_current_code_address())

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
        elif mnemonic == "call":
            self.emitter.emit_call(parameters[0])
        elif mnemonic == "sub":
            self.emitter.emit_sub(parameters[0], parameters[1], parameters[2])
        elif mnemonic == "xor":
            self.emitter.emit_xor(parameters[0], parameters[1], parameters[2])
        elif mnemonic == "sra":
            self.emitter.emit_sra(parameters[0], parameters[1])
        elif mnemonic == "db":
            if parameters[0].number > 0xff:
                raise ValueError(f"constant 0x{parameters[0].number:x} is too big for db on line {tree.children[0].line}")
            self.emitter.emit_data_8(parameters[0])
        elif mnemonic == "dw":
            self.emitter.emit_data_32(parameters[0])
        elif mnemonic == "ifkt":
            self.emitter.emit_ifkt(parameters[0])
        elif mnemonic == "jc":
            self.emitter.emit_conditional_jump(JMP_COND_CARRY, parameters[0])
        elif mnemonic == "jmp":
            self.emitter.emit_jump(parameters[0])
        elif mnemonic == "jz":
            self.emitter.emit_conditional_jump(JMP_COND_ZERO, parameters[0])
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
        parameter_len = len(self.macros[macro_name].parameters)
        argument_len = 0
        if tree.children[1] is not None:
            parameters = self.macros[macro_name].parameters
            arguments = tree.children[1].children
            argument_len = len(arguments)
            self.macro_scope = dict(zip(parameters, arguments))
        if parameter_len != argument_len:
            raise ValueError(f"Calling macro with {argument_len} parameter where {parameter_len} are expected on line {tree.children[0].line}")
        self.macros[macro_name].evaluate(self)
        self.macro_scope = {}

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
        if cfa==0:
            if word.endswith(":"):
                self.emitter.mark_label(word[:-1])
            elif word.startswith(":"):
                self.emitter.emit_label_target(word[1:])
            elif word.startswith("#0x"):
                self.emitter.emit_data_32(int(word[3:], 16))
            elif word.startswith("0x"):
                self.emitter.emit_data_32(int(word[2:], 16))
            elif word.isnumeric():
                self.emitter.emit_data_32(int(word))
            else:
                raise ValueError(f"Word '{word}' not found in current dictionary on line {tree.children[0].line}")
        else:
            self.emitter.emit_data_32(cfa)

    def jump_target(self, tree):
        return JumpOperand(tree.children[0])
    
    def expression(self, tree):
        def local_visit(node):
            """Only visit non-token nodes and just return the tokens"""
            if isinstance(node, Token):
                return node
            else:
                return self.visit(node)
        elements = [local_visit(node) for node in tree.children]

        if all(isinstance(element, Operand) and element.is_constant() for element in elements):
            value = self.visit(tree.children[0])
            expression_rest = tree.children[1:]
            for operator, value_node in zip(expression_rest[::2], expression_rest[1::2]):
                operand = self.visit(value_node)
                if str(operator)=="+":
                    value.number += operand.number
                else:
                    value.number -= operand.number
            return value
        else:
            return ExpressionOperand(elements)
    
    def term(self, tree):
        return self.visit(tree.children[0])

    def macro_parameter(self, tree):
        parameter_name = str(tree.children[0])
        if not parameter_name in self.macro_scope:
            raise ValueError(f"Unknown macro argument '{parameter_name}' on line {tree.children[0].line}")
        return self.visit(self.macro_scope[parameter_name])

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