# Patrones de demanda del Metro de Medellín con agrupamiento

**Inteligencia Artificial · Actividad 4 · Métodos de aprendizaje no supervisado**
Corporación Universitaria Iberoamericana · Ingeniería de Software

Agrupamos los perfiles horarios de demanda de las estaciones de las líneas A y B del
Metro de Medellín con **k-means** y con **agrupamiento jerárquico de Ward**, sin usar
etiquetas. El algoritmo encontró cinco patrones: días laborales en zonas residenciales,
en el centro y en zonas mixtas, sábados, y domingos y festivos. Además detectó por su
cuenta los días de partido en el estadio.

## Integrantes

- Julian Vega Joya
- Alejandro Mora

## Qué hay en el repositorio

| Entregable de la actividad | Dónde está |
|---|---|
| 1. Archivos de fuentes de datos | [`data/afluencia_metro_medellin.csv`](data/afluencia_metro_medellin.csv), [`data/perfiles_estacion_dia.csv`](data/perfiles_estacion_dia.csv), [`data/estaciones.csv`](data/estaciones.csv), [`data/generar_dataset.py`](data/generar_dataset.py) |
| 2. Código fuente en Python | [`src/agrupamiento.py`](src/agrupamiento.py), [`src/consultar.py`](src/consultar.py) |
| 3. Descripción de los datos | [`docs/Descripcion_de_los_datos.pdf`](docs/Descripcion_de_los_datos.pdf) (APA 7) |
| 4. Pruebas realizadas | [`docs/Pruebas_realizadas.pdf`](docs/Pruebas_realizadas.pdf) (APA 7) · carpeta [`tests/`](tests) |
| 5. Video | enlace en [`docs/Entrega_Actividad4.pdf`](docs/Entrega_Actividad4.pdf) |

## Cómo ejecutarlo

```bash
python -m pip install -r requirements.txt

python src/agrupamiento.py          # agrupa y guarda resultados
python -m pytest tests -v           # corre las 17 pruebas

python src/consultar.py --resumen
python src/consultar.py --estacion Estadio --dia Sábado
```

## Resultados

| Medida | Valor |
|---|---|
| Perfiles agrupados (estación-día) | 1568 de 19 horas cada uno |
| Número de grupos (método del codo) | 5 |
| Coeficiente de silueta | 0,308 |
| Coincidencia k-means vs. Ward (ARI) | 0,999 |
| Coincidencia con tipo de día y zona (ARI) | 0,955 |

![Perfiles por grupo](resultados/perfiles_por_grupo.png)

## Advertencia sobre los datos

La afluencia por estación es **simulada**, porque el Metro la publica por línea y no por
estación. Los resultados demuestran que el método funciona, no describen la operación
real del Metro. Detalle en [`docs/Descripcion_de_los_datos.pdf`](docs/Descripcion_de_los_datos.pdf).

## Referencia

Palma Méndez, J. T., y Marín Morales, R. L. (Coords.). (2008). *Inteligencia artificial: Métodos, técnicas y aplicaciones* (cap. 16, Técnicas de agrupamiento). McGraw-Hill.
