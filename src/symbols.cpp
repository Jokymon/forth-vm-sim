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
    intervals.emplace_back(name, start_address, end_address);
}

std::vector<std::string> Symbols::symbolsAtAddress(size_t address) const {
    std::vector<std::string> symbols;

    for (const auto &symbol: intervals) {
        if ((address >= std::get<1>(symbol)) && (address <= std::get<2>(symbol))) {
            symbols.push_back(std::get<0>(symbol));
        }
    }

    return symbols;
}
