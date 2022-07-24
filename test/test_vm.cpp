#include <catch2/catch_test_macros.hpp>
#include "vm.h"

CATCH_REGISTER_ENUM(Vm::Result,
    Vm::Result::Success,
    Vm::Result::Finished,
    Vm::Result::Error,
    Vm::Result::IllegalInstruction
)


TEST_CASE("Memory access", "Loading VM memory through iterator") {
    std::array<uint8_t, 3> testdata = {0x23, 0x53, 0x61};

    Vm uut;

    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    REQUIRE( uut.byteAt(0x0) == 0x23 );
    REQUIRE( uut.byteAt(0x1) == 0x53 );
    REQUIRE( uut.byteAt(0x2) == 0x61 );
}

TEST_CASE("Illegal instructions return IllegalInstruction", "[opcode]") {
    std::array<uint8_t, 1> testdata = {
        0xfd            // just take come opcode that so far has no meaning ;-)
    };

    Vm uut;

    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    REQUIRE( Vm::IllegalInstruction == uut.singleStep() );
}

TEST_CASE("Register based move bytes instructions", "[opcode]") {
    std::array<uint8_t, 8> testdata = {
        0x21, 0x14,     // mov.b %wp, %acc1
        0x21, 0xd1,     // mov.b [%acc2], %wp
        0x21, 0x4b,     // mov.b %acc1, [%dsp]
        0x21, 0xcd,     // mov.b [%acc1], [%acc2]
    };

    Vm uut;

    auto state = uut.getState();
    state.registers[Vm::Acc1] = 0x59;
    state.registers[Vm::Acc2] = 0xff;
    uut.setState(state);

    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    // Register to register transfer
    // Pre: %acc1 = 0x59; %wp = 0x0
    REQUIRE( Vm::Success == uut.singleStep() );
    // Post: %acc1 = 0x59; %wp = 0x59
    state = uut.getState();
    REQUIRE( 0x59 == state.registers[Vm::Wp] );

    // Register to register indirect transfer
    // Pre: %wp = 0x59; %acc2 = 0xff; mem[0xff] = 0xff
    REQUIRE( Vm::Success == uut.singleStep() );
    // Post: %wp = 0x59; %acc2 = 0xff; mem[0xff] = 0x59
    REQUIRE( 0x59 == uut.byteAt(0xff) );

    // Register indirect to register transfer
    state = uut.getState();
    state.registers[Vm::Dsp] = 0x0;
    uut.setState(state);
    // Pre: %dsp = 0x0; %acc1 = 0x59; mem[0x0] = 0x21
    REQUIRE( Vm::Success == uut.singleStep() );
    // Post: %dsp = 0x0; %acc1 = 0x21; mem[0x0] = 0x21
    state = uut.getState();
    REQUIRE( 0x21 == state.registers[Vm::Acc1] );

    // Register indirect to register indirect transfer
    state = uut.getState();
    state.registers[Vm::Acc1] = 0x0;
    state.registers[Vm::Acc2] = 0x3;
    uut.setState(state);
    // Pre: %acc1 = 0x0; %acc2 = 0x3; mem[0x0] = 0x21; mem[0x3] = 0xd1;
    REQUIRE( Vm::Success == uut.singleStep() );
    // Post: %acc1 = 0x0; %acc2 = 0x3; mem[0x0] = 0xd1; mem[0x3] = 0xd1;
    REQUIRE( 0xd1 == uut.byteAt(0x0) );
}

TEST_CASE("Register based move words instructions", "[opcode]") {
    std::array<uint8_t, 8> testdata = {
        0x20, 0x14,     // mov.w %wp, %acc1
        0x20, 0xd1,     // mov.w [%acc2], %wp
        0x20, 0x4b,     // mov.w %acc1, [%dsp]
        0x20, 0xcd,     // mov.w [%acc1], [%acc2]
    };

    Vm uut;

    auto state = uut.getState();
    state.registers[Vm::Acc1] = 0x12ab89dc;
    state.registers[Vm::Acc2] = 0xff;
    uut.setState(state);

    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    // Register to register transfer
    // Pre: %acc1 = 0x59; %wp = 0x0
    REQUIRE( Vm::Success == uut.singleStep() );
    // Post: %acc1 = 0x59; %wp = 0x59
    state = uut.getState();
    REQUIRE( 0x12ab89dc == state.registers[Vm::Wp] );

    // Register to register indirect transfer
    // Pre: %wp = 0x12ab89dc; %acc2 = 0xff; mem[0xff] = 0xff
    REQUIRE( Vm::Success == uut.singleStep() );
    // Post: %wp = 0x12ab89dc; %acc2 = 0xff; mem[0xff:0x104] = 0x12ab89dc
    REQUIRE( 0x12ab89dc == uut.wordAt(0xff) );

    // Register indirect to register transfer
    state = uut.getState();
    state.registers[Vm::Dsp] = 0x0;
    uut.setState(state);
    // Pre: %dsp = 0x0; %acc1 = 0x59; mem[0x0] = 0x20
    REQUIRE( Vm::Success == uut.singleStep() );
    // Post: %dsp = 0x0; %acc1 = 0x20; mem[0x0] = 0x20
    state = uut.getState();
    REQUIRE( 0xd1201420 == state.registers[Vm::Acc1] );

    // Register indirect to register indirect transfer
    state = uut.getState();
    state.registers[Vm::Acc1] = 0x100;
    state.registers[Vm::Acc2] = 0x0;
    uut.setState(state);
    // Pre: %acc1 = 0x100; %acc2 = 0x0; mem[0x0] = 0xd1201420; mem[0x100] = 0xffffffff;
    REQUIRE( Vm::Success == uut.singleStep() );
    // Post: %acc1 = 0x100; %acc2 = 0x0; mem[0x0] = 0xd1201420; mem[0x3] = 0xd1201420;
    REQUIRE( 0xd1201420 == uut.wordAt(0x100) );
}

TEST_CASE("Stack based move operations", "[opcode]") {
    Vm uut;

    SECTION("Copy acc1 to wp indirect with post increment") {
        std::array<uint8_t, 2> testdata = {
            0x22, 0xc   // mov.w [%wp++], %acc1
        };
        uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

        Vm::State state = uut.getState();
        state.registers[Vm::Wp] = 0x10;
        state.registers[Vm::Acc1] = 0x1234;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );

        state = uut.getState();
        REQUIRE( 0x14 == state.registers[Vm::Wp] );
        REQUIRE( 0x1234 == uut.wordAt(0x10) );
    }

    SECTION("Copy acc2 to ip indirect with pre decrement") {
        std::array<uint8_t, 2> testdata = {
            0x22, 0xc5   // mov.w [--%ip], %acc2
        };
        uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

        Vm::State state = uut.getState();
        state.registers[Vm::Ip] = 0x24;
        state.registers[Vm::Acc2] = 0xabcd;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );

        state = uut.getState();
        REQUIRE( 0x20 == state.registers[Vm::Ip] );
        REQUIRE( 0xabcd == uut.wordAt(0x20) );
    }

    SECTION("Copy ip indirect with post increment to wp") {
        std::array<uint8_t, 8> testdata = {
            0x24, 0x8,      // mov.w %wp, [%ip++]
            0x0, 0x0,       // alignment filler
            0x01, 0x23, 0x5a, 0xfa
        };
        uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

        Vm::State state = uut.getState();
        state.registers[Vm::Ip] = 0x4;
        state.registers[Vm::Wp] = 0x0;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );

        state = uut.getState();
        REQUIRE( 0x8 == state.registers[Vm::Ip] );
        REQUIRE( 0xfa5a2301 == state.registers[Vm::Wp] );
    }
}

TEST_CASE("Move label to acc1", "[opcode]") {
    std::array<uint8_t, 5> testdata = {
        0x26, 0x10, 0x41, 0x32, 0x22    // mov %acc1, 0x22324110
    };

    Vm uut;
    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    REQUIRE( Vm::Success == uut.singleStep() );

    Vm::State state = uut.getState();
    REQUIRE( 0x22324110 == state.registers[Vm::Acc1] );
    REQUIRE( 0x5 == state.registers[Vm::Pc] );
}

TEST_CASE("Register indirect jumping", "[opcode]") {
    std::array<uint8_t, 20> testdata = {
        0x60,       // jmp [%ip]
        0x61,       // jmp [%wp]
        0x62,       // jmp [%acc1]
        0x63,       // jmp [%acc2]
        0x10, 0x0, 0x0, 0x0,    // pointed to by %ip
        0x20, 0x0, 0x0, 0x0,    // pointed to by %wp
        0x30, 0x0, 0x0, 0x0,    // pointed to by %acc1
        0x40, 0x0, 0x0, 0x0,    // pointed to by %acc2
    };

    Vm uut;
    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    Vm::State state = uut.getState();
    state.registers[Vm::Ip] = 0x4;
    state.registers[Vm::Wp] = 0x8;
    state.registers[Vm::Acc1] = 0xc;
    state.registers[Vm::Acc2] = 0x10;
    uut.setState(state);

    SECTION("Jumping %ip indirect") {
        state = uut.getState();
        state.registers[Vm::Pc] = 0x0;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );
        state = uut.getState();
        REQUIRE( 0x00000010 == state.registers[Vm::Pc] );
    }

    SECTION("Jumping %wp indirect") {
        state = uut.getState();
        state.registers[Vm::Pc] = 0x1;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );
        state = uut.getState();
        REQUIRE( 0x00000020 == state.registers[Vm::Pc] );
    }

    SECTION("Jumping %acc1 indirect") {
        state = uut.getState();
        state.registers[Vm::Pc] = 0x2;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );
        state = uut.getState();
        REQUIRE( 0x00000030 == state.registers[Vm::Pc] );
    }

    SECTION("Jumping %acc2 indirect") {
        state = uut.getState();
        state.registers[Vm::Pc] = 0x3;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );
        state = uut.getState();
        REQUIRE( 0x00000040 == state.registers[Vm::Pc] );
    }
}

TEST_CASE("Register direct jumping", "[opcode]") {
    std::array<uint8_t, 20> testdata = {
        0x64, 0x07, 0x00, 0x00, 0x00,   // jmp +7
        0x00,       // nop
        0x00,       // nop
        0x00,       // nop (jump target)
    };

    Vm uut;
    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    REQUIRE( Vm::Success == uut.singleStep());

    Vm::State state = uut.getState();
    REQUIRE( 0x00000007 == state.registers[Vm::Pc] );
}

TEST_CASE("Register direct jumping if accumulator is 0", "[opcode]") {
    std::array<uint8_t, 20> testdata = {
        0x65, 0x07, 0x00, 0x00, 0x00,   // jmp +7
        0x00,       // nop
        0x00,       // nop
        0x00,       // nop (jump target)
    };

    Vm uut;
    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    SECTION("Should jump if acc1 is 0") {
        auto state = uut.getState();
        state.registers[Vm::Acc1] = 0x0;
        uut.setState(state);
        
        REQUIRE( Vm::Success == uut.singleStep());

        state = uut.getState();
        REQUIRE( 0x00000007 == state.registers[Vm::Pc] );
    }

    SECTION("Should not jump if acc1 is != 0") {
        auto state = uut.getState();
        state.registers[Vm::Acc1] = 0xff;
        uut.setState(state);
        
        REQUIRE( Vm::Success == uut.singleStep());

        state = uut.getState();
        REQUIRE( 0x00000005 == state.registers[Vm::Pc] );
    }
}

TEST_CASE("Add instruction") {
    std::array<uint8_t, 3> testdata = {
        0x30, 0x01, 0x4,    // add.w %ip, %wp, %acc1
    };

    Vm uut;
    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    auto state = uut.getState();
    state.registers[Vm::Acc1] = 0x562a;
    state.registers[Vm::Wp] = 0x723828;
    state.registers[Vm::Ip] = 0x0;
    uut.setState(state);

    REQUIRE( Vm::Success == uut.singleStep());

    state = uut.getState();
    REQUIRE( (0x562a + 0x723828) == state.registers[Vm::Ip] );
    REQUIRE( 0x3 == state.registers[Vm::Pc] );
}

TEST_CASE("Disassembling") {
    std::array<uint8_t, 51> testdata = {
        0x00,               // nop
        0xff,               // illegal
        0xfe, 0x34, 0x12,   // ifkt 0x1234
        0x60,               // jmp [%ip]
        0x61,               // jmp [%wp]
        0x62,               // jmp [%acc1]
        0x63,               // jmp [%acc2]
        0x64, 0x07, 0x00, 0x00, 0x00,   // jmp 0x7
        0x26, 0x10, 0x41, 0x32, 0x22,   // mov %acc1, 0x22324110
        0x20, 0x14,         // mov.w %wp, %acc1
        0x20, 0xd1,         // mov.w [%acc2], %wp
        0x20, 0x4b,         // mov.w %acc1, [%dsp]
        0x20, 0xcd,         // mov.w [%acc1], [%acc2]
        0x21, 0x14,         // mov.b %wp, %acc1
        0x21, 0xd1,         // mov.b [%acc2], %wp
        0x21, 0x4b,         // mov.b %acc1, [%dsp]
        0x21, 0xcd,         // mov.b [%acc1], [%acc2]
        0x22, 0xc,          // mov.w [%wp++], %acc1
        0x22, 0xc5,         // mov.w [--%ip], %acc2
        0x24, 0x8,          // mov.w %wp, [%ip++]
        0x24, 0xcb,         // mov.w %wp, [--%dsp]
        0x65, 0x07, 0x00, 0x00, 0x00,   // jz 0x7
        0x30, 0x01, 0x4,    // add.w %ip, %wp, %acc1
    };

    Vm uut;
    auto state = uut.getState();

    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    SECTION("Disassembling nop instruction") {
        state.registers[Vm::Pc] = 0;
        uut.setState(state);
        REQUIRE( "nop" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling illegal instruction") {
        state.registers[Vm::Pc] = 1;
        uut.setState(state);
        REQUIRE( "illegal" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling ifkt") {
        state.registers[Vm::Pc] = 2;
        uut.setState(state);
        REQUIRE( "ifkt 0x1234" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling jmp ip indirect") {
        state.registers[Vm::Pc] = 5;
        uut.setState(state);
        REQUIRE( "jmp [%ip]" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling jmp wp indirect") {
        state.registers[Vm::Pc] = 6;
        uut.setState(state);
        REQUIRE( "jmp [%wp]" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling jmp acc1 indirect") {
        state.registers[Vm::Pc] = 7;
        uut.setState(state);
        REQUIRE( "jmp [%acc1]" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling jmp acc2 indirect") {
        state.registers[Vm::Pc] = 8;
        uut.setState(state);
        REQUIRE( "jmp [%acc2]" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling jmp direct") {
        state.registers[Vm::Pc] = 9;
        uut.setState(state);
        REQUIRE( "jmp 0x7" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling jz direct") {
        state.registers[Vm::Pc] = 43;
        uut.setState(state);
        REQUIRE( "jz 0x7" == uut.disassembleAtPc() );
    }

    // ------ mov word instructions -----------------------------------------
    SECTION("Disassembling mov immediate to acc1") {
        state.registers[Vm::Pc] = 14;
        uut.setState(state);
        REQUIRE( "mov %acc1, 0x22324110" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov value from acc1 to wp") {
        state.registers[Vm::Pc] = 19;
        uut.setState(state);
        REQUIRE( "mov.w %wp, %acc1" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov value from wp to acc2 indirect") {
        state.registers[Vm::Pc] = 21;
        uut.setState(state);
        REQUIRE( "mov.w [%acc2], %wp" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov value from dsp indirect to acc1") {
        state.registers[Vm::Pc] = 23;
        uut.setState(state);
        REQUIRE( "mov.w %acc1, [%dsp]" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov value from acc2 indirect to acc1 indirect") {
        state.registers[Vm::Pc] = 25;
        uut.setState(state);
        REQUIRE( "mov.w [%acc1], [%acc2]" == uut.disassembleAtPc() );
    }

    // ------ mov byte instructions -----------------------------------------
    SECTION("Disassembling mov byte value from acc1 to wp") {
        state.registers[Vm::Pc] = 27;
        uut.setState(state);
        REQUIRE( "mov.b %wp, %acc1" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov byte value from wp to acc2 indirect") {
        state.registers[Vm::Pc] = 29;
        uut.setState(state);
        REQUIRE( "mov.b [%acc2], %wp" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov byte value from dsp indirect to acc1") {
        state.registers[Vm::Pc] = 31;
        uut.setState(state);
        REQUIRE( "mov.b %acc1, [%dsp]" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov byte value from acc2 indirect to acc1 indirect") {
        state.registers[Vm::Pc] = 33;
        uut.setState(state);
        REQUIRE( "mov.b [%acc1], [%acc2]" == uut.disassembleAtPc() );
    }

    // ------ stack based mov instructions -----------------------------------
    SECTION("Disassembling mov acc1 to wp indirect with post increment") {
        state.registers[Vm::Pc] = 35;
        uut.setState(state);
        REQUIRE( "mov.w [%wp++], %acc1" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov acc2 to ip indirect with pre decrement") {
        state.registers[Vm::Pc] = 37;
        uut.setState(state);
        REQUIRE( "mov.w [--%ip], %acc2" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov ip indirect with post increment to wp") {
        state.registers[Vm::Pc] = 39;
        uut.setState(state);
        REQUIRE( "mov.w %wp, [%ip++]" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling mov dsp indirect with pre decrement to wp") {
        state.registers[Vm::Pc] = 41;
        uut.setState(state);
        REQUIRE( "mov.w %wp, [--%dsp]" == uut.disassembleAtPc() );
    }

    // ------ add instructions -----------------------------------
    SECTION("Disassembling add with registers") {
        state.registers[Vm::Pc] = 48;
        uut.setState(state);
        REQUIRE( "add.w %ip, %wp, %acc1" == uut.disassembleAtPc() );
    }
}