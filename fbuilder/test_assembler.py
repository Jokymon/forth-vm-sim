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
            add
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "Opcode 'add' currently not implemented" in str(parsing_error)

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


def test_calling_macros_inserts_the_code():
    source = """
    macro TEST
        illegal
    end

    codeblock
        $TEST()
    end
    """

    binary = b"\xff"    # online contains the 'illegal' instruction once

    assert binary == assemble(source)


def test_trying_to_call_undefined_macro_raises_exception():
    source = """
    codeblock
        $MISSING_MACRO()
    end
    """

    with pytest.raises(ValueError) as parsing_error:
        assemble(source)
    assert "on line 3" in str(parsing_error)


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


class TestAssemblingMovrInstructions:
    def test_moving_between_instructions(self):
        source = """
        codeblock
            movr.b %wp, %acc1
            movr.b %rsp, %acc2
            movr.b [%dsp], %ip
            movr.b %wp, [%acc1]
            movr.b [%acc1], [%acc2]
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
            movr.w %wp, %acc1
            movr %wp, %acc1     // without suffix, 'word' is assumed
        end
        """

        binary = b"\x20\x14\x20\x14"
        assert binary == assemble(source)

    def test_movr_raises_exception_when_using_increment_or_decrements(self):
        source = """
        codeblock
            movr.w [%wp++], %acc1
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "movr doesn't support any increment or decrement operations" in str(parsing_error)


class TestAssemblingMovsInstructions:
    def test_moving_from_acc1_to_wp_post_increment(self):
        source = """
        codeblock
            movs.w [%wp++], %acc1
        end
        """

        binary = b"\x22\x0c"

        assert binary == assemble(source)

    def test_moving_from_acc2_to_rsp_pre_decrement(self):
        source = """
        codeblock
            movs.w [--%rsp], %acc2
        end
        """

        binary = b"\x22\xd5"

        assert binary == assemble(source)

    def test_moving_from_ip_pre_decrement_to_acc1(self):
        source = """
        codeblock
            movs.w %acc1, [--%ip]
        end
        """

        binary = b"\x24\xe0"

        assert binary == assemble(source)

    def test_moving_from_rsp_post_decrement_to_acc2(self):
        source = """
        codeblock
            movs.w %acc2, [%rsp--]
        end
        """

        binary = b"\x24\xaa"

        assert binary == assemble(source)

    def test_moving_from_indirect_to_indirect_raises_exception(self):
        source = """
        codeblock
            movs.w [%acc1++], [--%ip]
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "only one argument can be register indirect for movs" in str(parsing_error)

    def test_moving_from_direct_to_direct_raises_exception(self):
        source = """
        codeblock
            movs.w %acc1, %ip
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "only one argument can be register direct for movs" in str(parsing_error)

    def test_moving_to_indirect_without_operation_raises_exception(self):
        source = """
        codeblock
            movs.w [%acc1], %ip
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "movs indirect target requires a pre- or post- increment or decrement" in str(parsing_error)

    def test_moving_from_indirect_without_operation_raises_exception(self):
        source = """
        codeblock
            movs.w %acc1, [%ip]
        end
        """

        with pytest.raises(ValueError) as parsing_error:
            assemble(source)
        assert "on line 3" in str(parsing_error)
        assert "movs indirect source requires a pre- or post- increment or decrement" in str(parsing_error)


class TestCodeDefinitions:
    def test_code_definition_starts_with_backlink(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        defcode WORD1
            // backlink (4) + word size (1) + word name (5) + cfa field (4)
            nop
            // additional offset 1
        end
        defcode WORD2
            // backlink (4) + word size (1) + word name (5) + cfa field (4)
            nop
            // additional offset 1
        end
        """
        result = assemble(source)
        assert result[1:5] == b"\x00\x00\x00\x00"       # backlink for WORD1 is 0
        assert result[16:20] == b"\x01\x00\x00\x00"     # backlink for WORD2 points to WORD1

    def test_code_definition_contains_word_name(self):
        source = """
        codeblock
            nop
        end
        // code offset 0x1
        defcode WORD1
            // backlink (4) + word size (1) + word name (5) + cfa field (4)
            nop
            // additional offset 1
        end
        defcode WORD2
            // backlink (4) + word size (1) + word name (5) + cfa field (4)
            nop
            // additional offset 1
        end
        """
        result = assemble(source)
        assert result[5] == 5  # word length in characters
        assert result[6:11] == b"WORD1"
