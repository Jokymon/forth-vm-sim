import pathlib
import pytest
from lark import Lark


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
        defcode TEST_CODE
        end
        """
        parser.parse(source)

    def test_defcode_can_be_word_definitions_with_special_characters(self, parser):
        source = """
        defcode @!#HELLO
        end
        """
        parser.parse(source)


class TestWordBlocks:
    def test_defword(self, parser):
        source = """
        defword TEST_WORD
        end
        """
        parser.parse(source)

    def test_defword_can_be_word_definitions_with_special_characters(self, parser):
        source = """
        defword @!#HELLO
        end
        """
        parser.parse(source)



def test_empty_macro(parser):
    source = """
    macro TEST_MACRO
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


def test_macro_with_instructions(parser):
    source = """
    macro TEST_MACRO
        nop
        nop
    end
    """
    parser.parse(source)


def test_calling_a_macro(parser):
    source = """
    macro TEST_MACRO
        nop
        nop
    end

    codeblock
        TEST_MACRO()
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


class TestParsingDataDefinitions:
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


class TestParsingLaabels:
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
