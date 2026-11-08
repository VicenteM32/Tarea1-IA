# Tarea 1 de Inteligencia Artificial
## Autor
* **Nombre:** Vicente Miranda Gómez
* **Asignatura:** Inteligencia Artificial
---

## Algoritmos Implementados
* **Búsqueda no informada:** BFS (Anchura) y UCS (Costo Uniforme)
* **Búsqueda informada:** Greedy Best-First y A* con heurística Manhattan
* **Metaheurística bioinspirada:** Algoritmo Genético (selección por torneo, cruce y mutación)
---

### Requisitos:
* python 3.10 o superior
* librerias numpy, pandas y matplotlib

### Desde la carpeta del proyecto:
* main.py: simulación animada de forma básica de una evacuación (el algoritmo se elige con ALGORITMO_A_PROBAR)
* benchmark.py: Ejecuta el experimento completo, tiene como salida resultados_benchmark.csv
* analizar_resultados.py: calcula las estadísticas, los IC bootstrap y las comparaciones pareadas, ademas de generar gráficos visuales

## Instrucciones de Ejecución
El proyecto está escrito en python por lo que no necesita compilación previa. Ejecutar los siguientes comandos desde /Tarea1-IA

### Ejecución de simulación:
```bash
python -m src.main
```
El algoritmo se configura en `src/main.py`, mediante la variable
`ALGORITMO_A_PROBAR`: `bfs`, `ucs`, `greedy`, `astar` o `genetico`

### Prueba rápida de Benchmark:
```bash
python -m scripts.benchmark --hasta 1 --salida resultados/prueba.csv
```

### Experimento completo:
Ejecuta 80 iteraciones por combinación
```bash
python -m scripts.benchmark
```
Los resultados se guardan en `resultados/resultados_benchmark.csv`

Para ejecutar un nuevo experimento en un archivo diferente:
```bash
python -m scripts.benchmark --hasta 80 --salida resultados/nuevo.csv
```

### Análisis:
Análisis para datos incluidos en el proyecto:
```bash
python -m scripts.analizar_resultados
```

Para analizar el experimento nuevo:
```bash
python -m scripts.analizar_resultados resultados/nuevo.csv
```
