# Inteligencia-artificial-SANDRA-BAUTISTA-24082026_C1_202634-
Trabajo Universitario 
# Sistema Inteligente de Búsqueda de Rutas 🚇

Sistema inteligente desarrollado en Python que encuentra la ruta óptima entre dos estaciones dentro de una representación simplificada del sistema de transporte masivo de Medellín. El proyecto aplica conceptos de representación del conocimiento, sistemas basados en reglas y estrategias de búsqueda heurística, desarrollados en el curso de Inteligencia Artificial.

## Descripción

El sistema recibe una estación de origen y una estación de destino, y utiliza el algoritmo de búsqueda **A\*** (A-star) sobre una base de conocimiento representada como un grafo de estaciones y conexiones, para encontrar el camino más corto entre ambos puntos.

- **Base de conocimiento:** estaciones y conexiones representadas mediante un diccionario de adyacencia.
- **Reglas lógicas:** determinan qué desplazamientos son posibles y cuándo la búsqueda finaliza.
- **Estrategia de búsqueda:** algoritmo A*, combinando el costo acumulado `g(n)` con una heurística de distancia euclidiana `h(n)`.

## Integrantes

- Julian Vega Joya
- Alejandro Mora

## Requisitos

- Python 3.8 o superior
- No requiere librerías externas (solo `math` y `heapq`, incluidas en la instalación estándar de Python)

Puedes verificar tu versión de Python con:

```bash
python --version
```

## Instalación

1. Clona este repositorio:

```bash
   git clone https://github.com/tu-usuario/nombre-del-repositorio.git
```

2. Ingresa a la carpeta del proyecto:

```bash
   cd nombre-del-repositorio
```

No se necesita instalar dependencias adicionales.

## Ejecución

Ejecuta el script principal desde la terminal:

```bash
python ruta_transporte_ai.py
```

El programa mostrará el listado de estaciones disponibles y solicitará la estación de origen y de destino:

```
======================================
   SISTEMA INTELIGENTE DE RUTAS
======================================

Estaciones disponibles:
- Niquía
- Madera
- Bello
- Acevedo
- Caribe
- Universidad
- Hospital
- Prado
- Parque Berrío
- San Antonio
- Alpujarra
- Exposiciones
- Industriales
- Poblado
- Aguacatala

Ingrese la estación de origen: Niquía
Ingrese la estación de destino: Hospital
```

### Salida esperada

```
Ruta encontrada:
Niquía → Madera → Bello → Acevedo → Caribe → Universidad → Hospital
Número de conexiones: 6
```

Si alguna de las estaciones ingresadas no existe en la base de conocimiento, el sistema mostrará un mensaje de error indicando que los datos ingresados son incorrectos.

## Ejemplos de uso

| Origen    | Destino     | Resultado esperado |
|-----------|-------------|---------------------|
| Niquía    | Hospital    | Niquía → Madera → Bello → Acevedo → Caribe → Universidad → Hospital |
| Acevedo   | San Antonio | Acevedo → Parque Berrío → San Antonio |
| Poblado   | Niquía      | Poblado → Industriales → Exposiciones → San Antonio → Parque Berrío → Acevedo → Bello → Madera → Niquía |

## Estructura del proyecto

```
├── ruta_transporte_ai.py   # Código fuente del sistema inteligente
└── README.md                # Instrucciones de uso del proyecto
```

## Conceptos aplicados

- Representación del conocimiento mediante grafos y reglas lógicas
- Sistemas basados en reglas
- Búsqueda heurística informada (algoritmo A*)
- Función heurística basada en distancia euclidiana

## Curso

Inteligencia Artificial — Facultad de Ingeniería, Corporación Universitaria Iberoamericana
Docente: Sandra Bautista
