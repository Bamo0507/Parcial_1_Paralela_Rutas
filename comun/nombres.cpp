#include "nombres.h"

#include <fstream>
#include <stdexcept>

std::vector<std::string> cargar_nombres(const std::string& ruta) {
    std::ifstream archivo(ruta);
    if (!archivo) {
        throw std::runtime_error("No se pudo abrir " + ruta);
    }

    std::vector<std::string> nombres;
    std::string linea;
    while (std::getline(archivo, linea)) {
        size_t separador = linea.find(' ');
        nombres.push_back(linea.substr(separador + 1));
    }
    return nombres;
}
