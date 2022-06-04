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