#include <algorithm>
#include <memory>
#include <vector>

#include <omp.h>

#include "../comun/bfs.h"
#include "../comun/grafo.h"

// Cada contador vive en su propia línea de caché para que las escrituras de distintos
// threads no se invaliden entre sí (false sharing).
struct alignas(64) ContadorPorThread {
    long long valor = 0;
};

// Nivel-sincrónico: la frontera de cada nivel se reparte entre threads con parallel for.
// Cada thread acumula los nodos que descubre en un buffer propio; al cerrar el nivel se
// fusionan con un prefix sum para formar la siguiente frontera.
ResultadoBFS bfs(const Grafo& grafo, int origen, int destino) {
    int cantidad_threads = omp_get_max_threads();
    std::vector<int> distancia(grafo.cantidad_nodos, -1);
    std::vector<int> padre(grafo.cantidad_nodos, -1);
    std::vector<int> frontera(grafo.cantidad_nodos);

    // new int[] sin inicializar: las páginas solo se tocan cuando un thread las usa
    std::vector<std::unique_ptr<int[]>> buffers(cantidad_threads);
    for (auto& buffer : buffers) {
        buffer.reset(new int[grafo.cantidad_nodos]);
    }
    std::vector<ContadorPorThread> descubiertos_por_thread(cantidad_threads);
    std::vector<long long> desplazamientos(cantidad_threads + 1, 0);

    ResultadoBFS resultado;
    distancia[origen] = 0;
    frontera[0] = origen;
    long long tamano_frontera = 1;
    long long tamano_siguiente = 0;
    resultado.nodos_visitados = 1;

    while (tamano_frontera > 0 && distancia[destino] == -1) {
        int nivel_siguiente = resultado.niveles_explorados + 1;

        #pragma omp parallel
        {
            int id_thread = omp_get_thread_num();
            int* buffer = buffers[id_thread].get();
            long long cantidad_local = 0;

            #pragma omp for schedule(runtime) nowait
            for (long long posicion_frontera = 0; posicion_frontera < tamano_frontera; ++posicion_frontera) {
                int actual = frontera[posicion_frontera];
                for (long long posicion = grafo.indices[actual]; posicion < grafo.indices[actual + 1]; ++posicion) {
                    int vecino = grafo.vecinos[posicion];
                    // Lectura atómica relajada: en ARM64 es un load normal, pero evita la race formal
                    // con los CAS de otros threads. Filtra el caso común (ya visitado) sin pagar el CAS.
                    if (__atomic_load_n(&distancia[vecino], __ATOMIC_RELAXED) != -1) {
                        continue;
                    }
                    int esperado = -1;
                    bool gano = __atomic_compare_exchange_n(&distancia[vecino], &esperado, nivel_siguiente, false, __ATOMIC_RELAXED, __ATOMIC_RELAXED);
                    if (gano) {
                        padre[vecino] = actual;
                        buffer[cantidad_local++] = vecino;
                    }
                }
            }

            descubiertos_por_thread[id_thread].valor = cantidad_local;
            #pragma omp barrier

            #pragma omp single
            {
                for (int indice_thread = 0; indice_thread < cantidad_threads; ++indice_thread) {
                    desplazamientos[indice_thread + 1] = desplazamientos[indice_thread] + descubiertos_por_thread[indice_thread].valor;
                }
                tamano_siguiente = desplazamientos[cantidad_threads];
            }

            std::copy(buffer, buffer + cantidad_local, frontera.data() + desplazamientos[id_thread]);
        }

        tamano_frontera = tamano_siguiente;
        resultado.niveles_explorados = nivel_siguiente;
        resultado.nodos_visitados += tamano_frontera;
    }

    if (distancia[destino] == -1) {
        return resultado;
    }

    resultado.distancia = distancia[destino];
    for (int nodo = destino; nodo != -1; nodo = padre[nodo]) {
        resultado.camino.push_back(nodo);
    }
    std::reverse(resultado.camino.begin(), resultado.camino.end());
    return resultado;
}
