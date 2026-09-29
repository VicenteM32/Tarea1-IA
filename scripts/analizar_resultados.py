"""
Análisis de los resultados del benchmark (Tarea 1 de IA - Escape de las Torres).

Lee el CSV generado por benchmark.py y produce:
  - resumen_estadisticas.csv      (una fila por mapa x algoritmo)
  - comparaciones_pareadas.csv    (diferencias de supervivencia entre algoritmos)
  - figuras/*.png                 (gráficos para el informe)
  - datos_informe.json            (todos los números que usa el informe)

Solo se usan las iteraciones completas para los 3 mapas y los 5 algoritmos, de modo
que todas las configuraciones se comparan sobre exactamente las mismas instancias.

Uso: python3 analizar_resultados.py [resultados_benchmark.csv]
"""
import inspect
import json
import os
import re
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import agente as modulo_agente
import benchmark as bm

ARCHIVO = sys.argv[1] if len(sys.argv) > 1 else 'resultados_benchmark.csv'
B = 5000                      # remuestreos bootstrap
rng = np.random.default_rng(2026)

ORDEN = list(bm.ALGORITMOS)   # bfs, ucs, greedy, astar, genetico
ETQ = {'bfs': 'BFS', 'ucs': 'UCS', 'greedy': 'Greedy', 'astar': 'A*', 'genetico': 'Genético'}
MAPAS = {1: 'Mapa 1 (Alta densidad)', 2: 'Mapa 2 (Media densidad)', 3: 'Mapa 3 (Baja densidad)'}
COLORES = {'bfs': '#4C72B0', 'ucs': '#55A868', 'greedy': '#C44E52', 'astar': '#8172B2', 'genetico': '#CCB974'}

os.makedirs('figuras', exist_ok=True)
plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'grid.alpha': 0.3, 'axes.axisbelow': True})

# ---------------------------------------------------------------- datos ----
df = pd.read_csv(ARCHIVO)
df['tiempo_despeje'] = pd.to_numeric(df['tiempo_despeje'], errors='coerce')

# Iteraciones completas (5 algoritmos) en los 3 mapas
cuenta = df.groupby(['tipo_mapa', 'iteracion']).size()
por_iter = {}
for (m, i), n in cuenta.items():
    if n == len(ORDEN):
        por_iter.setdefault(i, set()).add(m)
iters = sorted(i for i, ms in por_iter.items() if len(ms) == len(MAPAS))
df = df[df['iteracion'].isin(iters)].sort_values(['tipo_mapa', 'algoritmo', 'iteracion']).copy()
n_iter = len(iters)
print(f"Iteraciones completas usadas: {n_iter}")
if n_iter == 0:
    sys.exit("Todavía no hay iteraciones completas en el CSV.")


def serie(m, a, col):
    s = df[(df.tipo_mapa == m) & (df.algoritmo == a)].sort_values('iteracion')
    return s[col].to_numpy()


def ic_boot_tasa(surv, agentes):
    idx = rng.integers(0, len(surv), size=(B, len(surv)))
    tasas = surv[idx].sum(axis=1) / agentes[idx].sum(axis=1)
    return [float(x) * 100 for x in np.percentile(tasas, [2.5, 97.5])]


# ---------------------------------------------------- estadísticas por config
filas = []
for m in MAPAS:
    for a in ORDEN:
        surv = serie(m, a, 'sobrevivientes').astype(float)
        agen = serie(m, a, 'n_agentes').astype(float)
        bajas = serie(m, a, 'bajas').sum()
        atrap = serie(m, a, 'atrapados').sum()
        t = pd.Series(serie(m, a, 'tiempo_despeje')).dropna()
        cpu = serie(m, a, 'cpu_seg')
        lo, hi = ic_boot_tasa(surv, agen)
        filas.append({
            'tipo_mapa': m, 'mapa': MAPAS[m], 'algoritmo': a,
            'n_corridas': int(len(surv)),
            'n_agentes_total': int(agen.sum()),
            'tasa_supervivencia': float(surv.sum() / agen.sum() * 100),
            'ic95_lo': lo, 'ic95_hi': hi,
            'bajas_pct': float(bajas / agen.sum() * 100),
            'atrapados_pct': float(atrap / agen.sum() * 100),
            'corridas_sin_sobrevivientes': int((surv == 0).sum()),
            'n_corridas_con_tiempo': int(len(t)),
            'tiempo_media': float(t.mean()) if len(t) else None,
            'tiempo_std': float(t.std(ddof=1)) if len(t) > 1 else None,
            'tiempo_mediana': float(t.median()) if len(t) else None,
            'tiempo_min': int(t.min()) if len(t) else None,
            'tiempo_max': int(t.max()) if len(t) else None,
            'cpu_media_ms': float(cpu.mean() * 1000),
            'cpu_mediana_ms': float(np.median(cpu) * 1000),
        })
resumen = pd.DataFrame(filas)
resumen.to_csv('resumen_estadisticas.csv', index=False)

# ------------------------------------------------ comparaciones pareadas ----
PARES = [('ucs', 'bfs'), ('greedy', 'bfs'), ('astar', 'bfs'), ('genetico', 'bfs'), ('genetico', 'astar')]
pareadas = []
for m in MAPAS:
    for (x, y) in PARES:
        tx = serie(m, x, 'sobrevivientes') / serie(m, x, 'n_agentes')
        ty = serie(m, y, 'sobrevivientes') / serie(m, y, 'n_agentes')
        d = tx - ty
        idx = rng.integers(0, len(d), size=(B, len(d)))
        medias = d[idx].mean(axis=1)
        lo, hi = [float(v) * 100 for v in np.percentile(medias, [2.5, 97.5])]
        pareadas.append({
            'tipo_mapa': m, 'mapa': MAPAS[m], 'comparacion': f"{ETQ[x]} - {ETQ[y]}",
            'dif_media_pp': float(d.mean() * 100), 'ic95_lo': lo, 'ic95_hi': hi,
            'significativa': bool(lo > 0 or hi < 0),
        })
pd.DataFrame(pareadas).to_csv('comparaciones_pareadas.csv', index=False)

# --------------------------------------- instancias sin solución práctica ----
sin_solucion = {}
for m in MAPAS:
    piv = df[df.tipo_mapa == m].pivot(index='iteracion', columns='algoritmo', values='sobrevivientes')
    todos_cero = int((piv[ORDEN] == 0).all(axis=1).sum())
    exactos_cero = int((piv[['bfs', 'ucs', 'astar']] == 0).all(axis=1).sum())
    sin_solucion[m] = {'todos_cero': todos_cero, 'exactos_cero': exactos_cero, 'n': int(len(piv))}

# ------------------------------------------------------------- parámetros ----
firma = inspect.signature(modulo_agente.Agente._buscar_ruta_genetico)
ga = {k: v.default for k, v in firma.parameters.items() if v.default is not inspect._empty}
codigo = inspect.getsource(modulo_agente.Agente._buscar_ruta_genetico)
ga['prob_dirigido'] = float(re.search(r"PROB_DIRIGIDO\s*=\s*([0-9.]+)", codigo).group(1))

datos = {
    'n_iter': n_iter,
    'config': {
        'filas': bm.FILAS, 'columnas': bm.COLUMNAS, 'n_agentes': bm.N_AGENTES,
        'k_fuego': bm.TURNOS_PROPAGACION_FUEGO, 'max_turnos': bm.MAX_TURNOS,
        'densidades': {'1': 0.7, '2': 0.3, '3': 0.1},
    },
    'ga': ga,
    'resumen': json.loads(resumen.to_json(orient='records')),
    'pareadas': pareadas,
    'sin_solucion': {str(k): v for k, v in sin_solucion.items()},
}
with open('datos_informe.json', 'w', encoding='utf-8') as f:
    json.dump(datos, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------- figuras ----
x = np.arange(len(MAPAS))
ancho = 0.15
etq_x = [f"Mapa {m}\n({['Alta', 'Media', 'Baja'][m - 1]} densidad)" for m in MAPAS]


def valores(col):
    return {a: [resumen[(resumen.tipo_mapa == m) & (resumen.algoritmo == a)][col].values[0] for m in MAPAS]
            for a in ORDEN}


# 1) Supervivencia con IC95%
fig, ax = plt.subplots(figsize=(9, 5))
v, lo, hi = valores('tasa_supervivencia'), valores('ic95_lo'), valores('ic95_hi')
for i, a in enumerate(ORDEN):
    err = [np.array(v[a]) - np.array(lo[a]), np.array(hi[a]) - np.array(v[a])]
    ax.bar(x + (i - 2) * ancho, v[a], ancho, yerr=err, capsize=2, label=ETQ[a], color=COLORES[a],
           error_kw={'elinewidth': 1, 'ecolor': '#333333'})
ax.set_ylabel('Tasa de supervivencia (%)')
ax.set_xticks(x); ax.set_xticklabels(etq_x); ax.set_ylim(0, 100)
ax.set_title(f'Tasa de supervivencia por algoritmo y mapa ({n_iter} corridas c/u, IC 95%)')
ax.legend(ncol=5, loc='upper center', bbox_to_anchor=(0.5, -0.12), frameon=False)
fig.tight_layout(); fig.savefig('figuras/supervivencia.png', dpi=150); plt.close(fig)

# 2) Tiempo de despeje (media ± desv. estándar)
fig, ax = plt.subplots(figsize=(9, 5))
med, sd = valores('tiempo_media'), valores('tiempo_std')
for i, a in enumerate(ORDEN):
    ax.bar(x + (i - 2) * ancho, med[a], ancho, yerr=sd[a], capsize=2, label=ETQ[a], color=COLORES[a],
           error_kw={'elinewidth': 1, 'ecolor': '#333333'})
ax.set_ylabel('Turnos hasta el último sobreviviente (media ± desv. estándar)')
ax.set_xticks(x); ax.set_xticklabels(etq_x)
ax.set_title('Tiempo de despeje por algoritmo y mapa')
ax.legend(ncol=5, loc='upper center', bbox_to_anchor=(0.5, -0.12), frameon=False)
fig.tight_layout(); fig.savefig('figuras/tiempo_despeje.png', dpi=150); plt.close(fig)

# 3) Distribución del tiempo de despeje (diagramas de caja)
fig, axes = plt.subplots(1, 3, figsize=(11, 4.3), sharey=True)
for ax, m in zip(axes, MAPAS):
    datos_caja = [pd.Series(serie(m, a, 'tiempo_despeje')).dropna().to_numpy() for a in ORDEN]
    bp = ax.boxplot(datos_caja, tick_labels=[ETQ[a] for a in ORDEN], patch_artist=True,
                    flierprops={'marker': 'o', 'markersize': 3, 'alpha': 0.5},
                    medianprops={'color': 'black'})
    for patch, a in zip(bp['boxes'], ORDEN):
        patch.set_facecolor(COLORES[a]); patch.set_alpha(0.85)
    ax.set_title(MAPAS[m], fontsize=10)
    ax.tick_params(axis='x', labelsize=8)
axes[0].set_ylabel('Turnos hasta el último sobreviviente')
fig.tight_layout(); fig.savefig('figuras/distribucion_tiempo.png', dpi=150); plt.close(fig)

# 4) Costo computacional (CPU, escala logarítmica)
fig, ax = plt.subplots(figsize=(9, 5))
cpu = valores('cpu_media_ms')
for i, a in enumerate(ORDEN):
    ax.bar(x + (i - 2) * ancho, cpu[a], ancho, label=ETQ[a], color=COLORES[a])
ax.set_yscale('log')
ax.set_ylabel('Tiempo de CPU por simulación (ms, escala log)')
ax.set_xticks(x); ax.set_xticklabels(etq_x)
ax.set_title('Costo computacional por algoritmo y mapa')
ax.legend(ncol=5, loc='upper center', bbox_to_anchor=(0.5, -0.12), frameon=False)
fig.tight_layout(); fig.savefig('figuras/costo_computacional.png', dpi=150); plt.close(fig)

# ------------------------------------------------------ resumen por pantalla ----
pd.set_option('display.width', 250)
pd.set_option('display.max_columns', 30)
cols = ['mapa', 'algoritmo', 'n_corridas', 'tasa_supervivencia', 'ic95_lo', 'ic95_hi', 'corridas_sin_sobrevivientes',
        'tiempo_media', 'tiempo_std', 'tiempo_min', 'tiempo_max', 'cpu_media_ms']
print(resumen[cols].round(2).to_string(index=False))
print("\nComparaciones pareadas (pp de supervivencia, IC95%):")
print(pd.DataFrame(pareadas).round(2).to_string(index=False))
print("\nInstancias sin sobrevivientes en ningún algoritmo:", sin_solucion)
print("\nParámetros AG:", ga)
