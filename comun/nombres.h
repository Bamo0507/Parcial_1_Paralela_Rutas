#pragma once

#include <string>
#include <vector>

// Lee nombres.txt: posición i del vector = nombre completo del usuario con id i.
std::vector<std::string> cargar_nombres(const std::string& ruta);
