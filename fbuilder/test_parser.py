import pathlib
import pytest
from lark import Lark
# I accept longer lines in tests because of hopefully better test names
# flake8: noqa: E501

@pytest.fixture
def parser():
    script_dir = pathlib.Path(__file__).parent
    lark_grammar_path = script_dir / "grammar.lark"

    grammar = lark_grammar_path.read_text()
    return Lark(grammar, parser='lalr')


def test_codeblock(parser):
    source = """
    codeblock
    end
    """
    parser.parse(source)


class TestCodeBlocks:
    def test_defcode(self, parser):
        source = """
        def asm(code) TEST_CODE
        end
        """
        parser.parse(source)

    def test_defcode_can_be_word_definitions_with_special_characters(self, parser):
        source = """
        def asm(code) @!#HELLO
        end
        """
        parser.parse(source)

    def test_defcode_can_have_alias_definition(self, parser):
        source = """
        def asm(code) alias WORD_ALIAS WORD
        end
        """
        parser.parse(source)

    def test_defcode_can_have_a_numeric_flag(self, parser):
        source = """
        def asm[0x80](code) AWORD
        end
        """
        parser.parse(source)

    def test_defcode_can_have_a_constant_flag(self, parser):
        source = """
        const IMMEDIATE = 0x80
        def asm[IMMEDIATE](code) AWORD
        end
        """
        parser.parse(source)

    def test_defcode_can_have_multiple_flags(self, parser):
        source = """
        def asm[0x80, 0x40](code) AWORD
        end
        """
        parser.parse(source)


class TestWordBlocks:
    def test_defword(self, parser):
        source = """
        def word(colon) TEST_WORD
        end
        """
        parser.parse(source)

    def test_defword_can_be_word_definitions_with_special_characters(self, parser):
        source = """
        def word(colon) @!#HELLO
        end
        """
        parser.parse(source)

    def test_defword_can_have_alias_definition(self, parser):
        source = """
        def word(colon) alias WORD_ALIAS WORD
        end
        """
        parser.parse(source)

    def test_defword_can_have_a_numeric_flag(self, parser):
        source = """
        def word[0x80](colon) AWORD
        end
        """
        parser.parse(source)

    def test_defword_can_have_a_constant_flag(self, parser):
        source = """
        const IMMEDIATE = 0x80
        def word[IMMEDIATE](colon) AWORD
        end
        """
        parser.parse(source)

    def test_defword_can_have_multiple_flags(self, parser):
        source = """
        def word[0x80, 0x40](colon) AWORD
        end
        """
        parser.parse(source)



class TestMacros:
    def test_empty_macro(self, parser):
        source = """
        macro TEST_MACRO()
        end
        """
        parser.parse(source)

    def test_macro_with_instructions(self, parser):
        source = """
        macro TEST_MACRO()
            nop
            nop
        end
        """
        parser.parse(source)

    def test_macro_with_register_argument(self, parser):
        source = """
        macro TEST_MACRO(reg)
            mov %acc1, @reg
        end
        """
        parser.parse(source)

    def test_macro_with_multiple_register_arguments(self, parser):
        source = """
        macro TEST_MACRO(reg1, reg2)
            mov %acc1, @reg1
            mov @reg2, %acc2
        end
        """
        parser.parse(source)

    def test_calling_a_macro(self, parser):
        source = """
        macro TEST_MACRO()
            nop
            nop
        end

        codeblock
            TEST_MACRO()
        end
        """
        parser.parse(source)

    def test_calling_a_macro_with_one_argument(self, parser):
        source = """
        macro TEST_MACRO(reg)
            mov %acc1, @reg
        end

        codeblock
            TEST_MACRO(%dsp)
        end
        """
        parser.parse(source)

    def test_calling_a_macro_with_two_arguments(self, parser):
        source = """
        macro TEST_MACRO(reg1, reg2)
            mov %acc1, @reg1
            mov @reg2, %acc2
        end

        codeblock
            TEST_MACRO(%dsp, %rsp)
        end
        """
        parser.parse(source)

    def test_macro_parameters_can_be_used_in_expressions(self, parser):
        source = """
        macro TEST_MACRO(label)
            dw @label - :base_label
        end

        codeblock
        base_label:
        label1:
            TEST_MACRO(:label1)
        end
        """
        parser.parse(source)


def test_constant_definition(parser):
    source = """
    const MY_VALUE = 23
    """
    parser.parse(source)


def test_opcodes_with_single_parameter(parser):
    source = """
    codeblock
        add %wp     // register
        add #234    // value - this is only syntax, semantics might be wrong
        add [%wp]   // register immediate - again with wrong semantics  
    end
    """
    parser.parse(source)


def test_mnemonics_are_prefered_over_identifiers_in_ambiguous_situations(parser):
    source = """
    codeblock
        ifkt #10
        add
        ifkt #12
    end
    """
    parser.parse(source)


def test_hexadecimal_notation_for_numbers_supported(parser):
    source = """
    codeblock
        add #0x234
    end
    """
    parser.parse(source)


def test_interpreter_interface_instruction(parser):
    source = """
    codeblock
        ifkt #34
    end
    """
    parser.parse(source)


def test_opcodes_with_two_parameter(parser):
    source = """
    codeblock
        add %wp, [%wp]
        add %ip, #4
    end
    """
    parser.parse(source)


def test_current_address_as_parameter(parser):
    source = """
    codeblock
        dw $
    end
    """
    parser.parse(source)


def test_simple_current_address_based_expression_as_parameter(parser):
    source = """
    codeblock
        dw $+4
    end
    """
    parser.parse(source)


def test_address_based_expression_as_parameter(parser):
    source = """
    codeblock
    label1:
    label2:
        dw :label2 - :label1
    end
    """
    parser.parse(source)


def test_comments(parser):
    source = """
    // comments on lines by themselves
    codeblock // comment on block start
        nop // comment on opcode line
    end // comment on block end
    """
    parser.parse(source)


class TestParsingOtherDefinitions:
    def test_definition_with_custom_name_works(self, parser):
        source = """
        def word(mytype) MY_WORD
        end
        """
        parser.parse(source)

    def test_definition_with_custom_name_can_contain_words(self, parser):
        source = """
        def word(mytype) MY_WORD
            DUP + DROP
        end
        """
        parser.parse(source)


class TestParsingDataDefinitions:
    def test_defining_immediate_8bit_value(self, parser):
        source = """
        codeblock
            db #0x12
        end
        """
        parser.parse(source)

    def test_defining_immediate_32bit_value(self, parser):
        source = """
        codeblock
            dw #0x12345678
        end
        """
        parser.parse(source)

    def test_defining_32bit_value_with_constant(self, parser):
        source = """
        const MY_VALUE = 23
        codeblock
            dw MY_VALUE
        end
        """
        parser.parse(source)

    def test_defining_32bit_value_with_label(self, parser):
        source = """
        codeblock
        mylabel:
            dw :mylabel
        end
        """
        parser.parse(source)

    def test_defining_bytes_with_strings(self, parser):
        source = """
        codeblock
            db "Hello"
        end
        """
        parser.parse(source)


class TestParsingMovInstructions:
    def test_moving_between_registers_instructions(self, parser):
        source = """
        codeblock
            mov %wp, %acc1
        end
        """
        parser.parse(source)


class TestParsingMovsInstructions:
    def test_moving_between_instructions(self, parser):
        source = """
        codeblock
            mov [%wp++], %acc1
            mov [--%ip], %acc2
            mov %acc1, [--%ip]
            mov %acc2, [%rsp++]
        end
        """
        parser.parse(source)


class TestParsingLabels:
    def test_labels_inside_codeblock(self, parser):
        source = """
        codeblock
            mov [%wp++], %acc1
            mov [--%ip], %acc2
        label1:
            mov %acc1, [--%ip]
            mov %acc2, [%rsp++]
        end
        """
        parser.parse(source)

    def test_jmp_to_targets(self, parser):
        source = """
        codeblock
            jmp :label1
            nop
        label1:
            nop
        end
        """
        parser.parse(source)

    def test_jump_if_zero_to_targets(self, parser):
        source = """
        codeblock
            jz :label1
            nop
        label1:
            nop
        end
        """
        parser.parse(source)

    def test_jump_if_carry_to_targets(self, parser):
        source = """
        codeblock
            jc :label1
            nop
        label1:
            nop
        end
        """
        parser.parse(source)