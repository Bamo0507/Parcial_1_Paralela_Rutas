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

### Secuencial

No depende de OpenMP:

```bash
clang++ -std=c++20 -O3 secuencial/bfs_seq.cpp comun/main_bfs.cpp comun/grafo.cpp comun/nombres.cpp -o secuencial/bfs_seq
```

### Paralelo — macOS (Apple Silicon)

Apple Clang no trae OpenMP habilitado por defecto; requiere `libomp`:

```bash
brew install libomp
```

```bash
clang++ -std=c++20 -O3 -Xpreprocessor -fopenmp \
        -I$(brew --prefix libomp)/include \
        -L$(brew --prefix libomp)/lib -lomp \
        paralelo/bfs_par.cpp comun/main_bfs.cpp comun/grafo.cpp comun/nombres.cpp -o paralelo/bfs_par
```

### Paralelo — Linux

```bash
g++ -std=c++20 -O3 -fopenmp paralelo/bfs_par.cpp comun/main_bfs.cpp comun/grafo.cpp comun/nombres.cpp -o paralelo/bfs_par
```

## Ejecución

Ambos binarios reciben el grafo, el usuario origen, el usuario destino y opcionalmente
el archivo de nombres para imprimir el camino con nombres en vez de ids:

```bash
./secuencial/bfs_seq datos/grafo.txt 0 1999999 datos/nombres.txt
```

```bash
OMP_NUM_THREADS=10 OMP_SCHEDULE="dynamic,64" ./paralelo/bfs_par datos/grafo.txt 0 1999999 datos/nombres.txt
```

El paralelo se compila con `schedule(runtime)`, de modo que la estrategia de
scheduling se cambia mediante la variable de entorno `OMP_SCHEDULE` sin recompilar.

### Modo lote (benchmark)

Carga el grafo una sola vez y resuelve todos los pares de un archivo, reportando el
tiempo total por repetición. Es el modo que usan los scripts de `bench/`:

```bash
./secuencial/bfs_seq datos/grafo.txt --lote bench/pares.txt --repeticiones 12
```

```bash
OMP_NUM_THREADS=10 OMP_SCHEDULE="dynamic,64" ./paralelo/bfs_par datos/grafo.txt --lote bench/pares.txt --repeticiones 12
```

