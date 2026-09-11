# Paralelink

Consultoría de optimización de software

## Integrantes

- Bryan Alberto Martínez Orellana - 23542
- Adriana Sophia Palacios Contreras - 23044

## Problema asignado

**Problema 4 — Búsqueda de Ruta Mínima en Grafos.**

Dado el mapa de una red social con millones de usuarios (nodos) y amistades (aristas),
encontrar el camino más corto de conexiones entre un Usuario X y un Usuario Y.
Las amistades no tienen peso, y la distribución de grados es fuertemente desbalanceada:
la mayoría de usuarios tiene unos pocos amigos, mientras un puñado tiene decenas de miles.

## Estructura del repositorio

```
generador/     Generador del grafo sintético (Python + numpy)
datos/         Grafo generado — NO versionado, se regenera (ver abajo)
comun/         Carga del grafo a memoria en formato CSR, compartida por ambas versiones
secuencial/    BFS secuencial — algoritmo base
paralelo/      BFS paralelizado con OpenMP
bench/         Scripts de medición y generación de gráficas
docs/          Reportes, gráficas y análisis de datos
```

## Requisitos

- Python 3.11 o superior
- Compilador C++ con soporte OpenMP y C++20
- ~2 GB libres en disco y al menos 8 GB de RAM

## Preparación

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Generación de los datos

El grafo **no está versionado**: pesa alrededor de 530 MB y GitHub rechaza el push de
cualquier archivo mayor a 100 MB. Lo que se versiona es el generador, no su salida.

Como el generador es determinista, ambos integrantes obtienen un grafo idéntico
usando la misma semilla:

```bash
python generador/generador.py --seed 123 --salida datos/
```

Produce en `datos/`:

- `grafo.txt` — cabecera `N M`, luego una amistad por línea `u v` con `u < v`
- `nombres.txt` — una persona por línea: `id nombre apellido apellido`
- `meta.json` — parámetros de generación y estadísticas del grafo resultante

Con la semilla 123: 2,000,000 nodos, 37,276,447 amistades, grado medio 37, grado máximo 33,532.

## Compilación

### macOS (Apple Silicon)

Apple Clang no trae OpenMP habilitado por defecto; requiere `libomp`:

```bash
brew install libomp
```

```bash
clang++ -std=c++20 -O3 -Xpreprocessor -fopenmp \
        -I$(brew --prefix libomp)/include \
        -L$(brew --prefix libomp)/lib -lomp \
        paralelo/bfs_par.cpp comun/grafo.cpp -o paralelo/bfs_par
```

### Linux

```bash
g++ -std=c++20 -O3 -fopenmp paralelo/bfs_par.cpp comun/grafo.cpp -o paralelo/bfs_par
```

## Ejecución

```bash
OMP_NUM_THREADS=10 OMP_SCHEDULE="dynamic,64" ./paralelo/bfs_par datos/grafo.txt
```

Ambos binarios se compilan con `schedule(runtime)`, de modo que la estrategia de
scheduling se cambia mediante la variable de entorno `OMP_SCHEDULE` sin recompilar.
