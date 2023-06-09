import sys
sys.path.append("fbuilder")

from assembler import *
from app import Assembler
import keyboard
import time

from dataclasses import dataclass
import os
import subprocess
import tempfile


def passmein(func):
    def wrapper(*args, **kwargs):
        return func(func, *args, **kwargs)
    return wrapper


def assemble(source):
    @dataclass
    class DefaultOptions:
        format : str = "bin"
    asm = Assembler(DefaultOptions())
    return asm.assemble_source(source)


def build_vm_image(word_under_test, test_data):
    with open("eforth/test_word.fvs", "r") as source_file:
        source = source_file.read()

        source = source.replace("%WUT%", word_under_test)
        test_data_source = "\n".join(map(lambda x: "db #"+str(hex(x)), test_data))
        source = source.replace("%TEST_DATA%", test_data_source)
    
        binary = assemble(source)
    tmp = tempfile.NamedTemporaryFile(suffix=".bin", delete=False)
    tmp.write(binary)
    tmp.close()
    return tmp


def get_stack(text_output):
    lines = text_output.split(b"\r")
    stack = []
    for line in lines:
        try:
            stack.append(int(line, 16))
        except ValueError:
            pass    # ignore lines without parsable numbers
    return stack


def run_vm_image(word_under_test, input_data=None, test_data=[]):
    image = build_vm_image(word_under_test, test_data)
    with subprocess.Popen(["build-debug/forth-vm-sim", "-i",
                          image.name],
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE) as proc:
        if input_data:
            for ch in input_data:
                if ch=="\n":
                    keyboard.press_and_release('enter')
                else:
                    keyboard.press_and_release(ch)
                time.sleep(0.00001)
        output = proc.stdout.read()
    os.remove(image.name)
    return get_stack(output)

# ---------------------------------------------

@passmein
def test_infrastructure_for_test_data(me):
    """PRE_INIT_DATA DUP C@ SWAP doLIT 1 + C@"""
    test_data = [0x53, 0xa6]
    stack = run_vm_image(me.__doc__, test_data=test_data)

    assert len(stack) == 2
    assert stack[0] == 0xa6
    assert stack[1] == 0x53

# ---------------------------------------------

@passmein
def test_doLIT_pushes_value_on_the_stack(me):
    """doLIT 42"""
    stack = run_vm_image(me.__doc__)
    assert stack[0] == 42


# -----------------------------------------------------
# kernel words

@passmein
def test_next_decrements_until_below_zero(me):
    """doLIT 3 >R
begin:
    R@
    next :begin
    """
    stack = run_vm_image(me.__doc__)
    assert len(stack) == 4
    assert stack[0] == 0
    assert stack[1] == 1
    assert stack[2] == 2
    assert stack[3] == 3


@passmein
def test_when_next_finishes_data_stack_is_empty(me):
    """doLIT 3 >R
begin:
    next :begin
    """
    stack = run_vm_image(me.__doc__)
    assert len(stack) == 0


@passmein
def test_when_next_finishes_return_stack_only_contains_one_return_address(me):
    """doLIT 3 >R
begin:
    next :begin

    RP@ RP0 @ -
    """
    stack = run_vm_image(me.__doc__)
    assert len(stack) == 1
    assert stack[0] == 4

# -----------------------------------------------------
# memory fetch & store

@passmein
def test_c_at_gets_value_at_address(me):
    """doLIT 0x12345678 doLIT 0x7000 !
    doLIT 0x7000 C@
    """
    stack = run_vm_image(me.__doc__)
    assert len(stack) == 1
    assert stack[0] == 0x78


@passmein
def test_subtract_is_second_minus_first_stack(me):
    """doLIT 250 doLIT 22 -"""
    stack = run_vm_image(me.__doc__)
    assert stack[0] == 250-22


@passmein
def test_lt_zero_returns_true_for_negative_numbers(me):
    """doLIT 0 doLIT 1 - 0<"""
    stack = run_vm_image(me.__doc__)
    assert stack[0] == 0xffffffff

# ------------------------
# data stack

@passmein
def test_qdup_duplicates_non_zero(me):
    """doLIT 32 ?DUP"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[0] == 32
    assert stack[1] == 32


@passmein
def test_qdup_returns_0_on_0(me):
    """doLIT 0 ?DUP"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0


# ------------------------
# Arithmetic
@passmein
def test_umplus_pushes_one_for_carry(me):
    """doLIT 2290649224 doLIT 2290649224 UM+"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[0] == 1
    assert stack[1] == 286331152


@passmein
def test_umplus_pushes_zero_for_no_carry(me):
    """doLIT 4 doLIT 5 UM+"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[0] == 0
    assert stack[1] == 9


class TestNegate:
    def test_negate_turns_positive_into_negative(self):
        stack = run_vm_image("doLIT 23522 NEGATE")

        assert len(stack) == 1
        assert stack[0] == 2**32 - 23522

    def test_negate_turns_negative_into_positive(self):
        stack = run_vm_image("doLIT -23522 NEGATE")

        assert len(stack) == 1
        assert stack[0] == 23522

    def test_negate_keep_0(self):
        stack = run_vm_image("doLIT 0 NEGATE")

        assert len(stack) == 1
        assert stack[0] == 0

    def test_dnegate_turns_double_negative_to_positiv(self):
        stack = run_vm_image("doLIT 123456 doLIT 3 DNEGATE")

        assert len(stack) == 2
        assert stack[0] == 4294967292
        assert stack[1] == 4294843840


# ------------------------
# User variables

@passmein
def test_sp0_returns_data_stack_base_address(me):
    """SP0 @"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0x5000

@passmein
def test_rp0_returns_return_stack_base_address(me):
    """RP0 @"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0x6000

# ------------------------
# Comparison


@passmein
def test_eq_returns_0_on_different_values(me):
    """doLIT 5 doLIT 123 ="""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0

@passmein
def test_eq_returns_minus_one_on_same_values(me):
    """doLIT 25 doLIT 25 ="""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0xffffffff


# See https://forth-standard.org/standard/core/Uless
@passmein
def test_u_lt_test1(me):
    """doLIT 0 doLIT 1 U<"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0xffffffff

@passmein
def test_u_lt_test2(me):
    """doLIT 1 doLIT 1 U<"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0x0

@passmein
def test_u_lt_test3(me):
    """doLIT 2 doLIT 1 U<"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0x0

# See https://forth-standard.org/standard/core/WITHIN

@passmein
def test_within_test1(me):
    """doLIT 40 doLIT 10 doLIT 200 WITHIN"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0xffffffff


# ------------------------
# Memory access
@passmein
def test_count_turns_counted_string_to_address_and_count(me):
    """PRE_INIT_DATA DUP
    COUNT
    """
    stack = run_vm_image(me.__doc__, test_data=[0x3, 0x6f, 0x6b, 0x2e])

    assert len(stack) == 3
    pre_init_address = stack[2]
    assert stack[0] == 3
    assert stack[1] == pre_init_address + 1


@passmein
def test_tib_returns_the_address_to_tib(me):
    """TIB"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0x3000


@passmein
def test_cmove_non_overlapping(me):
    """PRE_INIT_DATA doLIT 28500 doLIT 3 CMOVE
    doLIT 28500 C@
    doLIT 28501 C@
    doLIT 28502 C@
    """
    stack = run_vm_image(me.__doc__, test_data=[0x34, 0x53, 0xd8])
    assert len(stack) == 3
    assert stack[0] == 0xd8
    assert stack[1] == 0x53
    assert stack[2] == 0x34


# ------------------------
# Basic I/O
@passmein
def test_stringQuoteBar_leaves_string_address_on_stack(me):
    """STRING_ADDRESS_TEST
    """
    stack = run_vm_image(me.__doc__)
    assert len(stack) == 2
    assert stack[0] == stack[1]


# ------------------------
# parse
# In these tests, we always put PRE_INIT_DATA at the
# bottom of the stack to have a reference
# Next we expect the values
#   - b: start address of the parsed text
#   - u: length of the parsed text
#   - d: difference between the original start address
#        and the location for the next parsing start address

@passmein
def test_parse_finds_one_space_delimited_word(me):
    """PRE_INIT_DATA PRE_INIT_DATA doLIT 80 BL parse"""
    parse_input = "  word "
    stack = run_vm_image(me.__doc__, test_data=list(map(ord, parse_input)))

    assert len(stack) == 4
    pre_init_address = stack[3]
    assert stack[2] == pre_init_address + 2
    assert stack[1] == 4
    assert stack[0] == 7


@passmein
def test_parse_finds_one_space_delimited_word_from_multiple(me):
    """PRE_INIT_DATA PRE_INIT_DATA doLIT 80 BL parse"""
    parse_input = "   oneword   nextword  "
    stack = run_vm_image(me.__doc__, test_data=list(map(ord, parse_input)))

    assert len(stack) == 4
    pre_init_address = stack[3]
    assert stack[2] == pre_init_address + 3
    assert stack[1] == 7
    assert stack[0] == 11


@passmein
def test_parse_finds_text_delimited_by_bracket(me):
    # doLIT 41 == ord(')')
    """PRE_INIT_DATA PRE_INIT_DATA doLIT 80 doLIT 41 parse"""
    parse_input = "  comment text)"
    stack = run_vm_image(me.__doc__, test_data=list(map(ord, parse_input)))

    assert len(stack) == 4
    pre_init_address = stack[3]
    assert stack[2] == pre_init_address
    assert stack[1] == 14
    assert stack[0] == 15


# ------------------------
# accept

@passmein
def test_expect_returns_the_address_and_the_amount_of_read_chars(me):
    """doLIT 12000 doLIT 80 accept"""
    stack = run_vm_image(me.__doc__, "hello\n")

    assert len(stack) == 2
    assert stack[0] == 5
    assert stack[1] == 12000

# ------------------------
# QUERY

@passmein
def test_QUERY_stores_number_of_read_characters_and_resets_parser_pointer(me):
    """QUERY #TIB @ >IN @"""
    stack = run_vm_image(me.__doc__, "hello\n")

    assert len(stack) == 2
    assert stack[0] == 0
    assert stack[1] == 5
