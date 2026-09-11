"""Genera las gráficas de scheduling, speedup y eficiencia a partir de los CSV de bench/resultados/."""

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")

ORDEN_SCHEDULES = ["static", "guided", "dynamic,1", "dynamic,16", "dynamic,64", "dynamic,256", "dynamic,1024"]
ESTILO_POR_PERSONA = [
    {"color": "#2a78d6", "marcador": "o"},
    {"color": "#eb6834", "marcador": "s"},
]
COLOR_TEXTO = "#3a3a38"
COLOR_GRILLA = "#d9d9d6"
COLOR_REFERENCIA = "#8a8a86"
P_CORES_M4 = 4

parser = argparse.ArgumentParser(description="Gráficas de speedup y eficiencia.")
parser.add_argument("--resultados", type=Path, default=Path("bench/resultados"))
parser.add_argument("--salida", type=Path, default=Path("docs/graficas"))
parser.add_argument("--tabla", type=Path, default=Path("docs/tabla_resultados.md"))
parser.add_argument("--descartar", type=int, default=2, help="repeticiones de warm-up que no se consideran")
argumentos = parser.parse_args()
argumentos.salida.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 10,
    "text.color": COLOR_TEXTO,
    "axes.labelcolor": COLOR_TEXTO,
    "axes.edgecolor": COLOR_GRILLA,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.color": COLOR_TEXTO,
    "ytick.color": COLOR_TEXTO,
    "grid.color": COLOR_GRILLA,
    "grid.linewidth": 0.6,
    "legend.frameon": False,
})


def cargar_mediciones(directorio, descartar):
    mediciones = defaultdict(list)
    for ruta in sorted(directorio.glob("*.csv")):
        with open(ruta, newline="") as archivo:
            lector = csv.reader(archivo)
            next(lector)
            for fila in lector:
                # Corridas viejas guardaron "dynamic,64" sin comillas y la coma partió el campo en dos
                if len(fila) == 7:
                    fila = fila[:3] + [f"{fila[3]},{fila[4]}"] + fila[5:]
                quien, version, threads, schedule, repeticion, segundos = fila
                if int(repeticion) <= descartar:
                    continue
                mediciones[(quien, version, int(threads), schedule)].append(float(segundos))
    return mediciones


def resumir(valores):
    return {
        "mediana": float(np.median(valores)),
        "cuartil_inferior": float(np.percentile(valores, 25)),
        "cuartil_superior": float(np.percentile(valores, 75)),
    }


def resumir_por_persona(mediciones):
    personas = {}
    for (quien, version, threads, schedule), valores in mediciones.items():
        persona = personas.setdefault(quien, {"secuencial": None, "scheduling": {}, "escalamiento": {}, "schedule_ganador": None})
        resumen = resumir(valores)
        if version == "secuencial":
            persona["secuencial"] = resumen
            continue
        persona["scheduling"].setdefault(schedule, {})[threads] = resumen
        persona["escalamiento"].setdefault(schedule, {})[threads] = resumen

    # El ganador de la fase 1 es el único schedule medido con más de un conteo de threads
    for persona in personas.values():
        for schedule, por_threads in persona["escalamiento"].items():
            if len(por_threads) > 1:
                persona["schedule_ganador"] = schedule
        max_threads = max(threads for por_threads in persona["scheduling"].values() for threads in por_threads)
        persona["max_threads"] = max_threads
        persona["scheduling"] = {schedule: por_threads[max_threads] for schedule, por_threads in persona["scheduling"].items() if max_threads in por_threads}
        persona["escalamiento"] = dict(sorted(persona["escalamiento"][persona["schedule_ganador"]].items()))
    return personas


def speedup_con_rango(secuencial, paralelo):
    return {
        "valor": secuencial["mediana"] / paralelo["mediana"],
        "inferior": secuencial["mediana"] / paralelo["cuartil_superior"],
        "superior": secuencial["mediana"] / paralelo["cuartil_inferior"],
    }


def graficar_scheduling(personas, ruta):
    figura, ejes = plt.subplots(1, len(personas), figsize=(5.5 * len(personas), 4), sharey=False)
    ejes = np.atleast_1d(ejes)
    limite_x = max(resumen["cuartil_superior"] for persona in personas.values() for resumen in persona["scheduling"].values()) * 1.22
    for eje, (quien, persona), estilo in zip(ejes, personas.items(), ESTILO_POR_PERSONA):
        schedules = [schedule for schedule in ORDEN_SCHEDULES if schedule in persona["scheduling"]]
        medianas = [persona["scheduling"][schedule]["mediana"] for schedule in schedules]
        errores_inferiores = [medianas[indice] - persona["scheduling"][schedule]["cuartil_inferior"] for indice, schedule in enumerate(schedules)]
        errores_superiores = [persona["scheduling"][schedule]["cuartil_superior"] - medianas[indice] for indice, schedule in enumerate(schedules)]
        posiciones = np.arange(len(schedules))
        eje.barh(posiciones, medianas, height=0.55, color=estilo["color"], xerr=[errores_inferiores, errores_superiores], error_kw={"ecolor": COLOR_TEXTO, "elinewidth": 1, "capsize": 3})
        for posicion, schedule, mediana in zip(posiciones, schedules, medianas):
            eje.text(persona["scheduling"][schedule]["cuartil_superior"] + limite_x * 0.012, posicion, f"{mediana:.2f} s", va="center", fontsize=9)
        eje.set_yticks(posiciones, schedules)
        eje.invert_yaxis()
        eje.set_xlim(0, limite_x)
        eje.set_xlabel("mediana del lote de 100 consultas (s)")
        eje.set_title(f"{quien} · {persona['max_threads']} threads · ganador: {persona['schedule_ganador']}", fontsize=10)
        eje.grid(axis="x")
        eje.set_axisbelow(True)
    figura.suptitle("Fase 1: estrategia de scheduling (OMP_SCHEDULE)", fontsize=12)
    figura.tight_layout()
    figura.savefig(ruta, dpi=160)
    plt.close(figura)


def graficar_curvas(personas, ruta, metrica):
    figura, eje = plt.subplots(figsize=(7, 4.5))
    max_threads_global = max(persona["max_threads"] for persona in personas.values())
    for indice_persona, ((quien, persona), estilo) in enumerate(zip(personas.items(), ESTILO_POR_PERSONA)):
        threads = list(persona["escalamiento"].keys())
        speedups = [speedup_con_rango(persona["secuencial"], persona["escalamiento"][cantidad]) for cantidad in threads]
        if metrica == "speedup":
            valores = [speedup["valor"] for speedup in speedups]
            inferiores = [speedup["inferior"] for speedup in speedups]
            superiores = [speedup["superior"] for speedup in speedups]
        else:
            valores = [speedup["valor"] / cantidad for speedup, cantidad in zip(speedups, threads)]
            inferiores = [speedup["inferior"] / cantidad for speedup, cantidad in zip(speedups, threads)]
            superiores = [speedup["superior"] / cantidad for speedup, cantidad in zip(speedups, threads)]
        eje.fill_between(threads, inferiores, superiores, color=estilo["color"], alpha=0.12, linewidth=0)
        eje.plot(threads, valores, color=estilo["color"], marker=estilo["marcador"], markersize=6, linewidth=2, label=f"{quien} ({persona['schedule_ganador']})")
        desplazamiento_vertical = 7 if indice_persona == 0 else -7
        eje.annotate(f"{valores[-1]:.2f}", (threads[-1], valores[-1]), textcoords="offset points", xytext=(7, desplazamiento_vertical), va="center", fontsize=9, color=estilo["color"])

    if metrica == "speedup":
        eje.plot([1, max_threads_global], [1, max_threads_global], color=COLOR_REFERENCIA, linestyle="--", linewidth=1, label="ideal (lineal)")
        eje.set_ylabel("speedup = t_secuencial / t_paralelo")
        eje.set_title("Fase 2: speedup vs. threads", fontsize=12)
    else:
        eje.axhline(1.0, color=COLOR_REFERENCIA, linestyle="--", linewidth=1, label="ideal (100 %)")
        eje.set_ylabel("eficiencia = speedup / threads")
        eje.set_ylim(0, 1.1)
        eje.set_title("Fase 2: eficiencia vs. threads", fontsize=12)

    eje.axvline(P_CORES_M4, color=COLOR_REFERENCIA, linestyle=":", linewidth=1)
    limite_inferior, limite_superior = eje.get_ylim()
    altura_texto = limite_superior * 0.97 if metrica == "eficiencia" else limite_inferior + (limite_superior - limite_inferior) * 0.03
    eje.text(P_CORES_M4 + 0.1, altura_texto, "fin de los P-cores del M4", fontsize=8, color=COLOR_REFERENCIA, va="top" if metrica == "eficiencia" else "bottom")
    eje.set_xlabel("threads (OMP_NUM_THREADS)")
    eje.set_xticks(sorted({cantidad for persona in personas.values() for cantidad in persona["escalamiento"]}))
    eje.grid(axis="y")
    eje.set_axisbelow(True)
    eje.legend(loc="upper left" if metrica == "speedup" else "lower left")
    figura.tight_layout()
    figura.savefig(ruta, dpi=160)
    plt.close(figura)


def escribir_tabla(personas, ruta):
    lineas = ["# Resultados del benchmark", ""]
    for quien, persona in personas.items():
        lineas += [f"## {quien}", "", f"Secuencial: mediana {persona['secuencial']['mediana']:.3f} s sobre el lote de 100 consultas.", ""]
        lineas += [f"### Scheduling con {persona['max_threads']} threads", "", "| OMP_SCHEDULE | mediana (s) | Q1 (s) | Q3 (s) | speedup |", "|---|---|---|---|---|"]
        for schedule in ORDEN_SCHEDULES:
            if schedule not in persona["scheduling"]:
                continue
            resumen = persona["scheduling"][schedule]
            marca = " **(ganador)**" if schedule == persona["schedule_ganador"] else ""
            lineas.append(f"| {schedule}{marca} | {resumen['mediana']:.3f} | {resumen['cuartil_inferior']:.3f} | {resumen['cuartil_superior']:.3f} | {persona['secuencial']['mediana'] / resumen['mediana']:.2f} |")
        lineas += ["", f"### Escalamiento con {persona['schedule_ganador']}", "", "| threads | mediana (s) | Q1 (s) | Q3 (s) | speedup | eficiencia |", "|---|---|---|---|---|---|"]
        for threads, resumen in persona["escalamiento"].items():
            speedup = speedup_con_rango(persona["secuencial"], resumen)["valor"]
            lineas.append(f"| {threads} | {resumen['mediana']:.3f} | {resumen['cuartil_inferior']:.3f} | {resumen['cuartil_superior']:.3f} | {speedup:.2f} | {speedup / threads:.2f} |")
        lineas.append("")
    ruta.write_text("\n".join(lineas), encoding="utf-8")


mediciones = cargar_mediciones(argumentos.resultados, argumentos.descartar)
if not mediciones:
    raise SystemExit(f"No hay CSV en {argumentos.resultados}")
personas = resumir_por_persona(mediciones)

graficar_scheduling(personas, argumentos.salida / "scheduling.png")
graficar_curvas(personas, argumentos.salida / "speedup.png", "speedup")
graficar_curvas(personas, argumentos.salida / "eficiencia.png", "eficiencia")
escribir_tabla(personas, argumentos.tabla)

for quien, persona in personas.items():
    speedup_maximo = max(speedup_con_rango(persona["secuencial"], resumen)["valor"] for resumen in persona["escalamiento"].values())
    print(f"{quien}: secuencial {persona['secuencial']['mediana']:.2f} s, ganador {persona['schedule_ganador']}, speedup máximo {speedup_maximo:.2f}")
print(f"gráficas en {argumentos.salida}/, tabla en {argumentos.tabla}")
