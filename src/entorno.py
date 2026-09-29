import numpy as np
import random

'''
Para el entorno, se define una grilla de tamaño filas x columnas, donde los pasillos libres se representan con 0,
los obstaculos con 1,
la salida con 2 y el fuego con 3.

'''

DENSIDAD_OBSTACULOS = {
    1: 0.7,  # Alta densidad
    2: 0.3,  # Media densidad 
    3: 0.1,  # Baja densidad 
}

class Entorno:
    def __init__(self, filas, columnas, tipo_mapa, posiciones_a_proteger=None, posicion_fuego_inicial=(1, 1)):
        # posiciones_a_proteger: coordenadas que nunca deben quedar cubiertas por un obstáculo ni por el fuego inicial 
        # posicion_fuego_inicial: casilla donde nace el incendio. 

        if tipo_mapa not in DENSIDAD_OBSTACULOS:
            raise ValueError(
                f"tipo_mapa inválido: {tipo_mapa!r} "
            )

        self.filas = filas
        self.columnas = columnas
        self.grilla = np.zeros((filas, columnas), dtype=int)
        self.ocupacion = np.zeros((filas, columnas), dtype=int)  #grilla para la ocupación de los agentes

        self.salida = (self.filas - 1, self.columnas - 1)  # salida en la esquina inferior derecha

        protegidas = set(posiciones_a_proteger or [])
        protegidas.add(self.salida)

        self._generar_mapa(tipo_mapa, protegidas, posicion_fuego_inicial)

    def _dentro_de_grilla(self, celda): # verifica que una coordenada esté dentro del mapa
        f, c = celda
        return 0 <= f < self.filas and 0 <= c < self.columnas

    def _generar_mapa(self, tipo_mapa, protegidas, posicion_fuego_inicial):
        # Ubicar el fuego inicial evitando la salida y las posiciones protegidas
        if self._dentro_de_grilla(posicion_fuego_inicial) and posicion_fuego_inicial not in protegidas:
            posicion_fuego = posicion_fuego_inicial
        else:
            candidatas = [
                (f, c) for f in range(self.filas) for c in range(self.columnas)
                if (f, c) not in protegidas
            ]
            posicion_fuego = random.choice(candidatas) if candidatas else None

        # Ubicar obstáculos aleatorios sin pisar la salida, el fuego ni las protegidas
        celdas_reservadas = set(protegidas)
        if posicion_fuego is not None:
            celdas_reservadas.add(posicion_fuego)

        celdas_libres = [
            (f, c) for f in range(self.filas) for c in range(self.columnas)
            if (f, c) not in celdas_reservadas
        ]

        porcentaje = DENSIDAD_OBSTACULOS[tipo_mapa]
        num_obstaculos = min(int(self.filas * self.columnas * porcentaje), len(celdas_libres))

        for (f, c) in random.sample(celdas_libres, num_obstaculos): # se usa random.sample sobre las celdas libres
            self.grilla[f][c] = 1  # Obstáculo

        # Salida y fuego se escriben al final para garantizar que nunca quedan tapados
        self.grilla[self.salida] = 2
        if posicion_fuego is not None:
            self.grilla[posicion_fuego] = 3

        self._asegurar_conectividad(protegidas, posicion_fuego)

    def _celdas_vecinas(self, celda): # devuelve las celdas vecinas de una posición
        f, c = celda
        for df, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nf, nc = f + df, c + dc
            if 0 <= nf < self.filas and 0 <= nc < self.columnas:
                yield (nf, nc)

    def _bfs_alcanzables(self, origen, valores_bloqueados):
        # Genera un recorrido tipo bfs desde una celda dada
        # Útil para saver qie celdas son alcanzables desde la salida o desde un punto de inicio
        from collections import deque
        visitados = {origen}
        cola = deque([origen])
        while cola:
            actual = cola.popleft()
            for vecino in self._celdas_vecinas(actual):
                if vecino not in visitados and self.grilla[vecino] not in valores_bloqueados:
                    visitados.add(vecino)
                    cola.append(vecino)
        return visitados

    def _bfs_ignorando_obstaculos(self, origen, evitar):
        """Este bfs puede atravesar obstáculos para encontrar un camino pero no puede pasar por
        la celda <evitar>. La razón de esto es que, si un mapa queda aislado, necesita ver si existe
        alguna ruta, aunque hayan obstáculos intermedios que se puedan desoejar después"""
        from collections import deque
        if origen == self.salida:
            return []
        frontera = deque([(origen, [])])
        visitados = {origen}
        while frontera:
            actual, camino = frontera.popleft()
            if actual == self.salida:
                return camino
            for vecino in self._celdas_vecinas(actual):
                if vecino not in visitados and vecino != evitar: # evitar normalmente es el fuego inicial
                    visitados.add(vecino)
                    frontera.append((vecino, camino + [vecino]))
        return []

    def _asegurar_conectividad(self, protegidas, posicion_fuego):
        # Aquí se aplican los bfs de arriba, dada una coordenada busca si es alcanzable desde la salida
        # en el caso de no serlo, se busca un camino ignorando los obstáculos
        alcanzables = self._bfs_alcanzables(self.salida, valores_bloqueados={1, 3})
        for p in protegidas:
            if p == self.salida or p in alcanzables:
                continue
            camino = self._bfs_ignorando_obstaculos(p, evitar=posicion_fuego)
            for celda in camino:
                if self.grilla[celda] == 1:
                    self.grilla[celda] = 0  # despeja el obstaculo para abrir paso
            alcanzables = self._bfs_alcanzables(self.salida, valores_bloqueados={1, 3})

    def propagar_fuego(self):
        coordenadas_fuego = np.where(self.grilla == 3)
        lista_fuego = list(zip(coordenadas_fuego[0], coordenadas_fuego[1]))

        movimientos = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Arriba, Abajo, Izquierda, Derecha

        #Se usa un set para no contar dos veces una casilla alcanzada desde dos focos de fuego distintos 
        #en la misma propagación
        nuevas_casillas_fuego = set()
        for (f, c) in lista_fuego:
            for df, dc in movimientos:
                nueva_fila = f + df
                nueva_columna = c + dc
                if 0 <= nueva_fila < self.filas and 0 <= nueva_columna < self.columnas:
                    if self.grilla[nueva_fila][nueva_columna] == 0:
                        nuevas_casillas_fuego.add((nueva_fila, nueva_columna))

        for (f, c) in nuevas_casillas_fuego:
            self.grilla[f][c] = 3   # Propagar el fuego a la nueva casilla
        print(f"Fuego propagado a {len(nuevas_casillas_fuego)} nuevas casillas.")

    def actualizar_ocupacion(self, posicion_agentes):
        self.ocupacion.fill(0)  # Reiniciar la grilla de ocupación
        for (f, c) in posicion_agentes:
            if 0 <= f < self.filas and 0 <= c < self.columnas:
                self.ocupacion[f][c] += 1  # Cuenta cuántos agentes hay en la msma casilla

    def obtener_costo(self, fila, columna, tipo_funcion='cuadratica'):
        # Calcula el costo de transitar por una celda específica basado en su congestión.
        # el costo base de moverse a una celda libre es 1.
    
        if self.grilla[fila, columna] == 3 or self.grilla[fila, columna] == 1:
            return float('inf')  # costo infinito para fuego y obstáculos

        personas = self.ocupacion[fila, columna]
        costo_base = 1

        if tipo_funcion == 'lineal':
            costo_total = costo_base + (personas * 2)
        elif tipo_funcion == 'cuadratica':
            costo_total = costo_base + (personas ** 2)  
        elif tipo_funcion == 'exponencial':
            costo_total = costo_base * (2 ** personas)  
        else:
            raise ValueError(f"tipo_funcion desconocido {tipo_funcion!r}")

        return costo_total

    def imprimir_entorno(self):
        simbolos = {0: '.', 1: '#', 2: 'S', 3: 'F'}
        for i in range(self.filas):
            fila_str = ''
            for j in range(self.columnas):
                valor = self.grilla[i][j]
                fila_str += simbolos.get(valor, '?') + ' '
            print(fila_str)
