import heapq
import itertools
import random

class Agente:
    def __init__(self, id_agente, posicion_inicial, salida):
        self.id = id_agente
        self.posicion = posicion_inicial
        self.salida = salida
        self.ruta_planeada = []  # lista para almacenar el camino restante hacia la salida
        self.vivo = True
        self.escapo = False 
        self.turnos_tomados = 0

        if self.posicion == self.salida:
            # si el agente nace exactamente en la salida, se marca como escapado de inmediato
            self.escapo = True

    def necesita_replanificar(self, entorno):
        # Verifica si el agente necesita replanificar su ruta debido a cambios en el entorno
        if not self.ruta_planeada:
            return True  # si no hay ruta planeada, necesita planificar
        proximo_paso = self.ruta_planeada[0]
        # Si el próximo paso quedó bloqueado, la ruta ya no es válida
        if entorno.grilla[proximo_paso[0], proximo_paso[1]] in (1, 3):
            return True

        return False  # La ruta sigue siendo válida

    def actuar(self, entorno, algoritmo='bfs'):
        # Decide qué hacer en este turno
        if not self.vivo or self.escapo:
            return  # no hace nada si el agente no está vivo o escapó

        if self.posicion == self.salida:
            self.escapo = True
            return

        if self.necesita_replanificar(entorno):
            if algoritmo == 'bfs':
                self.ruta_planeada = self._buscar_ruta_bfs(entorno)
            elif algoritmo == 'ucs':
                self.ruta_planeada = self._buscar_ruta_ucs(entorno)
            elif algoritmo == 'greedy':
                self.ruta_planeada = self._buscar_ruta_greedy(entorno)
            elif algoritmo == 'astar':
                self.ruta_planeada = self._buscar_ruta_astar(entorno)
            elif algoritmo == 'genetico':
                self.ruta_planeada = self._buscar_ruta_genetico(entorno)
            else:
                raise ValueError(f"Algoritmo de búsqueda desconocido: {algoritmo!r}")

        # Ejecuta la acción
        if self.ruta_planeada:
            proximo_paso = self.ruta_planeada.pop(0)

            if entorno.grilla[proximo_paso[0], proximo_paso[1]] not in (1, 3):
                self.posicion = proximo_paso

            self.turnos_tomados += 1

            if self.posicion == self.salida:
                self.escapo = True
                print(f"Agente {self.id} ha escapado en {self.turnos_tomados} turnos.")

    @staticmethod
    def _distancia_manhattan(a, b):
        """Heurística admisible para esta grilla: como los agentes solo se mueven en horizontal/vertical
        y el costo mínimo real de cada paso es 1, la distancia Manhattan nunca sobreestima el costo
        real restante hasta la salida."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


    # vvv BÚSQUEDA NO INFORMADA vvv

    def _buscar_ruta_bfs(self, entorno):
        from collections import deque

        fila_inicio, col_inicio = self.posicion

        if self.posicion == self.salida:
            return []  # ya está en la salida

        #Cola para BFS que almacena (coord actual, ruta hasta ahora)
        frontera = deque([((fila_inicio, col_inicio), [])])
        explorados = set()
        explorados.add((fila_inicio, col_inicio))

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Arriba, Abajo, Izquierda, Derecha

        while frontera:
            (fila_actual, col_actual), ruta_actual = frontera.popleft()

            if (fila_actual, col_actual) == self.salida:
                return ruta_actual  # Retorna la ruta encontrada

            for df, dc in movimientos:
                f_nueva, c_nueva = fila_actual + df, col_actual + dc

                #Si no ha sido explorado y no es un muro ni fuego
                if 0 <= f_nueva < entorno.filas and 0 <= c_nueva < entorno.columnas:
                    vecino = (f_nueva, c_nueva)

                    if vecino not in explorados and entorno.grilla[f_nueva, c_nueva] not in (1, 3):
                        explorados.add(vecino)
                        nueva_ruta = list(ruta_actual)
                        nueva_ruta.append(vecino)
                        frontera.append((vecino, nueva_ruta))

        return []  # No se encontró ruta

    def _buscar_ruta_ucs(self, entorno):
        # Retorna una lista de coordenadas desde el próximo paso hasta la salida
        fila_inicio, col_inicio = self.posicion

        if self.posicion == self.salida:
            return []  # Ya está en la salida

        # si el costo se repite, se agrega un contador monótono para desempatar
        contador = itertools.count()

        # Cola de prioridad que almacena (costo acumulado, desempate, coord actual, ruta hasta ahora)
        frontera = []
        heapq.heappush(frontera, (0, next(contador), (fila_inicio, col_inicio), []))

        #Diccionario para mantener registro del costo mínimo para llegar a cada nodo explorado
        explorador_costo = {(fila_inicio, col_inicio): 0}

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Arriba, Abajo, Izquierda, Derecha

        while frontera:
            costo_actual, _, (fila_actual, col_actual), ruta_actual = heapq.heappop(frontera)

            if (fila_actual, col_actual) == self.salida: # test Objetivo
                return ruta_actual  # Retorna la ruta encontrada

            if costo_actual > explorador_costo.get((fila_actual, col_actual), float('inf')):
                continue  # Ya encontramos un camino más barato a este nodo

            for df, dc in movimientos:
                f_nueva, c_nueva = fila_actual + df, col_actual + dc
                # Verifica límites
                if 0 <= f_nueva < entorno.filas and 0 <= c_nueva < entorno.columnas:
                    vecino = (f_nueva, c_nueva)

                    costo_paso = entorno.obtener_costo(f_nueva, c_nueva)
                    if costo_paso != float('inf'):  # Si es transitable
                        nuevo_costo = costo_actual + costo_paso

                        if vecino not in explorador_costo or nuevo_costo < explorador_costo[vecino]:
                            explorador_costo[vecino] = nuevo_costo
                            nueva_ruta = list(ruta_actual)
                            nueva_ruta.append(vecino)
                            heapq.heappush(frontera, (nuevo_costo, next(contador), vecino, nueva_ruta))

        return []  # No se encontró ruta



    # vvv BÚSQUEDA INFORMADA vvv

    def _buscar_ruta_greedy(self, entorno):

        fila_inicio, col_inicio = self.posicion

        if self.posicion == self.salida:
            return []

        contador = itertools.count()
        frontera = []
        h_inicio = self._distancia_manhattan((fila_inicio, col_inicio), self.salida)
        heapq.heappush(frontera, (h_inicio, next(contador), (fila_inicio, col_inicio), []))
        explorados = {(fila_inicio, col_inicio)}

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while frontera:
            _, _, (fila_actual, col_actual), ruta_actual = heapq.heappop(frontera)

            if (fila_actual, col_actual) == self.salida:
                return ruta_actual

            for df, dc in movimientos:
                f_nueva, c_nueva = fila_actual + df, col_actual + dc
                if 0 <= f_nueva < entorno.filas and 0 <= c_nueva < entorno.columnas:
                    vecino = (f_nueva, c_nueva)

                    if vecino not in explorados and entorno.grilla[f_nueva, c_nueva] not in (1, 3):
                        explorados.add(vecino)
                        h = self._distancia_manhattan(vecino, self.salida)
                        nueva_ruta = list(ruta_actual)
                        nueva_ruta.append(vecino)
                        heapq.heappush(frontera, (h, next(contador), vecino, nueva_ruta))

        return []  # no se encontró ruta

    def _buscar_ruta_astar(self, entorno):
        # A*: f(n) = g(n) + h(n), g(n) es el mismo costo de congestión que usa UCS

        fila_inicio, col_inicio = self.posicion

        if self.posicion == self.salida:
            return []

        contador = itertools.count()
        frontera = []
        h_inicio = self._distancia_manhattan((fila_inicio, col_inicio), self.salida)
        # Tupla: (f=g+h, desempate, g acumulado, coord actual, ruta hasta ahora)
        heapq.heappush(frontera, (h_inicio, next(contador), 0, (fila_inicio, col_inicio), []))

        mejor_costo = {(fila_inicio, col_inicio): 0}

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        while frontera:
            _, _, costo_actual, (fila_actual, col_actual), ruta_actual = heapq.heappop(frontera)

            if (fila_actual,col_actual) == self.salida:
                return ruta_actual

            if costo_actual > mejor_costo.get((fila_actual,col_actual), float('inf')):
                continue

            for df, dc in movimientos:
                f_nueva, c_nueva = fila_actual + df, col_actual + dc
                if 0 <= f_nueva < entorno.filas and 0 <= c_nueva < entorno.columnas:
                    vecino = (f_nueva, c_nueva)

                    costo_paso = entorno.obtener_costo(f_nueva, c_nueva)
                    if costo_paso != float('inf'):
                        nuevo_costo = costo_actual + costo_paso

                        if vecino not in mejor_costo or nuevo_costo < mejor_costo[vecino]:
                            mejor_costo[vecino] = nuevo_costo
                            h = self._distancia_manhattan(vecino, self.salida)
                            nueva_ruta = list(ruta_actual)
                            nueva_ruta.append(vecino)
                            heapq.heappush(
                                frontera,
                                (nuevo_costo + h, next(contador), nuevo_costo, vecino, nueva_ruta),
                            )

        return []  # No se encontró ruta



    # vvv ALGORITMO GENÉTICO vvv
    

    def _buscar_ruta_genetico(self, entorno, tam_poblacion=50, generaciones=80,
                               prob_cruce=0.85, prob_mutacion=0.15, tam_torneo=3):
        """Metaheurística bioinspirada para planificar la ruta hacia la salida.
        La idea central se basa en:
        1. genera muchas rutas posibles
        2. evalua cual es mejor
        3. combina las mejores rutas
        4. muta algunas 
        se itera el procedimiento
        """
        ACCIONES = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]  # arriba, abajo, izq, der, esperar

        if self.posicion == self.salida:
            return []

        dist_inicial = self._distancia_manhattan(self.posicion, self.salida)
        longitud_cromosoma = min(max(15, dist_inicial * 3), (entorno.filas + entorno.columnas) * 2)
        longitud_cromosoma = max(longitud_cromosoma, 2)

        PENALIZACION_NO_LLEGAR = 10_000
        PENALIZACION_MOV_INVALIDO = 25
        PROB_DIRIGIDO = 0.6  # probabilidad de sesgar un gen hacia la salida al crear un individuo

        # Instantánea del entorno para esta planificación
        filas, columnas = entorno.filas, entorno.columnas
        salida = self.salida
        INF = float('inf')
        costo_celda = [
            [entorno.obtener_costo(f, c) for c in range(columnas)]
            for f in range(filas)
        ]
        costo_celda = [[(int(v) if v != INF else INF) for v in fila] for fila in costo_celda]

        def crear_individuo():
            """Genera un cromosoma mezclando exploración aleatoria con una caminata sesgada hacia la salida. 
            en cada paso, con probabilidad PROB_DIRIGIDO se elige una dirección valida que reduce la distancia Manhattan
            a la salida. El resto de las veces se elige una acción cualquiera al azar. Es una inicialización
            heurística típica en AG, no se reemplaza la evolución (selección, cruce, mutación y elitismo siguen intactos), 
            solo le da a la población inicial un punto de partida razonable."""
            cromosoma = []
            f, c = self.posicion
            for _ in range(longitud_cromosoma):
                if (f, c) == salida:
                    cromosoma.append((0, 0))
                    continue

                buenas = []
                if f > salida[0]:
                    buenas.append((-1, 0))
                elif f < salida[0]:
                    buenas.append((1, 0))
                if c > salida[1]:
                    buenas.append((0, -1))
                elif c < salida[1]:
                    buenas.append((0, 1))

                buenas_validas = [
                    (df, dc) for (df, dc) in buenas
                    if 0 <= f + df < filas and 0 <= c + dc < columnas
                    and costo_celda[f + df][c + dc] != INF
                ]

                if buenas_validas and random.random() < PROB_DIRIGIDO:
                    gen = random.choice(buenas_validas)
                else:
                    gen = random.choice(ACCIONES)

                cromosoma.append(gen)

                df, dc = gen
                f_sig, c_sig = f + df, c + dc
                if ((df, dc) != (0, 0) and 0 <= f_sig < filas and 0 <= c_sig < columnas
                        and costo_celda[f_sig][c_sig] != INF):
                    f, c = f_sig, c_sig
                # Si el gen resultó inválido, la posición simulada no avanza
                # decodificar() contabilizará ese mismo gen como movimiento inválido más adelante

            return cromosoma

        def decodificar(cromosoma):
            # Simula el cromosoma sobre la grilla actual y retorna:
            # (ruta, costo_total, llego_a_salida, movimientos_invalidos, pasos_usados)
            f, c = self.posicion
            ruta = []
            costo_total = 0
            movimientos_invalidos = 0
            pasos_usados = 0

            for df, dc in cromosoma:
                if (f, c) == salida:
                    break

                if df == 0 and dc == 0:  # esperar: siempre valido, cuesta 1 turno
                    ruta.append((f, c))
                    pasos_usados += 1
                    continue

                f_nueva, c_nueva = f + df, c + dc

                if 0 <= f_nueva < filas and 0 <= c_nueva < columnas and costo_celda[f_nueva][c_nueva] != INF:
                    costo_total += costo_celda[f_nueva][c_nueva]
                    f, c = f_nueva, c_nueva
                    ruta.append((f, c))
                    pasos_usados += 1
                else:
                    movimientos_invalidos += 1  # Choca contra muro-fuego-borde -> no avanza

            llego = (f, c) == salida
            return ruta, costo_total, llego, movimientos_invalidos, pasos_usados

        def costo_fitness(cromosoma): # Mide cuánto cuesta cada ruta
            ruta, costo_total, llego, movimientos_invalidos, pasos_usados = decodificar(cromosoma)
            f_final, c_final = ruta[-1] if ruta else self.posicion
            distancia_restante = self._distancia_manhattan((f_final, c_final), self.salida)

            costo = costo_total + pasos_usados + movimientos_invalidos * PENALIZACION_MOV_INVALIDO
            if not llego:
                costo += PENALIZACION_NO_LLEGAR + distancia_restante * 10
            return costo

        def seleccion_por_torneo(poblacion, costos):
            participantes = random.sample(range(len(poblacion)), min(tam_torneo, len(poblacion)))
            mejor = min(participantes, key=lambda i: costos[i])
            return poblacion[mejor]

        def cruzar(padre1, padre2):
            if longitud_cromosoma < 2 or random.random() > prob_cruce:
                return list(padre1), list(padre2)
            punto = random.randint(1, longitud_cromosoma - 1)
            hijo1 = padre1[:punto] + padre2[punto:]
            hijo2 = padre2[:punto] + padre1[punto:]
            return hijo1, hijo2

        def mutar(individuo):
            return [random.choice(ACCIONES) if random.random() < prob_mutacion else gen
                    for gen in individuo]

        # Ciclo evolutivo
        poblacion = [crear_individuo() for _ in range(tam_poblacion)]
        mejor_individuo = poblacion[0]
        mejor_costo = float('inf')

        for _generacion in range(generaciones):
            costos = [costo_fitness(ind) for ind in poblacion]

            idx_mejor_gen = min(range(len(poblacion)), key=lambda i: costos[i])
            if costos[idx_mejor_gen] < mejor_costo:
                mejor_costo = costos[idx_mejor_gen]
                mejor_individuo = poblacion[idx_mejor_gen]

            # Parada temprana: ya se encontró una ruta de longitud mínima (= ala distancia Manhattan) sin movimientos desperdiciados
            # no tiene sentido seguir evolucionando por menos pasos que eso
            _, _, llego_mejor, invalidos_mejor, pasos_mejor = decodificar(mejor_individuo)
            if llego_mejor and invalidos_mejor == 0 and pasos_mejor <= dist_inicial:
                break

            nueva_poblacion = [list(mejor_individuo)]  # Elitismo
            while len(nueva_poblacion) < tam_poblacion:
                padre1 = seleccion_por_torneo(poblacion, costos)
                padre2 = seleccion_por_torneo(poblacion, costos)
                hijo1, hijo2 = cruzar(padre1, padre2)
                nueva_poblacion.append(mutar(hijo1))
                if len(nueva_poblacion) < tam_poblacion:
                    nueva_poblacion.append(mutar(hijo2))

            poblacion = nueva_poblacion

        ruta_final, _, _, _, _ = decodificar(mejor_individuo)
        return ruta_final
