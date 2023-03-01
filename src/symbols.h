#ifndef SYMBOLS_H
#define SYMBOLS_H
#include <stdint.h>
#include <string>
#include <vector>

class Symbols {
public:
    Symbols();

    void loadFromFile(const std::string& symbol_file_path);
    void addSymbol(const std::string& name, size_t start_address, size_t end_address);

    std::vector<std::string> symbolsAtAddress(size_t address) const;

private:
    struct Symbol {
        std::string identifier;
        size_t start;
        size_t end;
    };

    std::vector<Symbol> intervals;
};

#endif