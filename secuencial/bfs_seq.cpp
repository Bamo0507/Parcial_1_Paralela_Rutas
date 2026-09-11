#include <algorithm>
#include <vector>

#include "../comun/bfs.h"
#include "../comun/grafo.h"

// Nivel-sincrónico: explora la frontera completa de cada nivel antes de pasar al siguiente.
// Al hallar el destino termina el nivel en curso, igual que la versión paralela.
ResultadoBFS bfs(const Grafo& grafo, int origen, int destino) {
    std::vector<int> distancia(grafo.cantidad_nodos, -1);
    std::vector<int> padre(grafo.cantidad_nodos, -1);
    std::vector<int> frontera;
    std::vector<int> siguiente_frontera;
    frontera.reserve(grafo.cantidad_nodos);
    siguiente_frontera.reserve(grafo.cantidad_nodos);

    ResultadoBFS resultado;
    distancia[origen] = 0;
    frontera.push_back(origen);
    resultado.nodos_visitados = 1;
    bool encontrado = origen == destino;

    while (!frontera.empty() && !encontrado) {
        siguiente_frontera.clear();
        int nivel_siguiente = resultado.niveles_explorados + 1;

        for (int actual : frontera) {
            for (long long posicion = grafo.indices[actual]; posicion < grafo.indices[actual + 1]; ++posicion) {
                int vecino = grafo.vecinos[posicion];
                if (distancia[vecino] == -1) {
                    distancia[vecino] = nivel_siguiente;
                    padre[vecino] = actual;
                    siguiente_frontera.push_back(vecino);
                    if (vecino == destino) {
                        encontrado = true;
                    }
                }
            }
        }

        resultado.niveles_explorados = nivel_siguiente;
        resultado.nodos_visitados += static_cast<long long>(siguiente_frontera.size());
        std::swap(frontera, siguiente_frontera);
    }

    if (!encontrado) {
        return resultado;
    }

    resultado.distancia = distancia[destino];
    for (int nodo = destino; nodo != -1; nodo = padre[nodo]) {
        resultado.camino.push_back(nodo);
    }
    std::reverse(resultado.camino.begin(), resultado.camino.end());
    return resultado;
}
