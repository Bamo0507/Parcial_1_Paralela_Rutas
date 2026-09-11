#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <string>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

#include "bfs.h"
#include "grafo.h"
#include "nombres.h"

// Un solo main para ambas versiones: se enlaza con bfs_seq.cpp o con bfs_par.cpp.
//   consulta:  <grafo.txt> <origen> <destino> [nombres.txt]
//   lote: <grafo.txt> --lote <pares.txt> [--repeticiones N]
double segundos_desde(std::chrono::steady_clock::time_point inicio) {
    return std::chrono::duration<double>(std::chrono::steady_clock::now() - inicio).count();
}

void imprimir_configuracion_paralela() {
#ifdef _OPENMP
    omp_sched_t tipo;
    int chunk;
    omp_get_schedule(&tipo, &chunk);
    const char* nombre = "desconocido";
    switch (tipo & ~omp_sched_monotonic) {
        case omp_sched_static: nombre = "static"; break;
        case omp_sched_dynamic: nombre = "dynamic"; break;
        case omp_sched_guided: nombre = "guided"; break;
        case omp_sched_auto: nombre = "auto"; break;
        default: break;
    }
    std::printf("threads: %d  schedule: %s,%d\n", omp_get_max_threads(), nombre, chunk);
#endif
}

bool ids_validos(const Grafo& grafo, int origen, int destino) {
    return origen >= 0 && origen < grafo.cantidad_nodos && destino >= 0 && destino < grafo.cantidad_nodos;
}

int modo_consulta(const Grafo& grafo, int origen, int destino, const char* ruta_nombres) {
    if (!ids_validos(grafo, origen, destino)) {
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
    if (ruta_nombres != nullptr) {
        nombres = cargar_nombres(ruta_nombres);
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

int modo_lote(const Grafo& grafo, const char* ruta_pares, int repeticiones) {
    std::ifstream archivo(ruta_pares);
    if (!archivo) {
        std::fprintf(stderr, "No se pudo abrir %s\n", ruta_pares);
        return 1;
    }
    std::vector<std::pair<int, int>> pares;
    int origen;
    int destino;
    while (archivo >> origen >> destino) {
        if (!ids_validos(grafo, origen, destino)) {
            std::fprintf(stderr, "par inválido en %s: %d %d\n", ruta_pares, origen, destino);
            return 1;
        }
        pares.emplace_back(origen, destino);
    }
    std::printf("pares: %zu\n", pares.size());

    long long suma_distancias = 0;
    for (int repeticion = 1; repeticion <= repeticiones; ++repeticion) {
        suma_distancias = 0;
        auto inicio_lote = std::chrono::steady_clock::now();
        for (const auto& [par_origen, par_destino] : pares) {
            suma_distancias += bfs(grafo, par_origen, par_destino).distancia;
        }
        std::printf("repeticion %d: %.4f s\n", repeticion, segundos_desde(inicio_lote));
        std::fflush(stdout);
    }
    // Permite verificar que secuencial y paralelo dan las mismas distancias sobre el lote
    std::printf("suma_distancias: %lld\n", suma_distancias);
    return 0;
}

int main(int cantidad_argumentos, char** argumentos) {
    if (cantidad_argumentos < 4) {
        std::fprintf(stderr, "uso:\n  %s <grafo.txt> <origen> <destino> [nombres.txt]\n  %s <grafo.txt> --lote <pares.txt> [--repeticiones N]\n", argumentos[0], argumentos[0]);
        return 1;
    }

    auto inicio_carga = std::chrono::steady_clock::now();
    Grafo grafo = cargar_grafo(argumentos[1]);
    std::printf("carga: %.2f s  (%d nodos, %lld amistades)\n", segundos_desde(inicio_carga), grafo.cantidad_nodos, grafo.cantidad_aristas);
    imprimir_configuracion_paralela();

    if (std::strcmp(argumentos[2], "--lote") == 0) {
        int repeticiones = 1;
        if (cantidad_argumentos >= 6 && std::strcmp(argumentos[4], "--repeticiones") == 0) {
            repeticiones = std::atoi(argumentos[5]);
        }
        return modo_lote(grafo, argumentos[3], repeticiones);
    }

    const char* ruta_nombres = cantidad_argumentos >= 5 ? argumentos[4] : nullptr;
    return modo_consulta(grafo, std::atoi(argumentos[2]), std::atoi(argumentos[3]), ruta_nombres);
}
