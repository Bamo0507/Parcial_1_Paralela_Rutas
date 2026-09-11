#include "grafo.h"

#include <cstdio>
#include <stdexcept>

namespace {

std::vector<char> leer_archivo_completo(const std::string& ruta) {
    FILE* archivo = std::fopen(ruta.c_str(), "rb");
    if (archivo == nullptr) {
        throw std::runtime_error("No se pudo abrir " + ruta);
    }
    std::fseek(archivo, 0, SEEK_END);
    long tamano = std::ftell(archivo);
    std::fseek(archivo, 0, SEEK_SET);

    std::vector<char> contenido(tamano);
    size_t leidos = std::fread(contenido.data(), 1, tamano, archivo);
    std::fclose(archivo);
    if (leidos != static_cast<size_t>(tamano)) {
        throw std::runtime_error("Lectura incompleta de " + ruta);
    }
    return contenido;
}

// Lee enteros directamente del buffer en memoria. fscanf por token es ~50x más lento.
class LectorEnteros {
public:
    LectorEnteros(const char* inicio, const char* limite) : cursor(inicio), limite(limite) {}

    long long siguiente() {
        while (cursor < limite && !es_digito(*cursor)) {
            ++cursor;
        }
        if (cursor >= limite) {
            throw std::runtime_error("Archivo truncado: se esperaban más enteros");
        }
        long long valor = 0;
        while (cursor < limite && es_digito(*cursor)) {
            valor = valor * 10 + (*cursor - '0');
            ++cursor;
        }
        return valor;
    }

private:
    const char* cursor;
    const char* limite;

    static bool es_digito(char caracter) {
        return caracter >= '0' && caracter <= '9';
    }
};

}

Grafo cargar_grafo(const std::string& ruta) {
    std::vector<char> contenido = leer_archivo_completo(ruta);
    LectorEnteros lector(contenido.data(), contenido.data() + contenido.size());

    Grafo grafo;
    grafo.cantidad_nodos = static_cast<int>(lector.siguiente());
    grafo.cantidad_aristas = lector.siguiente();

    std::vector<int> origenes(grafo.cantidad_aristas);
    std::vector<int> destinos(grafo.cantidad_aristas);
    for (long long arista = 0; arista < grafo.cantidad_aristas; ++arista) {
        origenes[arista] = static_cast<int>(lector.siguiente());
        destinos[arista] = static_cast<int>(lector.siguiente());
    }

    // El buffer del archivo ya no hace falta: liberarlo baja el pico de memoria ~500 MB
    contenido.clear();
    contenido.shrink_to_fit();

    grafo.indices.assign(grafo.cantidad_nodos + 1, 0);
    for (long long arista = 0; arista < grafo.cantidad_aristas; ++arista) {
        ++grafo.indices[origenes[arista] + 1];
        ++grafo.indices[destinos[arista] + 1];
    }
    for (int nodo = 0; nodo < grafo.cantidad_nodos; ++nodo) {
        grafo.indices[nodo + 1] += grafo.indices[nodo];
    }

    grafo.vecinos.resize(2 * grafo.cantidad_aristas);
    std::vector<long long> posicion_libre(grafo.indices.begin(), grafo.indices.end() - 1);
    for (long long arista = 0; arista < grafo.cantidad_aristas; ++arista) {
        int origen = origenes[arista];
        int destino = destinos[arista];
        grafo.vecinos[posicion_libre[origen]++] = destino;
        grafo.vecinos[posicion_libre[destino]++] = origen;
    }

    return grafo;
}
