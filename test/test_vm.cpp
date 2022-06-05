#include <catch2/catch_test_macros.hpp>
#include "vm.h"

TEST_CASE("Generic test", "passing") {
    REQUIRE( true == true );
}

TEST_CASE("Memory access", "Loading VM memory through iterator") {
    std::array<uint8_t, 3> testdata = {0x23, 0x53, 0x61};

    Vm uut;

    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    REQUIRE( uut.byteAt(0x0) == 0x23 );
    REQUIRE( uut.byteAt(0x1) == 0x53 );
    REQUIRE( uut.byteAt(0x2) == 0x61 );
}

TEST_CASE("Register based move bytes instructions", "[opcode]") {
    std::array<uint8_t, 8> testdata = {
        0x21, 0x14,     // movr.b %wp, %acc1
        0x21, 0xd1,     // movr.b [%acc2], %wp
        0x21, 0x4b,     // movr.b %acc1, [%dsp]
        0x21, 0xcd,     // movr.b [%acc1], [%acc2]
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
        0x20, 0x14,     // movr.w %wp, %acc1
        0x20, 0xd1,     // movr.w [%acc2], %wp
        0x20, 0x4b,     // movr.w %acc1, [%dsp]
        0x20, 0xcd,     // movr.w [%acc1], [%acc2]
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
