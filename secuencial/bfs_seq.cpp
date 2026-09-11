#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "../comun/bfs.h"
#include "../comun/grafo.h"
#include "../comun/nombres.h"

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

double segundos_desde(std::chrono::steady_clock::time_point inicio) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - inicio).count();
}

int main(int cantidad_argumentos, char** argumentos) {
    if (cantidad_argumentos < 4) {
        std::fprintf(stderr, "uso: %s <grafo.txt> <origen> <destino> [nombres.txt]\n", argumentos[0]);
        return 1;
    }
    std::string ruta_grafo = argumentos[1];
    int origen = std::atoi(argumentos[2]);
    int destino = std::atoi(argumentos[3]);

    auto inicio_carga = std::chrono::steady_clock::now();
    Grafo grafo = cargar_grafo(ruta_grafo);
    std::printf("carga: %.2f s  (%d nodos, %lld amistades)\n", segundos_desde(inicio_carga), grafo.cantidad_nodos, grafo.cantidad_aristas);

    if (origen < 0 || origen >= grafo.cantidad_nodos || destino < 0 || destino >= grafo.cantidad_nodos) {
        std::fprintf(stderr, "origen y destino deben estar en [0, %d)\n", grafo.cantidad_nodos);
        return 1;
    }

    auto inicio_bfs = std::chrono::steady_clock::now();
    ResultadoBFS resultado = bfs(grafo, origen, destino);
    double segundos_bfs = segundos_desde(inicio_bfs);

    std::printf("bfs: %.4f s\n", segundos_bfs);
    std::printf("niveles explorados: %d  nodos visitados: %lld\n", resultado.niveles_explorados, resultado.nodos_visitados);

    if (resultado.distancia == -1) {
        std::printf("no hay camino entre %d y %d\n", origen, destino);
        return 0;
    }

    std::printf("distancia: %d\n", resultado.distancia);
    std::vector<std::string> nombres;
    if (cantidad_argumentos >= 5) {
        nombres = cargar_nombres(argumentos[4]);
    }
    for (size_t paso = 0; paso < resultado.camino.size(); ++paso) {
        int nodo = resultado.camino[paso];
        if (nombres.empty()) {
            std::printf("%s%d", paso == 0 ? "" : " -> ", nodo);
        } else {
            std::printf("%s%s (%d)", paso == 0 ? "" : " -> ", nombres[nodo].c_str(), nodo);
        }
    }
    std::printf("\n");
    return 0;
}
