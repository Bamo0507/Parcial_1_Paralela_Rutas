"""Genera el lote fijo de consultas origen-destino que usan todas las mediciones."""

import argparse
import json
from pathlib import Path

import numpy as np

parser = argparse.ArgumentParser(description="Genera pares origen-destino para el benchmark.")
parser.add_argument("--seed", type=int, default=123)
parser.add_argument("--cantidad", type=int, default=100)
parser.add_argument("--meta", type=Path, default=Path("datos/meta.json"), help="para leer la cantidad de nodos del grafo")
parser.add_argument("--salida", type=Path, default=Path("bench/pares.txt"))
argumentos = parser.parse_args()

with open(argumentos.meta, encoding="utf-8") as archivo:
    cantidad_nodos = json.load(archivo)["nodos"]

generador_aleatorio = np.random.default_rng(argumentos.seed)
with open(argumentos.salida, "w") as archivo:
    escritos = 0
    while escritos < argumentos.cantidad:
        origen, destino = generador_aleatorio.integers(0, cantidad_nodos, size=2)
        if origen == destino:
            continue
        archivo.write(f"{origen} {destino}\n")
        escritos += 1

print(f"{escritos} pares escritos en {argumentos.salida}")
