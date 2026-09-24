import math
import heapq

# ==========================================
# BASE DE CONOCIMIENTO
# ==========================================

conexiones = {
    "Niquía": ["Madera"],
    "Madera": ["Niquía", "Bello"],
    "Bello": ["Madera", "Acevedo"],
    "Acevedo": ["Bello", "Caribe", "Parque Berrío"],
    "Caribe": ["Acevedo", "Universidad"],
    "Universidad": ["Caribe", "Hospital"],
    "Hospital": ["Universidad", "Prado"],
    "Prado": ["Hospital", "Parque Berrío"],
    "Parque Berrío": ["Prado", "Acevedo", "San Antonio"],
    "San Antonio": ["Parque Berrío", "Alpujarra", "Exposiciones"],
    "Alpujarra": ["San Antonio", "Exposiciones"],
    "Exposiciones": ["Alpujarra", "Industriales", "San Antonio"],
    "Industriales": ["Exposiciones", "Poblado"],
    "Poblado": ["Industriales", "Aguacatala"],
    "Aguacatala": ["Poblado"]
}

# ==========================================
# COORDENADAS SIMPLIFICADAS
# ==========================================

coordenadas = {
    "Niquía": (0, 0),
    "Madera": (1, 0),
    "Bello": (2, 0),
    "Acevedo": (3, 0),
    "Caribe": (4, 1),
    "Universidad": (5, 2),
    "Hospital": (6, 3),
    "Prado": (7, 2),
    "Parque Berrío": (6, 1),
    "San Antonio": (6, 0),
    "Alpujarra": (7, -1),
    "Exposiciones": (8, 0),
    "Industriales": (9, 0),
    "Poblado": (10, 1),
    "Aguacatala": (11, 2)
}

# ==========================================
# FUNCIÓN HEURÍSTICA
# ==========================================

def heuristica(estacion, destino):

    x1, y1 = coordenadas[estacion]
    x2, y2 = coordenadas[destino]

    return math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )


# ==========================================
# ALGORITMO A*
# ==========================================

def buscar_ruta(origen, destino):

    frontera = []

    heapq.heappush(frontera, (0, origen))

    costos = {origen: 0}
    anteriores = {origen: None}

    while frontera:

        _, actual = heapq.heappop(frontera)

        if actual == destino:
            break

        for vecino in conexiones[actual]:

            nuevo_costo = costos[actual] + 1

            if vecino not in costos or nuevo_costo < costos[vecino]:

                costos[vecino] = nuevo_costo

                prioridad = (
                    nuevo_costo +
                    heuristica(vecino, destino)
                )

                heapq.heappush(
                    frontera,
                    (prioridad, vecino)
                )

                anteriores[vecino] = actual

    if destino not in anteriores:
        return None

    ruta = []

    actual = destino

    while actual is not None:

        ruta.append(actual)

        actual = anteriores[actual]

    ruta.reverse()

    return ruta


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

print("======================================")
print("   SISTEMA INTELIGENTE DE RUTAS")
print("======================================")

print("\nEstaciones disponibles:")

for estacion in conexiones:
    print("-", estacion)

origen = input("\nIngrese la estación de origen: ")
destino = input("Ingrese la estación de destino: ")

if origen not in conexiones or destino not in conexiones:

    print("\nError: una de las estaciones no existe.")

else:

    ruta = buscar_ruta(origen, destino)

    if ruta:

        print("\nRuta encontrada:")
        print(" → ".join(ruta))

        print(
            "Número de conexiones:",
            len(ruta) - 1
        )

    else:

        print("\nNo se encontró una ruta.")
