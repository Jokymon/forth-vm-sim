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

# ------------------------
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
# EXPECT

@passmein
def test_expect_returns_the_address_and_the_amount_of_read_chars(me):
    """doLIT 12000 doLIT 80 EXPECT"""
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
