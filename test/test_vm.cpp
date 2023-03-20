#include <catch2/catch_test_macros.hpp>
#include "vm.h"
#include "vm_memory.h"

CATCH_REGISTER_ENUM(Vm::Result,
    Vm::Result::Success,
    Vm::Result::Finished,
    Vm::Result::Error,
    Vm::Result::IllegalInstruction
)


TEST_CASE("Loading VM memory at initialization", "[memory]") {
    Memory uut = {0x23, 0x53, 0x61};

    REQUIRE( uut[0x0] == 0x23 );
    REQUIRE( uut[0x1] == 0x53 );
    REQUIRE( uut[0x2] == 0x61 );
}

TEST_CASE("Loading VM memory through iterator", "[memory]") {
    std::array<uint8_t, 3> test_data = {0x23, 0x53, 0x61};
    Memory uut;
    uut.loadImageFromIterator(test_data.begin(), test_data.end());

    REQUIRE( uut[0x0] == 0x23 );
    REQUIRE( uut[0x1] == 0x53 );
    REQUIRE( uut[0x2] == 0x61 );
}

TEST_CASE("Illegal instructions return IllegalInstruction", "[opcode]") {
    Memory testdata = {
        0xfd            // just take come opcode that so far has no meaning ;-)
    };

    Vm uut{testdata};

    REQUIRE( Vm::IllegalInstruction == uut.singleStep() );
}

TEST_CASE("Register based move bytes instructions", "[opcode]") {
    Memory testdata = {
        0x21, 0x14,     // mov.b %wp, %acc1
        0x21, 0xd1,     // mov.b [%acc2], %wp
        0x21, 0x4b,     // mov.b %acc1, [%dsp]
        0x21, 0xcd,     // mov.b [%acc1], [%acc2]
    };

    Vm uut{testdata};

    auto state = uut.getState();
    state.registers[Vm::Acc1] = 0x59;
    state.registers[Vm::Acc2] = 0xff;
    uut.setState(state);

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
    REQUIRE( 0x59 == testdata[0xff] );

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
    REQUIRE( 0xd1 == testdata[0x0] );
}

TEST_CASE("Register based move words instructions", "[opcode]") {
    Memory testdata = {
        0x20, 0x14,     // mov.w %wp, %acc1
        0x20, 0xd1,     // mov.w [%acc2], %wp
        0x20, 0x4b,     // mov.w %acc1, [%dsp]
        0x20, 0xcd,     // mov.w [%acc1], [%acc2]
    };

    Vm uut{testdata};

    auto state = uut.getState();
    state.registers[Vm::Acc1] = 0x12ab89dc;
    state.registers[Vm::Acc2] = 0xff;
    uut.setState(state);

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
    REQUIRE( 0x12ab89dc == testdata.get32(0xff) );

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
    REQUIRE( 0xd1201420 == testdata.get32(0x100) );
}

TEST_CASE("Stack based move operations", "[opcode]") {
    Memory testdata;
    Vm uut{testdata};

    SECTION("Copy acc1 to wp indirect with post increment") {
        testdata = {
            0x22, 0xc   // mov.w [%wp++], %acc1
        };

        Vm::State state = uut.getState();
        state.registers[Vm::Wp] = 0x10;
        state.registers[Vm::Acc1] = 0x1234;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );

        state = uut.getState();
        REQUIRE( 0x14 == state.registers[Vm::Wp] );
        REQUIRE( 0x1234 == testdata.get32(0x10) );
    }

    SECTION("Copy acc2 to ip indirect with pre decrement") {
        testdata = {
            0x22, 0xc5   // mov.w [--%ip], %acc2
        };

        Vm::State state = uut.getState();
        state.registers[Vm::Ip] = 0x24;
        state.registers[Vm::Acc2] = 0xabcd;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );

        state = uut.getState();
        REQUIRE( 0x20 == state.registers[Vm::Ip] );
        REQUIRE( 0xabcd == testdata.get32(0x20) );
    }

    SECTION("Copy ip indirect with post increment to wp") {
        testdata = {
            0x24, 0x8,      // mov.w %wp, [%ip++]
            0x0, 0x0,       // alignment filler
            0x01, 0x23, 0x5a, 0xfa
        };

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
    Memory testdata = {
        0x26, 0x10, 0x41, 0x32, 0x22    // mov %acc1, 0x22324110
    };

    Vm uut{testdata};

    REQUIRE( Vm::Success == uut.singleStep() );

    Vm::State state = uut.getState();
    REQUIRE( 0x22324110 == state.registers[Vm::Acc1] );
    REQUIRE( 0x5 == state.registers[Vm::Pc] );
}

TEST_CASE("Register indirect jumping", "[opcode]") {
    Memory testdata = {
        0x60,       // jmp [%ip]
        0x61,       // jmp [%wp]
        0x62,       // jmp [%rsp]
        0x63,       // jmp [%dsp]
        0x64,       // jmp [%acc1]
        0x65,       // jmp [%acc2]
        0x10, 0x0, 0x0, 0x0,    // pointed to by %ip
        0x20, 0x0, 0x0, 0x0,    // pointed to by %wp
        0x30, 0x0, 0x0, 0x0,    // pointed to by %rsp
        0x40, 0x0, 0x0, 0x0,    // pointed to by %dsp
        0x50, 0x0, 0x0, 0x0,    // pointed to by %acc1
        0x60, 0x0, 0x0, 0x0,    // pointed to by %acc2
    };

    Vm uut{testdata};

    Vm::State state = uut.getState();
    state.registers[Vm::Ip] = 6;
    state.registers[Vm::Wp] = 10;
    state.registers[Vm::Rsp] = 14;
    state.registers[Vm::Dsp] = 18;
    state.registers[Vm::Acc1] = 22;
    state.registers[Vm::Acc2] = 26;
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

    SECTION("Jumping %rsp indirect") {
        state = uut.getState();
        state.registers[Vm::Pc] = 0x2;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );
        state = uut.getState();
        REQUIRE( 0x00000030 == state.registers[Vm::Pc] );
    }

    SECTION("Jumping %dsp indirect") {
        state = uut.getState();
        state.registers[Vm::Pc] = 0x3;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );
        state = uut.getState();
        REQUIRE( 0x00000040 == state.registers[Vm::Pc] );
    }

    SECTION("Jumping %acc1 indirect") {
        state = uut.getState();
        state.registers[Vm::Pc] = 0x4;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );
        state = uut.getState();
        REQUIRE( 0x00000050 == state.registers[Vm::Pc] );
    }

    SECTION("Jumping %acc2 indirect") {
        state = uut.getState();
        state.registers[Vm::Pc] = 0x5;
        uut.setState(state);

        REQUIRE( Vm::Success == uut.singleStep() );
        state = uut.getState();
        REQUIRE( 0x00000060 == state.registers[Vm::Pc] );
    }
}

TEST_CASE("Register direct jumping", "[opcode]") {
    Memory testdata = {
        0x70, 0x07, 0x00, 0x00, 0x00,   // jmp +7
        0x00,       // nop
        0x00,       // nop
        0x00,       // nop (jump target)
    };

    Vm uut{testdata};

    REQUIRE( Vm::Success == uut.singleStep());

    Vm::State state = uut.getState();
    REQUIRE( 0x00000007 == state.registers[Vm::Pc] );
}

TEST_CASE("Register direct jumping if accumulator is 0", "[opcode]") {
    Memory testdata = {
        0x71, 0x07, 0x00, 0x00, 0x00,   // jz +7
        0x00,       // nop
        0x00,       // nop
        0x00,       // nop (jump target)
    };

    Vm uut{testdata};

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

TEST_CASE("Register direct jumping based on carry flag", "[opcode]") {
    Memory testdata = {
        0x32, 0x44, 0x5,                // sub %acc1, %acc1, %acc2
        0x72, 0x0a, 0x00, 0x00, 0x00,   // jc +7
        0x00,       // nop
        0x00,       // nop
        0x00,       // nop (jump target)
    };

    Vm uut{testdata};

    SECTION("Should jump if carry is set") {
        auto state = uut.getState();
        state.registers[Vm::Acc1] = 0x0;
        state.registers[Vm::Acc2] = 0x10;
        uut.setState(state);
        
        REQUIRE( Vm::Success == uut.singleStep());  // sub
        REQUIRE( Vm::Success == uut.singleStep());  // jc

        state = uut.getState();
        REQUIRE( 0x0000000a == state.registers[Vm::Pc] );
    }

    SECTION("Should not jump if carry is cleared") {
        auto state = uut.getState();
        state.registers[Vm::Acc1] = 0x7f;
        state.registers[Vm::Acc2] = 0x0;
        uut.setState(state);
        
        REQUIRE( Vm::Success == uut.singleStep());  // sub
        REQUIRE( Vm::Success == uut.singleStep());  // jc

        state = uut.getState();
        REQUIRE( 0x00000008 == state.registers[Vm::Pc] );
    }
}

TEST_CASE("Add instruction") {
    Memory testdata = {
        0x30, 0x01, 0x4,    // add.w %ip, %wp, %acc1
    };

    Vm uut{testdata};

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

TEST_CASE("Sub instruction") {
    Memory testdata = {
        0x32, 0x01, 0x4,    // sub.w %ip, %wp, %acc1
    };

    Vm uut{testdata};

    auto state = uut.getState();
    state.registers[Vm::Acc1] = 0x562a;
    state.registers[Vm::Wp] = 0x723828;
    state.registers[Vm::Ip] = 0x0;
    uut.setState(state);

    REQUIRE( Vm::Success == uut.singleStep());

    state = uut.getState();
    REQUIRE( (0x723828 - 0x562a) == state.registers[Vm::Ip] );
    REQUIRE( 0x3 == state.registers[Vm::Pc] );
}

TEST_CASE("Xor instruction") {
    Memory testdata = {
        0x38, 0x01, 0x4,    // xor.w %ip, %wp, %acc1
    };

    Vm uut{testdata};

    auto state = uut.getState();
    state.registers[Vm::Acc1] = 0x562a;
    state.registers[Vm::Wp] = 0x723828;
    state.registers[Vm::Ip] = 0x0;
    uut.setState(state);

    REQUIRE( Vm::Success == uut.singleStep());

    state = uut.getState();
    REQUIRE( (0x723828 ^ 0x562a) == state.registers[Vm::Ip] );
    REQUIRE( 0x3 == state.registers[Vm::Pc] );
}

TEST_CASE("Sra instruction with signed value") {
    Memory testdata = {
        0x3c, 0x65,    // sra.w %dsp, #0x5
    };

    Vm uut{testdata};

    auto state = uut.getState();
    state.registers[Vm::Dsp] = 0x80000000;
    uut.setState(state);

    REQUIRE( Vm::Success == uut.singleStep());

    state = uut.getState();
    REQUIRE( 0xfc000000 == state.registers[Vm::Dsp] );
    REQUIRE( 0x2 == state.registers[Vm::Pc] );
}

TEST_CASE("Sra instruction with unsigned value") {
    Memory testdata = {
        0x3c, 0x64,    // sra.w %dsp, #0x4
    };

    Vm uut{testdata};

    auto state = uut.getState();
    state.registers[Vm::Dsp] = 0x60000000;
    uut.setState(state);

    REQUIRE( Vm::Success == uut.singleStep());

    state = uut.getState();
    REQUIRE( 0x06000000 == state.registers[Vm::Dsp] );
    REQUIRE( 0x2 == state.registers[Vm::Pc] );
}

TEST_CASE("Disassembling") {
    Memory testdata = {
        0x00,               // nop
        0xff,               // illegal
        0xfe, 0x34, 0x12,   // ifkt 0x1234
        0x60,               // jmp [%ip]
        0x61,               // jmp [%wp]
        0x64,               // jmp [%acc1]
        0x65,               // jmp [%acc2]
        0x70, 0x07, 0x00, 0x00, 0x00,   // jmp 0x7
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
        0x71, 0x07, 0x00, 0x00, 0x00,   // jz 0x7
        0x30, 0x01, 0x4,    // add.w %ip, %wp, %acc1
        0x32, 0x01, 0x4,    // sub.w %ip, %wp, %acc1
        0x38, 0x01, 0x4,    // xor.w %ip, %wp, %acc1
        0x3c, 0x65          // sra.w %dsp, #5
    };

    Vm uut{testdata};
    auto state = uut.getState();

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

    // ------ ALU instructions -----------------------------------
    SECTION("Disassembling add with registers") {
        state.registers[Vm::Pc] = 48;
        uut.setState(state);
        REQUIRE( "add.w %ip, %wp, %acc1" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling sub with registers") {
        state.registers[Vm::Pc] = 51;
        uut.setState(state);
        REQUIRE( "sub.w %ip, %wp, %acc1" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling xor with registers") {
        state.registers[Vm::Pc] = 54;
        uut.setState(state);
        REQUIRE( "xor.w %ip, %wp, %acc1" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling sra") {
        state.registers[Vm::Pc] = 57;
        uut.setState(state);
        REQUIRE( "sra.w %dsp, 0x5" == uut.disassembleAtPc() );
    }
}

TEST_CASE("Detailed disassembly", "[disassembly]") {
    Memory testdata;

    SECTION("Jump conditionally, jc") {
        testdata = {
            0x72, 0x15, 0x00, 0x00, 0x00,   // jc 0x15
        };
        Vm uut{testdata};

        REQUIRE( "jc 0x15" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling jmp rsp indirect") {
        testdata = {
            0x62   // jmp [%rsp]
        };
        Vm uut{testdata};

        REQUIRE( "jmp [%rsp]" == uut.disassembleAtPc() );
    }

    SECTION("Disassembling jmp dsp indirect") {
        testdata = {
            0x63   // jmp [%dsp]
        };
        Vm uut{testdata};

        REQUIRE( "jmp [%dsp]" == uut.disassembleAtPc() );
    }
}