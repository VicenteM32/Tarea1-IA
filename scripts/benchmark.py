"""
Benchmark de la Tarea 1 de IA (Escape de las Torres).

Corre, para cada combinación (mapa x algoritmo), N iteraciones con variaciones
estocásticas: distribución de obstáculos, posición inicial del fuego y posición
inicial del grupo de agentes.

Las instancias son LAS MISMAS para todos los algoritmos: la semilla depende solo
del mapa y del número de iteración. Así los algoritmos se comparan de forma pareada
sobre escenarios idénticos (marco experimental controlado).

Por cada corrida se registra:
  - sobrevivientes / bajas / atrapados (vivos que no alcanzaron a evacuar al
    llegar al límite de turnos)
  - tiempo_despeje: turno en el que el ÚLTIMO sobreviviente alcanzó la salida,
    es decir max(turnos_tomados) entre los agentes que escaparon. Queda vacío si
    nadie logró escapar en esa corrida.
  - cpu_seg: tiempo de CPU consumido por la simulación (indicador del costo
    computacional del algoritmo).

Las corridas se agregan al CSV de salida iteración por iteración y el script es
reanudable: si se interrumpe, al volver a lanzarlo omite lo que ya está en el CSV.

Ejemplos:
    python3 benchmark.py                          # 3 mapas x 5 algoritmos x 80 iteraciones
    python3 benchmark.py --hasta 200              # 200 iteraciones
    python3 benchmark.py --mapa 2 --algo astar --hasta 50 --salida prueba.csv
"""
import argparse
import contextlib
import csv
import io
import os
import random
import sys
import time

from entorno import Entorno
from agente import Agente
from main import simular_evacuacion

# --- Configuración del experimento ---
FILAS = 20
COLUMNAS = 20
N_AGENTES = 12
TURNOS_PROPAGACION_FUEGO = 4
MAX_TURNOS = 300
ITERACIONES_POR_DEFECTO = 80
ALGORITMOS = ('bfs', 'ucs', 'greedy', 'astar', 'genetico')
MAPAS = (1, 2, 3)

NOMBRES_MAPA = {
    1: 'Mapa 1 - Alta densidad (cuello de botella)',
    2: 'Mapa 2 - Media densidad (laberinto corporativo)',
    3: 'Mapa 3 - Baja densidad (dispersión abierta)',
}

CAMPOS = ['tipo_mapa', 'algoritmo', 'iteracion', 'semilla', 'n_agentes',
          'sobrevivientes', 'bajas', 'atrapados', 'tiempo_despeje',
          'turno_final_simulacion', 'cpu_seg']


def semilla_de(tipo_mapa, iteracion):
    return tipo_mapa * 100_000 + iteracion


def posiciones_agentes(n, filas, columnas, rng):
    """Grupo compacto cerca de una esquina, lejos de la salida (esquina opuesta),
    consistente con el escenario de la tarea (un grupo evacuando junto)."""
    region = [(f, c) for f in range(min(6, filas)) for c in range(min(6, columnas))]
    return rng.sample(region, n)


def posicion_fuego_aleatoria(filas, columnas, excluir, rng):
    candidatas = [(f, c) for f in range(filas) for c in range(columnas) if (f, c) not in excluir]
    return rng.choice(candidatas)


def correr_una_iteracion(tipo_mapa, algoritmo, iteracion):
    semilla = semilla_de(tipo_mapa, iteracion)
    rng = random.Random(semilla)
    random.seed(semilla)  # entorno.py y agente.py usan el módulo random global

    posiciones = posiciones_agentes(N_AGENTES, FILAS, COLUMNAS, rng)
    excluir = set(posiciones) | {(FILAS - 1, COLUMNAS - 1)}
    fuego_inicial = posicion_fuego_aleatoria(FILAS, COLUMNAS, excluir, rng)

    entorno = Entorno(FILAS, COLUMNAS, tipo_mapa,
                      posiciones_a_proteger=posiciones,
                      posicion_fuego_inicial=fuego_inicial)
    agentes = [Agente(i, p, entorno.salida) for i, p in enumerate(posiciones)]

    t0 = time.process_time()
    with contextlib.redirect_stdout(io.StringIO()):  # silencia los prints de la simulación
        sobrevivientes, turno_final = simular_evacuacion(
            entorno, agentes, algoritmo_usado=algoritmo,
            turnos_propagacion_fuego=TURNOS_PROPAGACION_FUEGO,
            animar=False, max_turnos=MAX_TURNOS,
        )
    cpu = time.process_time() - t0

    bajas = sum(1 for a in agentes if not a.vivo)
    atrapados = N_AGENTES - sobrevivientes - bajas
    turnos_escape = [a.turnos_tomados for a in agentes if a.escapo]
    tiempo_despeje = max(turnos_escape) if turnos_escape else ''

    return {
        'tipo_mapa': tipo_mapa,
        'algoritmo': algoritmo,
        'iteracion': iteracion,
        'semilla': semilla,
        'n_agentes': N_AGENTES,
        'sobrevivientes': sobrevivientes,
        'bajas': bajas,
        'atrapados': atrapados,
        'tiempo_despeje': tiempo_despeje,
        'turno_final_simulacion': turno_final,
        'cpu_seg': round(cpu, 4),
    }


def main():
    ap = argparse.ArgumentParser(description="Benchmark de algoritmos de evacuación.")
    ap.add_argument('--mapa', type=int, choices=MAPAS, help="solo este mapa (por defecto: los 3)")
    ap.add_argument('--algo', choices=ALGORITMOS, help="solo este algoritmo (por defecto: los 5)")
    ap.add_argument('--desde', type=int, default=0, help="primera iteración (por defecto 0)")
    ap.add_argument('--hasta', type=int, default=ITERACIONES_POR_DEFECTO,
                    help=f"última iteración, exclusiva (por defecto {ITERACIONES_POR_DEFECTO})")
    ap.add_argument('--salida', default='resultados_benchmark.csv', help="CSV de salida")
    args = ap.parse_args()

    mapas = [args.mapa] if args.mapa else list(MAPAS)
    algos = [args.algo] if args.algo else list(ALGORITMOS)

    hechos = set()
    existe = os.path.exists(args.salida) and os.path.getsize(args.salida) > 0
    if existe:
        with open(args.salida, newline='') as f:
            for fila in csv.DictReader(f):
                hechos.add((int(fila['tipo_mapa']), fila['algoritmo'], int(fila['iteracion'])))

    t_ini = time.time()
    with open(args.salida, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CAMPOS, lineterminator='\n')
        if not existe:
            writer.writeheader()
            f.flush()

        for i in range(args.desde, args.hasta):
            for m in mapas:
                for a in algos:
                    if (m, a, i) in hechos:
                        continue
                    writer.writerow(correr_una_iteracion(m, a, i))
                    f.flush()  # no se pierde progreso si el proceso se corta
            if (i + 1) % 10 == 0 or i + 1 == args.hasta:
                print(f"iteración {i + 1}/{args.hasta} completada "
                      f"({time.time() - t_ini:.0f}s)", file=sys.stderr, flush=True)


if __name__ == '__main__':
    main()
