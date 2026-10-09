# Predicción de congestión en el Metro de Medellín 

**Inteligencia Artificial · Actividad 3 · Métodos supervisados**
Corporación Universitaria Iberoamericana · Ingeniería de Software

Árbol de decisión que predice si una estación del Metro de Medellín (líneas A y B)
va a tener congestión **Baja, Media o Alta** en una hora dada, a partir de datos que
se conocen de antemano: estación, hora, día, clima y si hay un evento masivo cerca.

Es la continuación del proyecto de transporte masivo de las actividades anteriores:
antes buscábamos la mejor ruta entre dos estaciones; ahora añadimos la capacidad de
anticipar qué tan llena va a estar cada estación, que es justo el dato que le falta
a un planificador de rutas para recomendar bien.

## Integrantes

- Julian Vega Joya
- Alejandro Mora
<!-- Agregar aquí a los demás integrantes del equipo, si los hay -->

## Qué hay en el repositorio

| Entregable de la actividad | Dónde está |
|---|---|
| 1. Archivos de fuentes de datos | [`data/afluencia_metro_medellin.csv`](data/afluencia_metro_medellin.csv), [`data/estaciones.csv`](data/estaciones.csv), [`data/generar_dataset.py`](data/generar_dataset.py) |
| 2. Código fuente en Python | [`src/modelo_congestion.py`](src/modelo_congestion.py), [`src/predecir.py`](src/predecir.py) |
| 3. Descripción de los datos | [`docs/Descripcion_de_los_datos.pdf`](docs/Descripcion_de_los_datos.pdf) (APA 7) · versión web: [`docs/descripcion_datos.md`](docs/descripcion_datos.md) |
| 4. Pruebas realizadas | [`docs/Pruebas_realizadas.pdf`](docs/Pruebas_realizadas.pdf) (APA 7) · versión web: [`docs/pruebas.md`](docs/pruebas.md) · carpeta [`tests/`](tests) |
| 5. Video | enlace en [`docs/Entrega_Actividad5.pdf`](docs/Entrega_Actividad5.pdf) |

Resultados de la última ejecución: carpeta [`resultados/`](resultados).

## Cómo ejecutarlo

Se necesita Python 3.10 o superior.

```bash
pip install -r requirements.txt

python data/generar_dataset.py      # (opcional) vuelve a crear el dataset
python src/modelo_congestion.py     # entrena, evalúa y guarda resultados
python -m pytest tests -v           # corre las 27 pruebas

# Consultar un caso
python src/predecir.py --estacion "San Antonio" --dia Viernes --hora 18
python src/predecir.py --estacion Estadio --dia Sábado --hora 19 --evento
```

## Resultados

| Métrica | Valor |
|---|---|
| Registros | 29.176 (80 % entrenamiento, 20 % prueba) |
| Exactitud en prueba | **84,0 %** |
| Línea base (decir siempre "Bajo") | 47,0 % |
| Validación cruzada (5 particiones) | 83,7 % |
| F1 macro | 0,830 |
| Errores graves (confundir Bajo con Alto) | 0 de 5.836 |

![Matriz de confusión](resultados/matriz_confusion.png)

![Importancia de variables](resultados/importancia_variables.png)

## Advertencia sobre los datos

La afluencia por estación es **simulada**. El Metro publica la afluencia por línea,
no por estación, así que construimos una muestra con la misma estructura (punto 2 de
la actividad). Los resultados demuestran que el método funciona, no describen la
operación real del Metro. El detalle está en
[`docs/Descripcion_de_los_datos.pdf`](docs/Descripcion_de_los_datos.pdf).

## Documentos en PDF (APA 7)

Los tres PDF de `docs/` se generan desde los archivos `.md` con normas APA 7.ª edición
(portada, Times New Roman 12 a doble espacio, tablas y figuras numeradas, citas y
referencias). Para regenerarlos, completar la configuración al inicio del script y ejecutar:

```bash
python docs/generar_pdfs_apa.py
```

## Referencias

Palma Méndez, J. T., y Marín Morales, R. L. (Coords.). (2008). *Inteligencia artificial: Métodos, técnicas y aplicaciones*. McGraw-Hill.

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., y Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830.
