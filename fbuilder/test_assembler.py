from assembler import *
from app import Assembler
from dataclasses import dataclass
import pytest


def assemble(source):
    @dataclass
    class DefaultOptions:
        format: str = "bin"
    asm = Assembler(DefaultOptions())
    return asm.assemble_source(source)


def test_alignment_function():
    assert aligned(1, 4) == 4
    assert aligned(4, 4) == 4
    assert aligned(13, 4) == 16
    assert aligned(43, 16) == 48


class TestOpcodeHandling:
    def test_currently_unsupported_opcodes_are_reported(self):
        source = """
        codeblock
            unsup
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "Opcode 'unsup' currently not implemented" in str(parsing_error)


def test_hexadecimal_number_is_correctly_parsed():
    source = """
    codeblock
        ifkt #0x1234
    end
    """

    binary = b"\xfe\x34\x12"

    assert binary == assemble(source)


def test_constant_is_replaced_in_parameters():
    source = """
    const IFKT_VALUE = 0x1236
    codeblock
        ifkt IFKT_VALUE
    end
    """

    binary = b"\xfe\x36\x12"

    assert binary == assemble(source)


def test_ifkt_is_translated_with_16bit_argument():
    source = """
    codeblock
        ifkt #1234
        ifkt #32152
    end
    """

    binary = b"\xfe\xd2\x04\xfe\x98\x7d"

    assert binary == assemble(source)


class TestAssemblingMacros:
    def test_calling_macros_inserts_the_code(self):
        source = """
        macro TEST()
            illegal
        end

        codeblock
            TEST()
        end
        """

        binary = b"\xff"    # online contains the 'illegal' instruction once

        assert binary == assemble(source)

    def test_calling_macro_with_register_inserts_correctly(self):
        source = """
        macro TEST(reg)
            mov %acc1, @reg
        end

        codeblock
            TEST(%dsp)
        end
        """

        binary = b"\x20\x43"

        assert binary == assemble(source)

    def test_calling_macro_with_value_and_register_inserts_correctly(self):
        source = """
        macro LOAD_IMMEDIATE(reg, value)
            mov %acc1, @value
            mov @reg, %acc1
        end

        codeblock
            LOAD_IMMEDIATE(%dsp, #0x34)
        end
        """
        binary = b"\x26\x34\x00\x00\x00\x20\x34"

        assert binary == assemble(source)

    def test_trying_to_call_undefined_macro_raises_exception(self):
        source = """
        codeblock
            MISSING_MACRO()
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)

    def test_trying_to_call_with_mismatching_amount_of_arguments_raises_exception(self):
        source = """
        macro LOAD_IMMEDIATE(reg, value)
            mov %acc1, @value
            mov @reg, %acc1
        end

        codeblock
            LOAD_IMMEDIATE(%dsp)
        end
        """
        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 8" in str(parsing_error)
        assert "Calling macro with 1 parameter where 2 are expected" in str(parsing_error)

    def test_trying_to_call_with_unknown_argument_raises_exception(self):
        source = """
        macro LOAD_IMMEDIATE(reg)
            mov %acc1, @value
            mov @reg, %acc1
        end

        codeblock
            LOAD_IMMEDIATE(%dsp)
        end
        """
        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "Unknown macro argument 'value'" in str(parsing_error)

    def test_support_for_macro_local_labels(self):
        source = """
        macro INSERT_LABEL()
            dw :'label
        'label:
        end

        codeblock
            INSERT_LABEL()
            INSERT_LABEL()
        end
        """
        binary = b"\x04\x00\x00\x00\x08\x00\x00\x00"

        assert binary == assemble(source)


class TestAssemblingDwInstructions:
    def test_immediate_32bit_values_are_inserted_in_correct_byte_order(self):
        source = """
        codeblock
            dw #0x12345678
        end
        """
        binary = b"\x78\x56\x34\x12"

        assert binary == assemble(source)

    def test_constants_are_inserted_in_correct_byte_order(self):
        source = """
        const MY_VALUE = 0x36295372
        codeblock
            dw MY_VALUE
        end
        """
        binary = b"\x72\x53\x29\x36"

        assert binary == assemble(source)

    def test_labels_are_inserted_in_correct_byte_order(self):
        source = """
        codeblock
            dw :mylabel
        mylabel:
        end
        """
        binary = b"\x04\x00\x00\x00"

        assert binary == assemble(source)


class TestAssemblingDbInstructions:
    def test_immediate_8bit_values_are_inserted(self):
        source = """
        codeblock
            db #0x12
        end
        """
        binary = b"\x12"

        assert binary == assemble(source)

    def test_strings_are_inserted_as_bytes(self):
        source = """
        codeblock
            db "Hello"
        end
        """
        binary = b"\x48\x65\x6c\x6c\x6f"

        assert binary == assemble(source)

    def test_constants_are_inserted(self):
        source = """
        const MY_VALUE = 0x36
        codeblock
            db MY_VALUE
        end
        """
        binary = b"\x36"

        assert binary == assemble(source)

    def test_db_values_outside_range_raise_exception(self):
        source = """
        codeblock
            db #0x12345678
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "constant 0x12345678 is too big for db" in str(parsing_error)


class TestExpressions:
    def test_dollar_inserts_current_address(self):
        source = """
        codeblock
            nop // to get a little offset such that $ is not 0x0
            nop
            dw $
        end
        """
        binary = b"\x00\x00"
        binary += b"\x02\x00\x00\x00"

        assert binary == assemble(source)

    def test_dollar_based_addition_expression_is_properly_evaluated(self):
        source = """
        codeblock
            nop // to get a little offset such that $ is not 0x0
            nop
            dw $+#4
        end
        """
        binary = b"\x00\x00"
        binary += b"\x06\x00\x00\x00"

        assert binary == assemble(source)

    def test_dollar_based_subtraction_expression_is_properly_evaluated(self):
        source = """
        codeblock
            nop // to get a little offset such that $ is not 0x0
            nop
            dw $-#2
        end
        """
        binary = b"\x00\x00"
        binary += b"\x00\x00\x00\x00"

        assert binary == assemble(source)

    def test_expressions_of_labels_are_calculated_correctly(self):
        source = """
        codeblock
        start:
            dw #0x1
        entry2:
            dw #0x2
        entry3:
            dw #0x3
        calculation:
            dw :entry3 - :entry2
        end
        """
        binary = b"\x01\x00\x00\x00"
        binary += b"\x02\x00\x00\x00"
        binary += b"\x03\x00\x00\x00"
        binary += b"\x04\x00\x00\x00"

        assert binary == assemble(source)

    def test_expressions_of_labels_are_calculated_for_bytes(self):
        source = """
        codeblock
        start:
            dw #0x1
        entry2:
            dw #0x2
        entry3:
            dw #0x3
        calculation:
            db :entry3 - :entry2
        end
        """
        binary = b"\x01\x00\x00\x00"
        binary += b"\x02\x00\x00\x00"
        binary += b"\x03\x00\x00\x00"
        binary += b"\x04"

        assert binary == assemble(source)

    def test_dollar_inside_macro_uses_the_address_at_insertion(self):
        source = """
        macro CURRENT_ADDRESS()
            dw $
        end

        codeblock
            nop
            CURRENT_ADDRESS()
            CURRENT_ADDRESS()
        end
        """
        binary = b"\x00"
        binary += b"\x01\x00\x00\x00"
        binary += b"\x05\x00\x00\x00"

        assert binary == assemble(source)


class TestAssemblingJmpInstructions:
    def test_jmp_register_indirect(self):
        source = """
        codeblock
            jmp [%ip]
            jmp [%wp]
            jmp [%rsp]
            jmp [%dsp]
            jmp [%acc1]
            jmp [%acc2]
            jmp [%ret]
            jmp [%pc]
        end
        """
        binary = b"\x60"
        binary += b"\x61"
        binary += b"\x62"
        binary += b"\x63"
        binary += b"\x64"
        binary += b"\x65"
        binary += b"\x66"
        binary += b"\x67"

        assert binary == assemble(source)

    def test_jmp_register_direct(self):
        source = """
        codeblock
            jmp %ip
            jmp %wp
            jmp %rsp
            jmp %dsp
            jmp %acc1
            jmp %acc2
            jmp %ret
            jmp %pc
        end
        """
        binary = b"\x68"
        binary += b"\x69"
        binary += b"\x6a"
        binary += b"\x6b"
        binary += b"\x6c"
        binary += b"\x6d"
        binary += b"\x6e"
        binary += b"\x6f"

        assert binary == assemble(source)

    def test_jmp_absolute_to_label(self):
        source = """
        codeblock
            jmp :jump_target
            nop
            nop
        jump_target:
            nop
        end
        """
        binary = b"\x70\x07\x00\x00\x00"
        binary += b"\x00"
        binary += b"\x00"
        binary += b"\x00"

        assert binary == assemble(source)

    def test_jmp_absolute_to_label_complex_case(self):
        source = """
        codeblock
            jmp :target1    // offset 0x0
        target2:
            jmp :target3    // offset 0x5
        target1:
            jmp :target2    // offset 0xa
        target3:
            nop             // offset 0xf
        end
        """
        binary = b"\x70\x0a\x00\x00\x00"
        binary += b"\x70\x0f\x00\x00\x00"
        binary += b"\x70\x05\x00\x00\x00"
        binary += b"\x00"

        assert binary == assemble(source)

    def test_jmp_across_codeblocks_works(self):
        source = """
        codeblock
            jmp :target1    // offset 0x0
        end
        codeblock
        target1:
            nop
        end
        """
        binary = b"\x70\x05\x00\x00\x00"
        binary += b"\x00"

        assert binary == assemble(source)

    def test_jz_absolute_to_label(self):
        source = """
        codeblock
            jz :jump_target
            nop
            nop
        jump_target:
            nop
        end
        """
        binary = b"\x71\x07\x00\x00\x00"
        binary += b"\x00"
        binary += b"\x00"
        binary += b"\x00"

        assert binary == assemble(source)

    def test_jc_absolute_to_label(self):
        source = """
        codeblock
            jc :jump_target
            nop
            nop
        jump_target:
            nop
        end
        """
        binary = b"\x72\x07\x00\x00\x00"
        binary += b"\x00"
        binary += b"\x00"
        binary += b"\x00"

        assert binary == assemble(source)

    def test_call_absolute_to_label(self):
        source = """
        codeblock
            call :jump_target
            nop
            nop
        jump_target:
            nop
        end
        """
        binary = b"\x73\x07\x00\x00\x00"
        binary += b"\x00"
        binary += b"\x00"
        binary += b"\x00"

        assert binary == assemble(source)


class TestAssemblingStackInstructions:
    def test_data_stack_instructions(self):
        source = """
        codeblock
            pushd %acc1
            pushd.w %ip
            popd %acc2
            popd.w %wp
        end
        """

        binary = b"\xA4"
        binary += b"\xA0"
        binary += b"\xAD"
        binary += b"\xA9"

        assert binary == assemble(source)

    def test_return_stack_instructions(self):
        source = """
        codeblock
            pushr %acc1
            pushr.w %ip
            popr %acc2
            popr.w %wp
        end
        """

        binary = b"\xB4"
        binary += b"\xB0"
        binary += b"\xBD"
        binary += b"\xB9"

        assert binary == assemble(source)

    def test_data_stack_push_byte_operation_is_not_allowed(self):
        source = """
        codeblock
            pushd.b %acc1
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "pushd only supports word-sized mode" in str(parsing_error)

    def test_data_stack_pop_byte_operation_is_not_allowed(self):
        source = """
        codeblock
            popd.b %acc1
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "popd only supports word-sized mode" in str(parsing_error)

    def test_return_stack_push_byte_operation_is_not_allowed(self):
        source = """
        codeblock
            pushr.b %acc1
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "pushr only supports word-sized mode" in str(parsing_error)

    def test_return_stack_pop_byte_operation_is_not_allowed(self):
        source = """
        codeblock
            popr.b %acc1
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "popr only supports word-sized mode" in str(parsing_error)


class TestAssemblingMovInstructions:
    def test_moving_between_instructions(self):
        source = """
        codeblock
            mov.b %wp, %acc1
            mov.b %rsp, %acc2
            mov.b [%dsp], %ip
            mov.b %wp, [%acc1]
            mov.b [%acc1], [%acc2]
        end
        """

        binary = b"\x21\x14"
        binary += b"\x21\x25"
        binary += b"\x21\xb0"
        binary += b"\x21\x1c"
        binary += b"\x21\xcd"

        assert binary == assemble(source)

    def test_word_based_moving(self):
        source = """
        codeblock
            mov.w %wp, %acc1
            mov %wp, %acc1     // without suffix, 'word' is assumed
        end
        """

        binary = b"\x20\x14\x20\x14"
        assert binary == assemble(source)

    def test_moving_from_acc1_to_wp_post_increment(self):
        source = """
        codeblock
            mov.w [%wp++], %acc1
        end
        """

        binary = b"\x22\x0c"

        assert binary == assemble(source)

    def test_moving_byte_from_acc1_to_wp_post_increment(self):
        source = """
        codeblock
            mov.b [%wp++], %acc1
        end
        """

        binary = b"\x23\x0c"

        assert binary == assemble(source)

    def test_moving_from_acc2_to_rsp_pre_decrement(self):
        source = """
        codeblock
            mov.w [--%rsp], %acc2
        end
        """

        binary = b"\x22\xd5"

        assert binary == assemble(source)

    def test_moving_byte_from_acc2_to_rsp_pre_decrement(self):
        source = """
        codeblock
            mov.b [--%rsp], %acc2
        end
        """

        binary = b"\x23\xd5"

        assert binary == assemble(source)

    def test_moving_from_ip_pre_decrement_to_acc1(self):
        source = """
        codeblock
            mov.w %acc1, [--%ip]
        end
        """

        binary = b"\x24\xe0"

        assert binary == assemble(source)

    def test_moving_byte_from_ip_pre_decrement_to_acc1(self):
        source = """
        codeblock
            mov.b %acc1, [--%ip]
        end
        """

        binary = b"\x25\xe0"

        assert binary == assemble(source)

    def test_moving_from_rsp_post_decrement_to_acc2(self):
        source = """
        codeblock
            mov.w %acc2, [%rsp--]
        end
        """

        binary = b"\x24\xaa"

        assert binary == assemble(source)

    def test_moving_byte_from_rsp_post_decrement_to_acc2(self):
        source = """
        codeblock
            mov.b %acc2, [%rsp--]
        end
        """

        binary = b"\x25\xaa"

        assert binary == assemble(source)

    def test_moving_from_indirect_to_indirect_raises_exception(self):
        source = """
        codeblock
            mov.w [%acc1++], [--%ip]
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "only one argument can be register indirect for mov" in str(parsing_error)

    def test_moving_from_label_to_acc1_register(self):
        source = """
        codeblock
            nop
        test1:
            mov.w %acc1, :test1
        end
        """

        binary = b"\x00\x26\x01\x00\x00\x00"

        assert binary == assemble(source)

    def test_moving_from_label_to_acc2_register(self):
        source = """
        codeblock
            nop
        test1:
            mov.w %acc2, :test1
        end
        """

        binary = b"\x00\x27\x01\x00\x00\x00"

        assert binary == assemble(source)

    def test_moving_label_to_register_other_than_acc1_and_acc2_raises_exception(self):
        source = """
        codeblock
            nop
        test1:
            mov.w %dsp, :test1
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 5" in str(parsing_error)
        assert "label can only be moved to acc1 or acc2" in str(parsing_error)

    def test_moving_from_immediate_value_to_acc1_register(self):
        source = """
        codeblock
            mov.w %acc1, #0xab0356
        end
        """

        binary = b"\x26\x56\x03\xab\x00"

        assert binary == assemble(source)

    def test_moving_from_immediate_value_to_acc2_register(self):
        source = """
        codeblock
            mov.w %acc2, #0xab0356
        end
        """

        binary = b"\x27\x56\x03\xab\x00"

        assert binary == assemble(source)

    def test_moving_immediate_value_to_register_other_than_acc1_raises_exception(self):
        source = """
        codeblock
            mov.w %dsp, #0x123532
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "immediate value can only be moved to acc1 or acc2" in str(parsing_error)


class TestCodeDefinitions:
    def test_code_definition_starts_with_backlink(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def asm(code) WORD1
            // backlink (4) + word size (1) + word name (5)
            nop
            // additional offset 1
        end
        def asm(code) WORD2
            // backlink (4) + word size (1) + word name (5)
            nop
            // additional offset 1
        end
        """
        result = assemble(source)
        assert result[1:5] == b"\x00\x00\x00\x00"       # backlink for WORD1 is 0
        assert result[12:16] == b"\x01\x00\x00\x00"     # backlink for WORD2 points to WORD1

    def test_code_definition_contains_word_name(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def asm(code) WORD1
            // backlink (4) + word size (1) + word name (5)
            nop
            // additional offset 1
        end
        def asm(code) WORD2
            // backlink (4) + word size (1) + word name (5)
            nop
            // additional offset 1
        end
        """
        result = assemble(source)
        assert result[5] == 5  # word length in characters
        assert result[6:11] == b"WORD1"

    def test_code_definition_gets_numeric_flag_in_name_length(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def asm[#0x80](code) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 0x80 | 5  # word length in characters

    def test_code_definition_gets_constant_flag_in_name_length(self):
        source = """
        const IMMEDIATE = 0x80
        codeblock
            nop
        end
        // code offset 0x1
        def asm[IMMEDIATE](code) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 0x80 | 5  # word length in characters

    def test_code_definition_gets_flags_in_name_length(self):
        source = """
        const IMMEDIATE = 0x80
        codeblock
            nop
        end
        // code offset 0x1
        def asm[IMMEDIATE, #0x40](code) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 0xc0 | 5  # word length in characters

    def test_cfa_is_filled_with_macro(self):
        source = """
        macro __DEFCODE_CFA()
            dw #0x3829af7b
        end
        codeblock
            nop
        end
        // code offset 0x1
        def asm(code) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\x7b\xaf\x29\x38"

    def test_address_of_cfa_is_available_as_label(self):
        source = """
        codeblock
            dw :word1_cfa
        end
        // code offset 0x4
        def asm(code) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[0:4] == b"\x0e\x00\x00\x00"

    def test_first_address_after_word_is_available_as_label(self):
        source = """
        codeblock
            dw :word1_end
        end
        // code offset 0x4
        def asm(code) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[0:4] == b"\x0e\x00\x00\x00"

    def test_if_available_uses_alias_for_address_labels(self):
        source = """
        codeblock
            dw :word1_alias_cfa
        end
        // code offset 0x4
        def asm(code) alias WORD1_ALIAS WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[0:4] == b"\x0e\x00\x00\x00"


class TestWordDefinitions:
    def test_word_definition_starts_with_backlink(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) //+ word size (1) + word name (5)
        end
        def word(colon) WORD2
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[1:5] == b"\x00\x00\x00\x00"       # backlink for WORD1 is 0
        assert result[11:15] == b"\x01\x00\x00\x00"     # backlink for WORD2 points to WORD1

    def test_word_definition_contains_word_name(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 5  # word length in characters
        assert result[6:11] == b"WORD1"

    def test_word_definition_gets_numeric_flag_in_name_length(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word[#0x80](colon) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 0x80 | 5  # word length in characters

    def test_word_definition_gets_constant_flag_in_name_length(self):
        source = """
        const IMMEDIATE = 0x80
        codeblock
            nop
        end
        // code offset 0x1
        def word[IMMEDIATE](colon) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 0x80 | 5  # word length in characters

    def test_word_definition_gets_flags_in_name_length(self):
        source = """
        const IMMEDIATE = 0x80
        codeblock
            nop
        end
        // code offset 0x1
        def word[IMMEDIATE, #0x40](colon) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 0xc0 | 5  # word length in characters

    def test_cfa_is_filled_with_macro(self):
        source = """
        macro __DEFCOLON_CFA()
            dw #0x3829af7b
        end
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\x7b\xaf\x29\x38"

    def test_words_are_compiled_into_cfas(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        def word(colon) WORD2
            // backlink (4) + word size (1) + word name (5)
            WORD1
        end
        """
        result = assemble(source)
        assert result[21:26] == b"\x0b\x00\x00\x00"

    def test_constants_in_word_definitions_are_replaced(self):
        source = """
        const C = 0xa210
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
            C
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\x10\xa2\x00\x00"

    def test_missing_words_raise_an_exception(self):
        source = """
        codeblock
            nop
        end
        def word(colon) WORD1
            missing_word
        end
        """
        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "Word 'missing_word' not found in current dictionary" in str(parsing_error)
        assert "on line 6" in str(parsing_error)

    def test_non_existing_words_ending_with_colon_in_definitions_are_treated_as_labels(self):
        source = """
        codeblock
            nop
        end
        def word(colon) WORD1
            missing_word:
        end
        """

        assemble(source)

    def test_missing_words_beginning_with_colon_are_resolved_as_label_targets(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        def word(colon) WORD2
            // offset 11d
            // backlink (4) + word size (1) + word name (5)
            // offset 21d = 15h
            word_label:     // no code generated
            WORD1           // 4 bytes for CFA
            // offset 25d
            :word_label     // 4 bytes for resolved word_label
        end
        """

        result = assemble(source)
        assert result[25:30] == b"\x15\x00\x00\x00"

    def test_address_of_cfa_is_available_as_label(self):
        source = """
        codeblock
            dw :word1_cfa
        end
        // code offset 0x4
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[0:4] == b"\x0e\x00\x00\x00"

    def test_if_available_uses_alias_for_address_labels(self):
        source = """
        codeblock
            dw :word1_alias_cfa
        end
        // code offset 0x4
        def word(colon) alias WORD1_ALIAS WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[0:4] == b"\x0e\x00\x00\x00"

    def test_defcode_addresses_are_properly_resolved_with_cfas(self):
        source = """
        macro __DEFCODE_CFA()
            dw #0x0
        end
        // code offset 0
        def asm(code) A
            // backlink (4) + word size (1) + word name (1)
            // offset 6
            // CFA (4) --> offset 10
            illegal
        end
        // code offset 11
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
            // offset 21
            A
        end
        """
        result = assemble(source)
        assert result[21:25] == b"\x06\x00\x00\x00"

    def test_defword_addresses_are_properly_resolved_with_cfas(self):
        source = """
        macro __DEFCOLON_CFA()
            dw #0x0
        end
        // code offset 0
        def word(colon) A
            // backlink (4) + word size (1) + word name (1) + CFA (4)
            // offset 10
        end
        // code offset 10
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5) + CFA(4)
            // offset 24
            A
        end
        """
        result = assemble(source)
        assert result[24:29] == b"\x06\x00\x00\x00"

    def test_first_address_after_word_is_available_as_label(self):
        source = """
        codeblock
            dw :word1_end
        end
        // code offset 0x4
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[0:4] == b"\x0e\x00\x00\x00"

    def test_words_that_are_immediate_numbers_will_be_inserted_as_plain_numbers(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
            #0x1234
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\x34\x12\x00\x00"

    def test_words_that_are_hex_numbers_will_be_inserted_as_plain_numbers(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
            0x1234
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\x34\x12\x00\x00"

    def test_words_that_are_dec_numbers_will_be_inserted_as_plain_numbers(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
            234153
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\xa9\x92\x03\x00"

    def test_words_that_are_numbers_with_a_sign_are_inserted_as_plain_number(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(colon) WORD1
            // backlink (4) + word size (1) + word name (5)
            -1
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\xff\xff\xff\xff"


class TestCustomWordTypes:
    def test_custom_word_type_starts_with_backlink(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(mytype) WORD1
            // backlink (4) //+ word size (1) + word name (5)
        end
        def word(mytype) WORD2
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[1:5] == b"\x00\x00\x00\x00"       # backlink for WORD1 is 0
        assert result[11:15] == b"\x01\x00\x00\x00"     # backlink for WORD2 points to WORD1

    def test_custom_word_type_contains_word_name(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(mytype) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 5  # word length in characters
        assert result[6:11] == b"WORD1"

    def test_cfa_is_filled_with_macro(self):
        source = """
        macro __DEFMYTYPE_CFA()
            dw #0x3829af7b
        end
        codeblock
            nop
        end
        // code offset 0x1
        def word(mytype) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\x7b\xaf\x29\x38"

    def test_custom_types_are_compiled_into_cfas(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def word(mytype) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        def word(mytype) WORD2
            // backlink (4) + word size (1) + word name (5)
            WORD1
        end
        """
        result = assemble(source)
        assert result[21:26] == b"\x0b\x00\x00\x00"


class TestCustomAsmTypes:
    def test_custom_asm_type_starts_with_backlink(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def asm(mytype) WORD1
            // backlink (4) //+ word size (1) + word name (5)
        end
        def asm(mytype) WORD2
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[1:5] == b"\x00\x00\x00\x00"       # backlink for WORD1 is 0
        assert result[11:15] == b"\x01\x00\x00\x00"     # backlink for WORD2 points to WORD1

    def test_custom_asm_type_contains_word_name(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        def asm(mytype) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 5  # word length in characters
        assert result[6:11] == b"WORD1"

    def test_cfa_is_filled_with_macro(self):
        source = """
        macro __DEFMYTYPE_CFA()
            dw #0x3829af7b
        end
        codeblock
            nop
        end
        // code offset 0x1
        def asm(mytype) WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\x7b\xaf\x29\x38"


class TestALUInstruction:
    def test_adding_two_registers(self):
        source = """
        codeblock
            add.w %ip, %wp, %acc1
        end
        """

        binary = b"\x30\x01\x04"

        assert binary == assemble(source)

    def test_subtracting_two_registers(self):
        source = """
        codeblock
            sub.w %ip, %wp, %acc1
        end
        """

        binary = b"\x32\x01\x04"

        assert binary == assemble(source)

    def test_oring_two_registers(self):
        source = """
        codeblock
            or.w %ip, %wp, %acc1
        end
        """

        binary = b"\x34\x01\x04"

        assert binary == assemble(source)

    def test_anding_two_registers(self):
        source = """
        codeblock
            and.w %ip, %wp, %acc1
        end
        """

        binary = b"\x36\x01\x04"

        assert binary == assemble(source)

    def test_xoring_two_registers(self):
        source = """
        codeblock
            xor.w %ip, %wp, %acc1
        end
        """

        binary = b"\x38\x01\x04"

        assert binary == assemble(source)

    def test_shift_right_arithmetically(self):
        source = """
        codeblock
            sra.w %dsp, #5
        end
        """

        binary = b"\x3c\x65"

        assert binary == assemble(source)

    def test_shift_left_logically(self):
        source = """
        codeblock
            sll.w %dsp, #2
        end
        """

        binary = b"\x3e\x62"

        assert binary == assemble(source)
