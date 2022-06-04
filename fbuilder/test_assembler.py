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