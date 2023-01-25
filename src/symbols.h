#ifndef SYMBOLS_H
#define SYMBOLS_H
#include <stdint.h>
#include <string>
#include <tuple>
#include <vector>

class Symbols {
public:
    Symbols();

    void loadFromFile(const std::string& symbol_file_path);
    void addSymbol(const std::string& name, size_t start_address, size_t end_address);

    std::vector<std::string> symbolsAtAddress(size_t address) const;

private:
    std::vector<std::tuple<std::string, size_t, size_t>> intervals;
};

#endif