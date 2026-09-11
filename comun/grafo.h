#pragma once

#include <string>
#include <vector>

// Grafo no dirigido en formato CSR: los vecinos del nodo u son vecinos[indices[u] .. indices[u+1]).
struct Grafo {
    int cantidad_nodos = 0;
    long long cantidad_aristas = 0;
    std::vector<long long> indices;
    std::vector<int> vecinos;

    int grado(int nodo) const {
        return static_cast<int>(indices[nodo + 1] - indices[nodo]);
    }
};

Grafo cargar_grafo(const std::string& ruta);
