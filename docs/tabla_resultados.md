# Resultados del benchmark

## Adriana

Secuencial: mediana 7.389 s sobre el lote de 100 consultas.

### Scheduling con 10 threads

| OMP_SCHEDULE | mediana (s) | Q1 (s) | Q3 (s) | speedup |
|---|---|---|---|---|
| static | 3.038 | 2.929 | 3.184 | 2.43 |
| guided | 2.690 | 2.649 | 2.750 | 2.75 |
| dynamic,1 | 3.441 | 3.395 | 3.530 | 2.15 |
| dynamic,16 | 2.558 | 2.490 | 2.649 | 2.89 |
| dynamic,64 | 2.580 | 2.525 | 2.612 | 2.86 |
| dynamic,256 **(ganador)** | 2.484 | 2.457 | 2.531 | 2.97 |
| dynamic,1024 | 2.591 | 2.544 | 2.614 | 2.85 |

### Escalamiento con dynamic,256

| threads | mediana (s) | Q1 (s) | Q3 (s) | speedup | eficiencia |
|---|---|---|---|---|---|
| 1 | 7.471 | 7.446 | 7.493 | 0.99 | 0.99 |
| 2 | 3.902 | 3.886 | 3.909 | 1.89 | 0.95 |
| 4 | 2.783 | 2.728 | 2.815 | 2.66 | 0.66 |
| 6 | 2.608 | 2.583 | 2.647 | 2.83 | 0.47 |
| 8 | 2.503 | 2.484 | 2.522 | 2.95 | 0.37 |
| 10 | 2.484 | 2.457 | 2.531 | 2.97 | 0.30 |

## Bryan

Secuencial: mediana 8.245 s sobre el lote de 100 consultas.

### Scheduling con 10 threads

| OMP_SCHEDULE | mediana (s) | Q1 (s) | Q3 (s) | speedup |
|---|---|---|---|---|
| static | 3.195 | 3.180 | 3.301 | 2.58 |
| guided | 3.035 | 2.995 | 3.107 | 2.72 |
| dynamic,1 | 3.857 | 3.795 | 3.921 | 2.14 |
| dynamic,16 | 3.044 | 2.982 | 3.063 | 2.71 |
| dynamic,64 **(ganador)** | 2.910 | 2.901 | 2.927 | 2.83 |
| dynamic,256 | 3.024 | 2.974 | 3.067 | 2.73 |
| dynamic,1024 | 3.065 | 3.006 | 3.122 | 2.69 |

### Escalamiento con dynamic,64

| threads | mediana (s) | Q1 (s) | Q3 (s) | speedup | eficiencia |
|---|---|---|---|---|---|
| 1 | 8.660 | 8.594 | 8.734 | 0.95 | 0.95 |
| 2 | 4.557 | 4.521 | 4.618 | 1.81 | 0.90 |
| 4 | 2.968 | 2.937 | 3.004 | 2.78 | 0.69 |
| 6 | 2.986 | 2.942 | 3.089 | 2.76 | 0.46 |
| 8 | 3.014 | 2.948 | 3.079 | 2.74 | 0.34 |
| 10 | 2.910 | 2.901 | 2.927 | 2.83 | 0.28 |
