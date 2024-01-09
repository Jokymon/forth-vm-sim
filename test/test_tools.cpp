#include <catch2/catch_test_macros.hpp>
#include "tools.h"
#include <array>

TEST_CASE("Overflow in addition is detected") {
    REQUIRE( is_uint32_add_overflow(0xFFFFFFFF, 0xFFFFFFFF));
}

TEST_CASE("Bare overflow in addition is detected") {
    REQUIRE( is_uint32_add_overflow(0x80000000, 0x80000000));
}

TEST_CASE("No-overflow in addition is detected") {
    REQUIRE_FALSE( is_uint32_add_overflow(0x20, 0x20));
}

TEST_CASE("Joining strings from a string vector creates a joined string") {
    std::vector<std::string> s_list = {"ananas", "banana", "corn"};
    REQUIRE( join(s_list.begin(), s_list.end(), "/ ")=="ananas/ banana/ corn");
}

TEST_CASE("Join with ',' separator combines strings with a comma") {
    std::array<std::string, 3> s_list{"ananas", "banana", "corn"};
    REQUIRE( join(s_list.begin(), s_list.end(), ",")=="ananas,banana,corn");
}

TEST_CASE("Joining an empty list returns an empty string") {
    std::array<std::string, 0> empty_list;
    REQUIRE( join(empty_list.begin(), empty_list.end(), ",")=="");
}
