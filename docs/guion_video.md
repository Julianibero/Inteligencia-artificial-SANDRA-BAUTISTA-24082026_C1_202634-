# Guion del video (máximo 10 minutos)

Está pensado para 9:30, con medio minuto de margen. Son cuatro bloques; cada bloque
lo presenta una persona con su cámara o voz, para que **todos los integrantes participen**.

| Integrantes | Reparto sugerido |
|---|---|
| 2 | Persona 1: bloques 1 y 3 · Persona 2: bloques 2 y 4 |
| 3 | Persona 1: bloque 1 y la primera mitad del 3 · Persona 2: bloque 2 y la segunda mitad del 3 · Persona 3: bloque 4 |
| 4 | Un bloque por persona |

**Antes de grabar:** tener abierta la terminal en la carpeta del proyecto, el
repositorio en el navegador y el editor con `src/modelo_congestion.py`. Correr una vez
`python src/modelo_congestion.py` para que los gráficos ya existan. Subir el tamaño de
letra de la terminal y del editor.

---

## Bloque 1 · El proyecto (0:00 – 1:30)

**En pantalla:** README del repositorio.

> Hola, somos [nombres] y esta es la actividad 5 de Inteligencia Artificial: métodos
> supervisados.
>
> Venimos trabajando sobre el transporte masivo, con el Metro de Medellín. En las
> actividades anteriores el sistema encontraba la mejor ruta entre dos estaciones. Pero
> una ruta puede ser la más corta y aun así ser mala idea si la estación de transbordo
> está colapsada. Eso es lo que resolvemos hoy.
>
> Construimos un modelo que predice si una estación va a tener congestión baja, media o
> alta en una hora determinada, usando solo información que se conoce de antemano: la
> estación, la hora, el día, si llueve y si hay un evento masivo cerca.
>
> Es aprendizaje supervisado porque le mostramos al modelo miles de ejemplos donde ya
> conocemos la respuesta, y él aprende las reglas. Usamos un árbol de decisión, que es
> el tema del capítulo 17 del libro de Palma Méndez.

## Bloque 2 · Los datos (1:30 – 3:30)

**En pantalla:** `docs/Descripcion_de_los_datos.pdf`, luego el CSV abierto.

> Lo primero fue buscar datos reales. El Metro de Medellín tiene un portal de datos
> abiertos y publica la afluencia, pero agregada por línea, no por estación. También
> encontramos el catálogo de estaciones, un GTFS con los recorridos y un informe con
> la afluencia de 2016. Ninguna fuente trae pasajeros por estación y por hora, que es
> lo que necesitamos.
>
> La actividad dice que en ese caso se construye un dataset de muestra, y eso hicimos.
> Queremos ser claros: los pasajeros son simulados. Lo que sí es real son las 27
> estaciones de las líneas A y B, el calendario con sus festivos y el orden de magnitud
> de la demanda, unos 713 mil usos en un día laboral.

*(Mostrar el CSV.)*

> Cada fila es una estación en una hora. Son 29.176 filas, ocho semanas de operación.
> Las columnas son: día, tipo de día, hora, línea, estación, tipo de zona, si es de
> transferencia, clima y evento. Y al final la etiqueta: nivel de congestión.
>
> Un detalle importante: las columnas de pasajeros e índice de ocupación NO se las
> damos al modelo. La etiqueta sale de ahí, así que sería hacer trampa. Además, en la
> vida real uno no sabe cuánta gente va a entrar antes de que pase.

## Bloque 3 · El código (3:30 – 7:00)

**En pantalla:** editor con `src/modelo_congestion.py`, luego la terminal.

> El código está en un solo archivo y sigue seis pasos.

*(Ir bajando por el archivo y señalar cada parte.)*

> **Uno**, cargar el CSV con pandas y validar que no falten columnas ni haya nulos.
>
> **Dos**, separar las variables predictoras, que llamamos X, de la etiqueta, que es y.
>
> **Tres**, `train_test_split`: 80 % para entrenar y 20 % para probar. Usamos
> `stratify` para que las dos partes tengan la misma proporción de cada clase.
>
> **Cuatro**, el modelo. Es un `Pipeline` con dos piezas. La primera es un
> `OneHotEncoder`: scikit-learn solo entiende números, así que cada estación se vuelve
> una columna de ceros y unos. La segunda es el `DecisionTreeClassifier` con criterio
> de entropía, que es la ganancia de información del libro: en cada nodo el árbol
> elige la pregunta que mejor separa las clases.
>
> **Cinco**, `GridSearchCV`. En vez de adivinar la profundidad del árbol, probamos 35
> combinaciones con validación cruzada y nos quedamos con la mejor.
>
> **Seis**, evaluar con los datos de prueba, que el árbol nunca vio, y guardar los
> resultados.

*(Pasar a la terminal y ejecutar.)*

```bash
python src/modelo_congestion.py
```

> Ahí vemos los 29 mil registros, la división, la línea base de 47 % y, después de la
> búsqueda, el mejor árbol.

*(Mientras corre, o al terminar, abrir `resultados/arbol_decision.png`.)*

> Estos son los primeros niveles del árbol. La primera pregunta es si la hora es
> anterior a las 8 de la noche. Si lo es, pregunta si es domingo o festivo; si ya es
> de noche, pregunta por el tipo de zona. Cada camino de la raíz a una hoja se lee
> como una regla: si es día laboral, hora pico de la tarde y zona de empleo, entonces
> congestión alta.

*(Ejecutar dos consultas.)*

```bash
python src/predecir.py --estacion "San Antonio" --dia Viernes --hora 18
python src/predecir.py --estacion Estadio --dia Sábado --hora 19
python src/predecir.py --estacion Estadio --dia Sábado --hora 19 --evento
```

> San Antonio un viernes a las seis: alto. La estación Estadio un sábado a las siete
> de la noche: bajo. Pero si hay partido, la misma estación a la misma hora pasa a alto.

## Bloque 4 · Resultados y pruebas (7:00 – 9:30)

**En pantalla:** `docs/Pruebas_realizadas.pdf` con las figuras, luego la terminal.

> El modelo acierta el 84 % de los casos de prueba. La línea base, que es decir siempre
> "bajo", acierta el 47 %. Son 37 puntos de diferencia.

*(Mostrar la matriz de confusión.)*

> Esta es la matriz de confusión. Lo que más nos interesa: nunca confunde bajo con
> alto. Todos los errores son entre niveles vecinos, sobre todo en "medio".

*(Mostrar la curva de profundidad.)*

> Aquí se ve el sobreajuste. Si dejamos crecer el árbol sin control, en entrenamiento
> sigue mejorando, pero en validación empieza a bajar: está memorizando en lugar de
> aprender. Por eso exigimos un mínimo de 10 ejemplos por hoja, que funciona como poda.

*(Mostrar la importancia de variables.)*

> La hora y la estación explican casi dos tercios de la decisión.

*(Ejecutar las pruebas.)*

```bash
python -m pytest tests -v
```

> Además tenemos 27 pruebas automáticas: 9 revisan la calidad de los datos y 18 el
> modelo. Todas pasan.
>
> Las pruebas nos sirvieron de verdad. En la primera versión el modelo no distinguía
> si había partido o no, porque teníamos muy pocos ejemplos de eventos. La exactitud
> general se veía bien y aun así fallaba en ese caso. Ampliamos la muestra y quedó
> corregido.
>
> Para cerrar: el árbol de decisión nos dio un modelo que se puede explicar, porque
> cada predicción es una cadena de preguntas. La limitación principal es que los datos
> son simulados. El paso siguiente sería conseguir la afluencia real por estación y
> conectar esta predicción con el buscador de rutas de las actividades anteriores.
>
> El código, los datos y la documentación están en el repositorio. Gracias.

---

## Lista de chequeo antes de entregar

- [ ] El video dura menos de 10 minutos.
- [ ] Hablan todos los integrantes.
- [ ] Se ve la ejecución real de los comandos, no solo capturas.
- [ ] El video está subido con enlace que el tutor pueda abrir sin pedir permiso.
- [ ] El tutor está agregado como colaborador del repositorio.
- [ ] El historial de Git tiene commits de cada integrante desde su propia cuenta.
- [ ] Completaron la configuración de `docs/generar_pdfs_apa.py` (repositorio, video y docente) y volvieron a generar los PDF.
