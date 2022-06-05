from assembler import *
import pathlib
import pytest
from lark import Lark


def test_alignment_function():
    assert aligned(1, 4) == 4
    assert aligned(4, 4) == 4
    assert aligned(13, 4) == 16
    assert aligned(43, 16) == 48


@pytest.fixture
def assembler():
    script_dir = pathlib.Path(__file__).parent
    lark_grammar_path = script_dir / "grammar.lark"

    grammar = lark_grammar_path.read_text()
    return Lark(grammar, parser='lalr', transformer=VmForthAssembler())


def test_hexadecimal_number_is_correctly_parsed(assembler):
    source = """
    codeblock
        ifkt #0x1234
    end
    """

    binary = b"\xfe\x34\x12"

    assert binary == assembler.parse(source)


def test_constant_is_replaced_in_parameters(assembler):
    source = """
    const IFKT_VALUE = 0x1234
    codeblock
        ifkt IFKT_VALUE
    end
    """

    binary = b"\xfe\x34\x12"

    assert binary == assembler.parse(source)


def test_ifkt_is_translated_with_16bit_argument(assembler):
    source = """
    codeblock
        ifkt #1234
        ifkt #32152
    end
    """

    binary = b"\xfe\xd2\x04\xfe\x98\x7d"

    assert binary == assembler.parse(source)


def test_calling_macros_inserts_the_code(assembler):
    source = """
    macro TEST
        illegal
    end

    codeblock
        $TEST()
    end
    """

    binary = b"\xff"    # online contains the 'illegal' instruction once

    assert binary == assembler.parse(source)


def test_trying_to_call_undefined_macro_raises_exception(assembler):
    source = """
    codeblock
        $MISSING_MACRO()
    end
    """

    with pytest.raises(ValueError) as parsing_error:
        assembler.parse(source)
    assert "on line 3" in str(parsing_error)


class TestAssemblingMovrInstructions:
    def test_moving_between_instructions(self, assembler):
        source = """
        codeblock
            movr %wp, %acc1
            movr %rsp, %acc2
            movr [%dsp], %ip
            movr %wp, [%acc1]
            movr [%acc1], [%acc2]
        end
        """

        binary = b"\x21\x14"
        binary += b"\x21\x25"
        binary += b"\x21\xb0"
        binary += b"\x21\x1c"
        binary += b"\x21\xcd"

        assert binary == assembler.parse(source)
