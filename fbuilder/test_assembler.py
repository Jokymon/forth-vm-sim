from assembler import *
import pytest


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


class TestAssemblingDefSysVarDefinitions:
    def test_variable_definition_starts_with_backlink(self):
        source = """
        codeblock
            nop
        end

        defsysvar SP0
        """

        result = assemble(source)
        assert result[1:5] == b"\x00\x00\x00\x00"

    def test_variable_definition_contains_variable_name(self):
        source = """
        codeblock
            nop
        end
    
        defsysvar SP0
        """

        result = assemble(source)
        assert result[5] == 3
        assert result[6:9] == b"SP0"

    def test_variable_definition_contains_contains_default_0_value(self):
        source = """
        codeblock
            nop
        end

        defsysvar SP0
        """

        result = assemble(source)
        assert result[9:13] == b"\x00\x00\x00\x00"

    def test_variable_definition_contains_given_default_value(self):
        source = """
        codeblock
            nop
        end

        defsysvar SP0 #0xab78cd11
        """

        result = assemble(source)
        assert result[9:13] == b"\x11\xcd\x78\xab"

    def test_variable_definition_contains_given_label_target(self):
        source = """
        codeblock
            nop
        test_target:
        end

        defsysvar SP0 :test_target
        """

        result = assemble(source)
        assert result[9:13] == b"\x01\x00\x00\x00"

    def test_variable_definition_contains_given_constant_value(self):
        source = """
        const SP0_BASE = 0x5000
        codeblock
            nop
        test_target:
        end

        defsysvar SP0 SP0_BASE
        """

        result = assemble(source)
        assert result[9:13] == b"\x00\x50\x00\x00"

    def test_address_of_variable_is_provided_as_label(self):
        source = """
        codeblock
            nop
            dw :sp0_var
        end

        defsysvar SP0
        """

        result = assemble(source)
        # Address must be calculated from backlink, variable name length
        # and variable name itself
        assert result[1:5] == b"\x0d\x00\x00\x00"

    def test_cfa_of_variable_is_filled_with_macro(self):
        source = """
        macro __DEFVAR_CFA()
            dw #0x17fcaa55
        end
        codeblock
            nop
        end

        defsysvar SP0
        """

        result = assemble(source)
        assert result[9:13] == b"\x55\xaa\xfc\x17"


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


class TestCurrentAddressExpressions:
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
            dw $+4
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
            dw $-2
        end
        """
        binary = b"\x00\x00"
        binary += b"\x00\x00\x00\x00"

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
            jmp [%acc1]
            jmp [%acc2]
        end
        """
        binary = b"\x60"
        binary += b"\x61"
        binary += b"\x62"
        binary += b"\x63"

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
        binary = b"\x64\x07\x00\x00\x00"
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
        binary = b"\x64\x0a\x00\x00\x00"
        binary += b"\x64\x0f\x00\x00\x00"
        binary += b"\x64\x05\x00\x00\x00"
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
        binary = b"\x64\x05\x00\x00\x00"
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
        binary = b"\x65\x07\x00\x00\x00"
        binary += b"\x00"
        binary += b"\x00"
        binary += b"\x00"

        assert binary == assemble(source)



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

    def test_moving_from_acc2_to_rsp_pre_decrement(self):
        source = """
        codeblock
            mov.w [--%rsp], %acc2
        end
        """

        binary = b"\x22\xd5"

        assert binary == assemble(source)

    def test_moving_from_ip_pre_decrement_to_acc1(self):
        source = """
        codeblock
            mov.w %acc1, [--%ip]
        end
        """

        binary = b"\x24\xe0"

        assert binary == assemble(source)

    def test_moving_from_rsp_post_decrement_to_acc2(self):
        source = """
        codeblock
            mov.w %acc2, [%rsp--]
        end
        """

        binary = b"\x24\xaa"

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

    def test_moving_label_to_register_other_than_acc1_raises_exception(self):
        source = """
        codeblock
            nop
        test1:
            mov.w %acc2, :test1
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 5" in str(parsing_error)
        assert "label can only be moved to acc1" in str(parsing_error)

    def test_moving_from_immediate_value_to_acc1_register(self):
        source = """
        codeblock
            mov.w %acc1, #0xab0356
        end
        """

        binary = b"\x26\x56\x03\xab\x00"

        assert binary == assemble(source)

    def test_moving_immediate_value_to_register_other_than_acc1_raises_exception(self):
        source = """
        codeblock
            mov.w %acc2, #0x123532
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "immediate value can only be moved to acc1" in str(parsing_error)


class TestCodeDefinitions:
    def test_code_definition_starts_with_backlink(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        defcode WORD1
            // backlink (4) + word size (1) + word name (5)
            nop
            // additional offset 1
        end
        defcode WORD2
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
        defcode WORD1
            // backlink (4) + word size (1) + word name (5)
            nop
            // additional offset 1
        end
        defcode WORD2
            // backlink (4) + word size (1) + word name (5)
            nop
            // additional offset 1
        end
        """
        result = assemble(source)
        assert result[5] == 5  # word length in characters
        assert result[6:11] == b"WORD1"

    def test_cfa_is_filled_with_macro(self):
        source = """
        macro __DEFCODE_CFA()
            dw #0x3829af7b
        end
        codeblock
            nop
        end
        // code offset 0x1
        defcode WORD1
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
        defcode WORD1
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
        defcode WORD1
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
        defword WORD1
            // backlink (4) //+ word size (1) + word name (5)
        end
        defword WORD2
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
        defword WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        """
        result = assemble(source)
        assert result[5] == 5  # word length in characters
        assert result[6:11] == b"WORD1"

    def test_cfa_is_filled_with_macro(self):
        source = """
        macro __DEFWORD_CFA()
            dw #0x3829af7b
        end
        codeblock
            nop
        end
        // code offset 0x1
        defword WORD1
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
        defword WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        defword WORD2
            // backlink (4) + word size (1) + word name (5)
            WORD1
        end
        """
        result = assemble(source)
        assert result[21:26] == b"\x0b\x00\x00\x00"

    def test_missing_words_raise_an_exception(self):
        source = """
        codeblock
            nop
        end
        defword WORD1
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
        defword WORD1
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
        defword WORD1
            // backlink (4) + word size (1) + word name (5)
        end
        defword WORD2
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
        defword WORD1
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
        defcode A
            // backlink (4) + word size (1) + word name (1)
            // offset 6
            // CFA (4) --> offset 10
            illegal
        end
        // code offset 11
        defword WORD1
            // backlink (4) + word size (1) + word name (5)
            // offset 21
            A
        end
        """
        result = assemble(source)
        assert result[21:25] == b"\x06\x00\x00\x00"

    def test_defword_addresses_are_properly_resolved_with_cfas(self):
        source = """
        macro __DEFWORD_CFA()
            dw #0x0
        end
        // code offset 0
        defword A
            // backlink (4) + word size (1) + word name (1) + CFA (4)
            // offset 10
        end
        // code offset 10
        defword WORD1
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
        defword WORD1
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
        defword WORD1
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
        defword WORD1
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
        defword WORD1
            // backlink (4) + word size (1) + word name (5)
            234153
        end
        """
        result = assemble(source)
        assert result[11:15] == b"\xa9\x92\x03\x00"

class TestAddInstruction:
    def test_adding_three_registers(self):
        source = """
        codeblock
            add.w %ip, %wp, %acc1
        end
        """

        binary = b"\x30\x01\x04"

        assert binary == assemble(source)
