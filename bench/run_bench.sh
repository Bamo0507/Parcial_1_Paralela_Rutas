#!/usr/bin/env bash
# Benchmark en dos fases: elige el scheduling con el máximo de threads y luego mide el escalamiento con el ganador.

set -euo pipefail

quien=""
repeticiones=12
descartar_primeras=2
ruta_grafo="datos/grafo.txt"
ruta_pares="bench/pares.txt"
lista_schedules="static guided dynamic,1 dynamic,16 dynamic,64 dynamic,256 dynamic,1024"
lista_threads="1 2 4 6 8 10"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --quien) quien="$2"; shift 2 ;;
        --repeticiones) repeticiones="$2"; shift 2 ;;
        --grafo) ruta_grafo="$2"; shift 2 ;;
        --pares) ruta_pares="$2"; shift 2 ;;
        *) echo "argumento desconocido: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$quien" ]]; then
    echo "uso: bench/run_bench.sh --quien <nombre> [--repeticiones 12] [--grafo datos/grafo.txt] [--pares bench/pares.txt]" >&2
    exit 1
fi

directorio_resultados="bench/resultados"
mkdir -p "$directorio_resultados"
archivo_csv="$directorio_resultados/$quien.csv"
archivo_info="$directorio_resultados/${quien}_maquina.txt"
archivo_log="$directorio_resultados/${quien}_salida.log"

if [[ "$(uname)" == "Darwin" ]]; then
    max_threads=$(sysctl -n hw.logicalcpu)
    descripcion_cpu=$(sysctl -n machdep.cpu.brand_string)
else
    max_threads=$(nproc)
    descripcion_cpu=$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs)
fi

{
    echo "quien: $quien"
    echo "fecha: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "sistema: $(uname -srm)"
    echo "cpu: $descripcion_cpu"
    echo "threads maximos: $max_threads"
    echo "compilador: $(clang++ --version 2>/dev/null | head -1 || g++ --version | head -1)"
    echo "grafo: $ruta_grafo"
    echo "pares: $ruta_pares ($(wc -l < "$ruta_pares" | xargs) consultas)"
    echo "repeticiones: $repeticiones (se descartan las primeras $descartar_primeras)"
} | tee "$archivo_info"
echo

echo "quien,version,threads,schedule,repeticion,segundos" > "$archivo_csv"
: > "$archivo_log"
suma_distancias_referencia=""

correr_lote() {
    local version="$1" binario="$2" threads="$3" schedule="$4"
    local salida
    salida=$(OMP_NUM_THREADS="$threads" OMP_SCHEDULE="$schedule" "$binario" "$ruta_grafo" --lote "$ruta_pares" --repeticiones "$repeticiones")
    printf '### %s threads=%s schedule=%s\n%s\n\n' "$version" "$threads" "$schedule" "$salida" >> "$archivo_log"

    echo "$salida" | awk -v quien="$quien" -v version="$version" -v threads="$threads" -v schedule="$schedule" \
        '/^repeticion/ { gsub(":", "", $2); print quien "," version "," threads "," schedule "," $2 "," $3 }' >> "$archivo_csv"

    local suma_distancias
    suma_distancias=$(echo "$salida" | awk '/^suma_distancias/ { print $2 }')
    if [[ -z "$suma_distancias_referencia" ]]; then
        suma_distancias_referencia="$suma_distancias"
    elif [[ "$suma_distancias" != "$suma_distancias_referencia" ]]; then
        echo "ERROR: suma_distancias=$suma_distancias difiere del secuencial ($suma_distancias_referencia)" >&2
        exit 1
    fi

    echo "$salida" | awk -v descartar="$descartar_primeras" \
        '/^repeticion/ { gsub(":", "", $2); if ($2 + 0 > descartar) print $3 }' | sort -n | awk '
        { valores[NR] = $1 }
        END {
            if (NR % 2 == 1) print valores[(NR + 1) / 2]
            else printf "%.4f\n", (valores[NR / 2] + valores[NR / 2 + 1]) / 2
        }'
}

echo "== fase 0: secuencial =="
mediana_secuencial=$(correr_lote secuencial ./secuencial/bfs_seq 1 static)
printf '  mediana: %s s\n\n' "$mediana_secuencial"

echo "== fase 1: scheduling con $max_threads threads =="
mejor_schedule=""
mejor_mediana=""
for schedule in $lista_schedules; do
    mediana=$(correr_lote paralelo ./paralelo/bfs_par "$max_threads" "$schedule")
    printf '  %s mediana: %s s\n' "$schedule" "$mediana"
    if [[ -z "$mejor_mediana" ]] || (( $(echo "$mediana < $mejor_mediana" | bc -l) )); then
        mejor_mediana="$mediana"
        mejor_schedule="$schedule"
    fi
done
printf '  ganador: %s\n\n' "$mejor_schedule"
echo "schedule ganador: $mejor_schedule" >> "$archivo_info"

echo "== fase 2: escalamiento con $mejor_schedule =="
for threads in $lista_threads; do
    if (( threads > max_threads )); then
        continue
    fi
    if [[ "$threads" == "$max_threads" ]]; then
        mediana="$mejor_mediana"
    else
        mediana=$(correr_lote paralelo ./paralelo/bfs_par "$threads" "$mejor_schedule")
    fi
    speedup=$(echo "$mediana_secuencial / $mediana" | bc -l)
    eficiencia=$(echo "$speedup / $threads" | bc -l)
    printf '  %s threads mediana: %s s speedup: %.2f eficiencia: %.2f\n' "$threads" "$mediana" "$speedup" "$eficiencia"
done

echo
echo "resultados en $archivo_csv"
