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


def test_defcode(parser):
    source = """
    defcode TEST_CODE
    end
    """
    parser.parse(source)


def test_defword(parser):
    source = """
    defword TEST_WORD
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
        $TEST_MACRO()
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


class TestParsingMovrInstructions:
    def test_moving_between_instructions(self, parser):
        source = """
        codeblock
            movr %wp, %acc1
        end
        """
        parser.parse(source)


class TestParsingMovsInstructions:
    def test_moving_between_instructions(self, parser):
        source = """
        codeblock
            movs [%wp++], %acc1
            movs [--%ip], %acc2
            movs %acc1, [--%ip]
            movs %acc2, [%rsp++]
        end
        """
        parser.parse(source)
