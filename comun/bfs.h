#pragma once

#include <vector>

#include "grafo.h"

struct ResultadoBFS {
    int distancia = -1;
    std::vector<int> camino;
    int niveles_explorados = 0;
    long long nodos_visitados = 0;
};

// Camino más corto de origen a destino. Cada versión (secuencial, paralela) implementa esta firma.
ResultadoBFS bfs(const Grafo& grafo, int origen, int destino);
