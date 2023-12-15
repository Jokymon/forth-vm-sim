from fbuilder.app import Assembler
import keyboard
import time

from dataclasses import dataclass
import json
import os
import subprocess
import tempfile


# Forth constants
TRUE = -1
FALSE = 0


def passmein(func):
    def wrapper(*args, **kwargs):
        return func(func, *args, **kwargs)
    return wrapper


def assemble(source):
    @dataclass
    class DefaultOptions:
        format: str = "bin"
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
    state = json.loads(lines[-2])
    stack = state["dataStack"]
    return stack


def run_vm_image(word_under_test, input_data=None, test_data=[]):
    image = build_vm_image(word_under_test, test_data)
    with subprocess.Popen(["build-debug/forth-vm-sim",
                           "--dump-state",
                           "-i", image.name],
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE) as proc:
        if input_data:
            for ch in input_data:
                if ch == "\n":
                    keyboard.press_and_release('enter')
                else:
                    keyboard.press_and_release(ch)
                time.sleep(0.00001)
        output = proc.stdout.read()
        if "Vm hit illegal instruction" in output.decode(encoding="utf-8"):
            raise RuntimeError("VM execution failed")
    os.remove(image.name)
    return get_stack(output)


# ---------------------------------------------
@passmein
def test_infrastructure_for_test_data(me):
    """PRE_INIT_DATA DUP C@ SWAP doLIT 1 + C@"""
    test_data = [0x53, 0xa6]
    stack = run_vm_image(me.__doc__, test_data=test_data)

    assert len(stack) == 2
    assert stack[1] == 0xa6
    assert stack[0] == 0x53


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
    assert stack[3] == 0
    assert stack[2] == 1
    assert stack[1] == 2
    assert stack[0] == 3


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
    assert stack[0] == -1


# ------------------------
# data stack
@passmein
def test_sp_at_returns_current_stack_pointer(me):
    # Fill stack with some elements so the pointer is != 0
    """doLIT 1 doLIT 2 doLIT 3 SP@"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 4
    assert stack[-1] == 3 * 0x4


@passmein
def test_sp_store_writes_new_sp_value_from_stack(me):
    """doLIT 52 SP!"""
    stack = run_vm_image(me.__doc__)

    # Use indirect observation of changes in the SP:
    # we store 13*4 in SP and expect the stack size to
    # be 13 4-byte words now
    assert len(stack) == 13


@passmein
def test_rot_rotates_third_element_to_tos(me):
    """doLIT 123 doLIT 4352 doLIT 6234 ROT"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 3
    assert stack[2] == 123
    assert stack[1] == 6234
    assert stack[0] == 4352


@passmein
def test_plus_adds_values_without_carry(me):
    """doLIT 2290649224 doLIT 2290649224 +"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 286331152


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
    assert stack[1] == 1
    assert stack[0] == 286331152


@passmein
def test_umplus_pushes_zero_for_no_carry(me):
    """doLIT 4 doLIT 5 UM+"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[1] == 0
    assert stack[0] == 9


@passmein
def test_abs_turns_negative_number_to_positive(me):
    """doLIT -542234 ABS"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 542234


class TestNegate:
    def test_negate_turns_positive_into_negative(self):
        stack = run_vm_image("doLIT 23522 NEGATE")

        assert len(stack) == 1
        assert stack[0] == -23522

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
        assert stack[1] == -4
        assert stack[0] == -123456


# ------------------------
# User variables

@passmein
def test_sp0_returns_data_stack_base_address(me):
    """SP0 @"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0x0


@passmein
def test_rp0_returns_return_stack_base_address(me):
    """RP0 @"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0x0


# ------------------------
# Comparison
@passmein
def test_equal_zero_returns_true_on_zero(me):
    """doLIT 0 0="""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == TRUE


@passmein
def test_equal_zero_returns_false_on_non_zero(me):
    """doLIT 134 0="""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == FALSE


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
    assert stack[0] == -1


# See https://forth-standard.org/standard/core/Uless
@passmein
def test_u_lt_test1(me):
    """doLIT 0 doLIT 1 U<"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == -1


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


# See https://forth-standard.org/standard/core/less
@passmein
def test_lt_test1(me):
    """doLIT 0 doLIT 1 <"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == -1


@passmein
def test_lt_test2(me):
    """doLIT -1 doLIT 0 <"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == -1


@passmein
def test_lt_test3(me):
    """doLIT 1 doLIT 0 <"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0


@passmein
def test_min_returns_smaller_of_two_numbers(me):
    """doLIT 2 doLIT 1 MIN"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 1


@passmein
def test_min_treats_negative_numbers_as_smaller_than_corresponding_positive_number(me):
    """doLIT -39 doLIT 50 MIN"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == -39


@passmein
def test_max_returns_larger_of_two_numbers(me):
    """doLIT 32 doLIT 1 MAX"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 32


# See https://forth-standard.org/standard/core/WITHIN
@passmein
def test_within_test1(me):
    """doLIT 40 doLIT 10 doLIT 200 WITHIN"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == -1


# ------------------------
# Divide

@passmein
def test_ummod_calculates_correctly(me):
    """doLIT 42 doLIT 0 doLIT 5 UM/MOD"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[1] == 8        # quotient
    assert stack[0] == 2        # reminder


# ------------------------
# Multiply
@passmein
def test_um_multiply_calculates_correctly(me):
    """doLIT 1234 doLIT 4567 UM*"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[1] == 0            # high word
    assert stack[0] == 1234*4567    # low word


@passmein
def test_um_multiply_calculates_correctly_with_overflow(me):
    """doLIT 4300000 doLIT 12000 UM*"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[1] == 0xc          # high word
    assert stack[0] == 0x3998400    # low word


@passmein
def test_multiply_only_returns_low_word(me):
    """doLIT 4300000 doLIT 12000 *"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 0x3998400


@passmein
def test_mstar_multiplies_with_sign(me):
    """doLIT -7654 doLIT 35132 M*"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[1] == -1               # high word
    assert stack[0] == -(7654*35132)    # low word


@passmein
def test_mstar_creates_positiv_with_two_negatives(me):
    """doLIT -7654 doLIT -5132 M*"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[1] == 0
    assert stack[0] == 7654 * 5132


@passmein
def test_multiply_mod_works_correctly(me):
    """doLIT 3252 doLIT 2349 doLIT 342 */MOD"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 2
    assert stack[1] == 22336    # quotient
    assert stack[0] == 36       # modulus


# ------------------------
# Bits & Bytes
@passmein
def test_cells_converts_cell_count_to_bytes(me):
    """doLIT 7 CELLS"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 1
    assert stack[0] == 28


class TestToChar:
    def test_turns_non_printable_char_to_underscore(self):
        stack = run_vm_image("doLIT 10 >CHAR")

        assert len(stack) == 1
        assert stack[0] == ord('_')

    def test_keeps_printable_char_as_is(self):
        stack = run_vm_image("doLIT 65 >CHAR")

        assert len(stack) == 1
        assert stack[0] == ord('A')


@passmein
def test_depth_runs_item_count_in_stack(me):
    """doLIT 3252 doLIT 2349 doLIT 342 DEPTH"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 4
    assert stack[3] == 3        # depth
    assert stack[2] == 342
    assert stack[1] == 2349
    assert stack[0] == 3252


@passmein
def test_pick_2_takes_third_stack_entry(me):
    """doLIT 3252 doLIT 2349 doLIT 342 doLIT 2 PICK"""
    stack = run_vm_image(me.__doc__)

    assert len(stack) == 4
    assert stack[3] == 3252
    assert stack[2] == 342
    assert stack[1] == 2349
    assert stack[0] == 3252


# ------------------------
# Memory access
@passmein
def test_plus_store_increases_value_at_address(me):
    """doLIT 123 PRE_INIT_DATA +! PRE_INIT_DATA @
    """
    stack = run_vm_image(me.__doc__, test_data=[0x0, 0x10, 0x0, 0x0])
    assert len(stack) == 1
    assert stack[0] == 0x1000 + 123


@passmein
def test_2store_stores_double_integer(me):
    """doLIT 123 doLIT 456 PRE_INIT_DATA 2! PRE_INIT_DATA @ PRE_INIT_DATA CELL+ @"""
    stack = run_vm_image(me.__doc__, test_data=8*[0x0])
    assert len(stack) == 2
    assert stack[0] == 456
    assert stack[1] == 123


@passmein
def test_2at_gets_double_integer_from_address(me):
    """PRE_INIT_DATA 2@"""
    stack = run_vm_image(me.__doc__, test_data=[0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8])
    assert len(stack) == 2
    assert stack[0] == 0x08070605
    assert stack[1] == 0x04030201


@passmein
def test_count_turns_counted_string_to_address_and_count(me):
    """PRE_INIT_DATA DUP
    COUNT
    """
    stack = run_vm_image(me.__doc__, test_data=[0x3, 0x6f, 0x6b, 0x2e])

    assert len(stack) == 3
    pre_init_address = stack[0]
    assert stack[2] == 3
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
    assert stack[2] == 0xd8
    assert stack[1] == 0x53
    assert stack[0] == 0x34


@passmein
def test_fill_puts_character_in_memory_block(me):
    """PRE_INIT_DATA doLIT 3 doLIT 10 FILL
    PRE_INIT_DATA C@
    PRE_INIT_DATA doLIT 1 + C@
    PRE_INIT_DATA doLIT 2 + C@
    PRE_INIT_DATA doLIT 3 + C@
    """
    stack = run_vm_image(me.__doc__, test_data=4*[0x0])
    assert len(stack) == 4
    assert stack[0] == 10
    assert stack[1] == 10
    assert stack[2] == 10
    assert stack[3] == 0


@passmein
def test_mtrailing_removes_leading_whitespace(me):
    """PRE_INIT_DATA doLIT 4 -TRAILING PRE_INIT_DATA
    """
    stack = run_vm_image(me.__doc__, test_data=[0x65, 0x66, 0x20, 0x20])
    assert len(stack) == 3
    pre_init_address = stack[2]
    assert stack[1] == 2
    assert stack[0] == pre_init_address


@passmein
def test_pack_copies_string_with_length(me):
    """PRE_INIT_DATA doLIT 3 doLIT 28500 PACK$
    doLIT 28500 C@
    doLIT 28501 C@
    doLIT 28502 C@
    doLIT 28503 C@
    """
    stack = run_vm_image(me.__doc__, test_data=[0x34, 0x53, 0xd8])
    assert len(stack) == 5
    assert stack[4] == 0xd8
    assert stack[3] == 0x53
    assert stack[2] == 0x34
    assert stack[1] == 0x3      # first byte at target is length
    assert stack[0] == 28500    # PACK$ returns the target address


# ------------------------
# Basic I/O
@passmein
def test_stringQuoteBar_leaves_string_address_on_stack(me):
    """STRING_ADDRESS_TEST
    """
    stack = run_vm_image(me.__doc__)
    assert len(stack) == 2
    assert stack[0] == stack[1]


@passmein
def test_say_hello(me):
    """PRE_INIT_DATA doLIT 5 TYPE"""
    parse_input = "Hello"
    run_vm_image(me.__doc__, test_data=list(map(ord, parse_input)))
    # TODO: capture stdout to check for 'Hello'


@passmein
def test_print_right_justified_number(me):
    """doLIT 123 doLIT 5 .R"""
    run_vm_image(me.__doc__)
    # TODO: capture stdout to check for '  123'


@passmein
def test_dot_outputs_unsigned_number_with_space_in_front(me):
    """doLIT 4352 ."""
    run_vm_image(me.__doc__)
    # TODO: capture stdout to check for ' 4352'


@passmein
def test_dot_outputs_signed_number_with_space_and_sign_in_front(me):
    """doLIT -4352 ."""
    run_vm_image(me.__doc__)
    # TODO: capture stdout to check for ' -4352'


# ------------------------

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
    pre_init_address = stack[0]
    assert stack[1] == pre_init_address + 2
    assert stack[2] == 4
    assert stack[3] == 7


@passmein
def test_parse_finds_one_space_delimited_word_from_multiple(me):
    """PRE_INIT_DATA PRE_INIT_DATA doLIT 80 BL parse"""
    parse_input = "   oneword   nextword  "
    stack = run_vm_image(me.__doc__, test_data=list(map(ord, parse_input)))

    assert len(stack) == 4
    pre_init_address = stack[0]
    assert stack[1] == pre_init_address + 3
    assert stack[2] == 7
    assert stack[3] == 11


@passmein
def test_parse_finds_text_delimited_by_bracket(me):
    # doLIT 41 == ord(')')
    """PRE_INIT_DATA PRE_INIT_DATA doLIT 80 doLIT 41 parse"""
    parse_input = "  comment text)"
    stack = run_vm_image(me.__doc__, test_data=list(map(ord, parse_input)))

    assert len(stack) == 4
    pre_init_address = stack[0]
    assert stack[1] == pre_init_address
    assert stack[2] == 14
    assert stack[3] == 15


# ------------------------
# accept

@passmein
def test_expect_returns_the_address_and_the_amount_of_read_chars(me):
    """doLIT 12000 doLIT 80 accept"""
    stack = run_vm_image(me.__doc__, "hello\n")

    assert len(stack) == 2
    assert stack[1] == 5
    assert stack[0] == 12000

# ------------------------
# QUERY

@passmein
def test_QUERY_stores_number_of_read_characters_and_resets_parser_pointer(me):
    """QUERY #TIB @ >IN @"""
    stack = run_vm_image(me.__doc__, "hello\n")

    assert len(stack) == 2
    assert stack[1] == 0
    assert stack[0] == 5
