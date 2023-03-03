#include <catch2/catch_test_macros.hpp>
#include "tools.h"

TEST_CASE("Overflow in addition is detected") {
    REQUIRE( is_uint32_add_overflow(0xFFFFFFFF, 0xFFFFFFFF));
}

TEST_CASE("Bare overflow in addition is detected") {
    REQUIRE( is_uint32_add_overflow(0x80000000, 0x80000000));
}

TEST_CASE("No-vverflow in addition is detected") {
    REQUIRE_FALSE( is_uint32_add_overflow(0x20, 0x20));
}
