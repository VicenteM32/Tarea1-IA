import time
import os
from entorno import Entorno
from agente import Agente


def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')


def imprimir_estado_actual(entorno, agentes, turno):
    limpiar_pantalla()
    print(f"-  TURNO {turno}   -")

    # Marcadores visuales
    simbolos = {0: '.', 1: '█', 2: 'S', 3: 'F'}

    for r in range(entorno.filas):
        fila_str = ""
        for c in range(entorno.columnas):
            # Verificar si hay agentes vivos en esta celda
            agentes_aqui = [a for a in agentes if a.posicion == (r, c) and a.vivo and not a.escapo]

            if agentes_aqui:
                if len(agentes_aqui) > 1:
                    fila_str += f"{len(agentes_aqui)} "
                else:
                    fila_str += "A "
            else:
                valor = entorno.grilla[r, c]
                fila_str += simbolos.get(valor, '?') + " "
        print(fila_str)
    print("-" * 20)
    time.sleep(0.5)  # Pausa de medio segundo para poder ver la animación


def simular_evacuacion(entorno, agentes, algoritmo_usado='bfs', turnos_propagacion_fuego=3,
                        animar=True, max_turnos=1000):
    turno = 0

    if animar:
        imprimir_estado_actual(entorno, agentes, turno)

    while turno < max_turnos:
        activos = [a for a in agentes if a.vivo and not a.escapo]
        if not activos:
            break

        posiciones_actuales = [a.posicion for a in activos]
        entorno.actualizar_ocupacion(posiciones_actuales)

        # Turno de los agentes
        for agente in activos:
            # Check fuego antes de mover
            if entorno.grilla[agente.posicion[0], agente.posicion[1]] == 3:
                agente.vivo = False
                continue

            agente.actuar(entorno, algoritmo=algoritmo_usado)

            # Check fuego después de mover
            if entorno.grilla[agente.posicion[0], agente.posicion[1]] == 3:
                agente.vivo = False

        # Turno del entorno (Fuego)
        if turno % turnos_propagacion_fuego == 0 and turno > 0:
            entorno.propagar_fuego()

        turno += 1

        if animar:
            imprimir_estado_actual(entorno, agentes, turno)

    # Estadísticas finales
    sobrevivientes = sum(1 for a in agentes if a.escapo)
    bajas = sum(1 for a in agentes if not a.vivo)
    atrapados = len(agentes) - sobrevivientes - bajas  # vivos pero sin evacuar al cortar la simulación

    print(f"\n[ RESULTADOS - Algoritmo: {algoritmo_usado.upper()} ]")
    print(f"Simulación finalizada en {turno} turnos.")
    print(f"Sobrevivientes: {sobrevivientes}/{len(agentes)} ({(sobrevivientes/len(agentes))*100:.1f}%)")
    print(f"Bajas: {bajas}")
    if atrapados:
        print(f"Atrapados (no evacuaron antes del límite de {max_turnos} turnos): {atrapados}")
    print()

    return sobrevivientes, turno


if __name__ == "__main__":
    # Configurar los parámetros de prueba
    FILAS = 30
    COLUMNAS = 30
    ALGORITMO_A_PROBAR = 'bfs'  # 'bfs', 'ucs', 'greedy', 'astar' o 'genetico'

    # Posiciones iniciales del grupo de agentes
    posiciones_iniciales = [(0, 0), (0, 1), (1, 0), (1, 1), (0, 2)]

    # Instanciar el entorno
    edificio = Entorno(
        filas=FILAS,
        columnas=COLUMNAS,
        tipo_mapa=3,
        posiciones_a_proteger=posiciones_iniciales,
    )

    # Crear un grupo de agentes en distintas posiciones iniciales
    lista_agentes = []
    for i, pos in enumerate(posiciones_iniciales):
        #edificio.salida ya fue generada al crear el Entorno
        nuevo_agente = Agente(id_agente=i, posicion_inicial=pos, salida=edificio.salida)
        lista_agentes.append(nuevo_agente)

        
    print("Iniciando evacuación...")
    simular_evacuacion(
        entorno=edificio,
        agentes=lista_agentes,
        algoritmo_usado=ALGORITMO_A_PROBAR,
        turnos_propagacion_fuego=4,
        animar=True,  # Cambia a False si solo quieres ver el resultado final rápido
        max_turnos=500,
    )
