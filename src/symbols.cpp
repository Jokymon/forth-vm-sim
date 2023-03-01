#include "symbols.h"
#include <csv.hpp>

Symbols::Symbols() {
}

void Symbols::loadFromFile(const std::string& symbol_file_path) {
    csv::CSVReader reader(symbol_file_path);
    
    for (const csv::CSVRow& row: reader) {
        std::string symbol_name = row[0].get<>();
        size_t start_address = row[1].get<size_t>();
        size_t end_address = row[2].get<size_t>();

        addSymbol(symbol_name, start_address, end_address);
    }
}

void Symbols::addSymbol(const std::string& name, size_t start_address, size_t end_address) {
    intervals.emplace_back(Symbol{name, start_address, end_address});
}

std::vector<std::string> Symbols::symbolsAtAddress(size_t address) const {
    std::vector<std::string> symbols;

    for (const auto &symbol: intervals) {
        if ((address >= symbol.start) && (address < symbol.end)) {
            symbols.push_back(symbol.identifier);
        }
    }

    return symbols;
}
