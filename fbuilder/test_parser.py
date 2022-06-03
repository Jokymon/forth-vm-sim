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


def test_macro_with_instructions(parser):
    source = """
    macro TEST_MACRO
        opcode
        opcode
    end
    """
    parser.parse(source)


def test_calling_a_macro(parser):
    source = """
    macro TEST_MACRO
        opcode
        opcode
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
        some_op_code // comment on opcode line
    end // comment on block end
    """