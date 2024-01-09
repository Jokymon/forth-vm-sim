#ifndef TOOLS_H
#define TOOLS_H

#include <stdint.h>
#include <string>
#include <sstream>

bool is_uint32_add_overflow(uint32_t a, uint32_t b);

// C++ join function for strings according to
// https://stackoverflow.com/questions/6097927/is-there-a-way-to-implement-analog-of-pythons-separator-join-in-c
template <typename Iter>
std::string join(Iter begin, Iter end, std::string const& separator)
{
  std::ostringstream result;
  if (begin != end)
    result << *begin++;
  while (begin != end)
    result << separator << *begin++;
  return result.str();
}

#endif