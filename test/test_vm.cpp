#include <catch2/catch_test_macros.hpp>
#include "vm.h"

TEST_CASE("Generic test", "passing") {
    REQUIRE( true == true );
}

TEST_CASE("Memory access", "Loading VM memory through iterator") {
    std::array<uint8_t, 3> testdata = {0x23, 0x53, 0x61};

    Vm uut;

    uut.loadImageFromIterator(std::begin(testdata), std::end(testdata));

    REQUIRE( uut.memoryAt(0x0) == 0x23 );
    REQUIRE( uut.memoryAt(0x1) == 0x53 );
    REQUIRE( uut.memoryAt(0x2) == 0x61 );
}

TEST_CASE("Register based move instructions", "[opcode]") {
    std::array<uint8_t, 8> testdata = {
        0x21, 0x14,     // movr %wp, %acc1
        0x21, 0xd1,     // movr [%acc2], %wp
        0x21, 0x4b,     // movr %acc1, [%dsp]
        0x21, 0xcd,     // movr [%acc1], [%acc2]
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
    REQUIRE( 0x59 == uut.memoryAt(0xff) );

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
    REQUIRE( 0xd1 == uut.memoryAt(0x0) );
}