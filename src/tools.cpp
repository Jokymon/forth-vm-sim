#include "tools.h"

bool is_uint32_add_overflow(uint32_t a, uint32_t b)
{
    uint32_t sum = a + b;
    return sum < (a | b);
}