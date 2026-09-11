"""Genera una red social sintética con grados desbalanceados: grafo.txt, nombres.txt y meta.json."""

import argparse
import json
import time
from pathlib import Path

import numpy as np

DIRECTORIO_SCRIPT = Path(__file__).resolve().parent

# Fuertemente sesgada a propósito: así se ve una red social real y así aparece el
# desbalance de carga que plantea el problema (usuarios con 2 amigos vs. 20,000).
BUCKETS = [
    ("unidades", 0.8000, 1, 9),
    ("decenas", 0.1750, 10, 99),
    ("centenas", 0.0230, 100, 999),
    ("miles", 0.0019, 1000, 9999),
    ("decenas_de_miles", 0.0001, 10000, 50000),
]

FILAS_POR_BLOQUE = 1_000_000


def cargar_lista(ruta):
    with open(ruta, encoding="utf-8") as archivo:
        return [linea.strip() for linea in archivo if linea.strip()]


def generar_nombres(generador_aleatorio, cantidad_nodos, nombres, apellidos):
    # Cada combinación (nombre, apellido1, apellido2) tiene un índice único; muestrear
    # índices sin reemplazo garantiza nombres únicos sin verificar colisiones.
    cantidad_apellidos = len(apellidos)
    combinaciones_posibles = len(nombres) * cantidad_apellidos * cantidad_apellidos
    if cantidad_nodos > combinaciones_posibles:
        raise SystemExit(
            f"Se pidieron {cantidad_nodos:,} nodos pero solo hay {combinaciones_posibles:,} nombres únicos posibles."
        )

    indices_combinacion = generador_aleatorio.choice(combinaciones_posibles, size=cantidad_nodos, replace=False)
    indices_nombre = indices_combinacion // (cantidad_apellidos * cantidad_apellidos)
    indices_apellido_paterno = (indices_combinacion // cantidad_apellidos) % cantidad_apellidos
    indices_apellido_materno = indices_combinacion % cantidad_apellidos
    return indices_nombre, indices_apellido_paterno, indices_apellido_materno


def asignar_grados(generador_aleatorio, cantidad_nodos):
    probabilidades = np.array([fraccion for _, fraccion, _, _ in BUCKETS])
    probabilidades = probabilidades / probabilidades.sum()
    bucket_por_nodo = generador_aleatorio.choice(len(BUCKETS), size=cantidad_nodos, p=probabilidades)

    grados = np.empty(cantidad_nodos, dtype=np.int64)
    for indice_bucket, (_, _, grado_minimo, grado_maximo) in enumerate(BUCKETS):
        pertenece = bucket_por_nodo == indice_bucket
        grados[pertenece] = generador_aleatorio.integers(grado_minimo, grado_maximo + 1, size=int(pertenece.sum()))

    # Relevante solo en grafos de prueba chicos, donde un bucket puede pedir más amigos que personas hay
    np.minimum(grados, cantidad_nodos - 1, out=grados)

    # El modelo de configuración empareja stubs de a dos: la suma debe ser par
    if grados.sum() % 2 == 1:
        grados[0] += 1

    return bucket_por_nodo, grados


def cablear(generador_aleatorio, cantidad_nodos, grados):
    # Modelo de configuración: cada nodo aparece grados[nodo] veces en la lista de stubs,
    # se revuelve y se emparejan consecutivos.
    stubs = np.repeat(np.arange(cantidad_nodos, dtype=np.int32), grados)
    generador_aleatorio.shuffle(stubs)
    extremo_origen = stubs[0::2]
    extremo_destino = stubs[1::2]

    sin_auto_loop = extremo_origen != extremo_destino
    auto_loops = int((~sin_auto_loop).sum())
    extremo_origen = extremo_origen[sin_auto_loop]
    extremo_destino = extremo_destino[sin_auto_loop]

    # Clave entera única por par no dirigido: permite deduplicar con np.unique y deja el resultado ordenado
    extremo_menor = np.minimum(extremo_origen, extremo_destino).astype(np.int64)
    extremo_mayor = np.maximum(extremo_origen, extremo_destino).astype(np.int64)
    claves = extremo_menor * cantidad_nodos + extremo_mayor
    claves_unicas = np.unique(claves)
    duplicadas = int(claves.size - claves_unicas.size)

    extremo_menor = (claves_unicas // cantidad_nodos).astype(np.int32)
    extremo_mayor = (claves_unicas % cantidad_nodos).astype(np.int32)
    return extremo_menor, extremo_mayor, auto_loops, duplicadas


def escribir_grafo(ruta, cantidad_nodos, extremo_menor, extremo_mayor):
    cantidad_aristas = extremo_menor.size
    aristas = np.column_stack((extremo_menor, extremo_mayor))
    with open(ruta, "w") as archivo:
        archivo.write(f"{cantidad_nodos} {cantidad_aristas}\n")
        for inicio in range(0, cantidad_aristas, FILAS_POR_BLOQUE):
            np.savetxt(archivo, aristas[inicio:inicio + FILAS_POR_BLOQUE], fmt="%d %d")


def escribir_nombres(ruta, nombres, apellidos, indices_nombre, indices_apellido_paterno, indices_apellido_materno):
    with open(ruta, "w", encoding="utf-8") as archivo:
        for identificador in range(len(indices_nombre)):
            nombre = nombres[indices_nombre[identificador]]
            apellido_paterno = apellidos[indices_apellido_paterno[identificador]]
            apellido_materno = apellidos[indices_apellido_materno[identificador]]
            archivo.write(f"{identificador} {nombre} {apellido_paterno} {apellido_materno}\n")


def escribir_meta(ruta, semilla, cantidad_nodos, cantidad_aristas, bucket_por_nodo, extremo_menor, extremo_mayor, auto_loops, duplicadas, segundos):
    grado_real = np.bincount(extremo_menor, minlength=cantidad_nodos) + np.bincount(extremo_mayor, minlength=cantidad_nodos)
    nodos_por_bucket = np.bincount(bucket_por_nodo, minlength=len(BUCKETS))

    meta = {
        "semilla": semilla,
        "nodos": cantidad_nodos,
        "aristas": cantidad_aristas,
        "grado_medio": round(float(grado_real.mean()), 2),
        "grado_max": int(grado_real.max()),
        "grado_min": int(grado_real.min()),
        "buckets": {
            nombre_bucket: {
                "rango": [grado_minimo, grado_maximo],
                "nodos": int(nodos_por_bucket[indice_bucket]),
                "porcentaje": round(100.0 * nodos_por_bucket[indice_bucket] / cantidad_nodos, 4),
            }
            for indice_bucket, (nombre_bucket, _, grado_minimo, grado_maximo) in enumerate(BUCKETS)
        },
        "descartadas": {"auto_loops": auto_loops, "duplicadas": duplicadas},
        "segundos_generacion": round(segundos, 1),
    }
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(meta, archivo, indent=2, ensure_ascii=False)
        archivo.write("\n")
    return meta


parser = argparse.ArgumentParser(description="Genera una red social sintética con grados desbalanceados.")
parser.add_argument("--seed", type=int, default=123, help="semilla del generador (default: 123)")
parser.add_argument("--nodos", type=int, default=2_000_000, help="cantidad de usuarios (default: 2,000,000)")
parser.add_argument("--salida", type=Path, default=Path("datos"), help="directorio de salida (default: datos/)")
argumentos = parser.parse_args()

argumentos.salida.mkdir(parents=True, exist_ok=True)
generador_aleatorio = np.random.default_rng(argumentos.seed)
cantidad_nodos = argumentos.nodos
tiempo_inicio = time.perf_counter()


def reportar_fase(mensaje):
    print(f"[{time.perf_counter() - tiempo_inicio:.1f}s] {mensaje}", flush=True)


nombres = cargar_lista(DIRECTORIO_SCRIPT / "nombres.txt")
apellidos = cargar_lista(DIRECTORIO_SCRIPT / "apellidos.txt")
reportar_fase(f"listas cargadas: {len(nombres)} nombres y {len(apellidos)} apellidos, {len(nombres) * len(apellidos) ** 2:,} combinaciones")

indices_nombre, indices_apellido_paterno, indices_apellido_materno = generar_nombres(generador_aleatorio, cantidad_nodos, nombres, apellidos)
reportar_fase(f"{cantidad_nodos:,} usuarios con nombre único")

bucket_por_nodo, grados = asignar_grados(generador_aleatorio, cantidad_nodos)
reportar_fase(f"grados asignados: {grados.sum():,} stubs")

extremo_menor, extremo_mayor, auto_loops, duplicadas = cablear(generador_aleatorio, cantidad_nodos, grados)
cantidad_aristas = extremo_menor.size
reportar_fase(f"cableado: {cantidad_aristas:,} amistades (descartadas {auto_loops:,} auto-loops y {duplicadas:,} duplicadas)")

escribir_grafo(argumentos.salida / "grafo.txt", cantidad_nodos, extremo_menor, extremo_mayor)
reportar_fase(f"escrito {argumentos.salida / 'grafo.txt'}")

escribir_nombres(argumentos.salida / "nombres.txt", nombres, apellidos, indices_nombre, indices_apellido_paterno, indices_apellido_materno)
reportar_fase(f"escrito {argumentos.salida / 'nombres.txt'}")

meta = escribir_meta(argumentos.salida / "meta.json", argumentos.seed, cantidad_nodos, cantidad_aristas, bucket_por_nodo, extremo_menor, extremo_mayor, auto_loops, duplicadas, time.perf_counter() - tiempo_inicio)
reportar_fase(f"escrito {argumentos.salida / 'meta.json'}")

print()
print(f"nodos: {meta['nodos']:,}")
print(f"aristas: {meta['aristas']:,}")
print(f"grado medio: {meta['grado_medio']}")
print(f"grado máximo: {meta['grado_max']:,}")
for nombre_bucket, informacion in meta["buckets"].items():
    print(f"{nombre_bucket}: {informacion['nodos']:,} nodos ({informacion['porcentaje']}%)")
