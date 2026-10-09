# Descripción de los datos para el modelo de predicción de congestión del Metro de Medellín

## Introducción

Este documento describe los datos que alimentan el modelo de aprendizaje supervisado
de la Actividad 5. El modelo es un árbol de decisión que predice, para cada estación
de las líneas A y B del Metro de Medellín y para cada hora, el nivel de congestión:
`Bajo`, `Medio` o `Alto`. Se trata de un problema de clasificación supervisada, porque
el algoritmo aprende a partir de ejemplos en los que la respuesta ya se conoce
(Palma Méndez y Marín Morales, 2008).

Para que el árbol aprenda se necesitan registros históricos con dos partes: las
condiciones de cada hora (estación, día, hora, clima, eventos) y lo que ocurrió en
ella (cuántas personas ingresaron). A continuación se presentan las fuentes que se
identificaron, el dataset que se construyó y el diccionario de cada archivo.

## Fuentes de datos identificadas

Se buscaron fuentes públicas que sirvieran para entrenar el modelo. La consulta se
hizo el 7 de octubre de 2026 y sus resultados se resumen en la Tabla 1.

**Tabla 1**

*Fuentes de datos identificadas para el proyecto*

| Fuente | Contenido | Uso en el proyecto | Limitación |
|---|---|---|---|
| Pasajeros movilizados: afluencia (Metro de Medellín, s.f.-a; TUMI, 2023) | Pasajeros por línea, día y hora | Variable objetivo | Está agregada por línea, no por estación; el enlace de datos.gov.co respondió "no encontrado" el día de la consulta |
| Pasajeros movilizados mensual (Metro de Medellín, s.f.-b) | Total de pasajeros por mes | Tendencia y estacionalidad | Demasiado agregada para un modelo por hora |
| Estaciones y líneas del sistema (Metro de Medellín, s.f.-c; Alcaldía de Medellín, 2021) | Ubicación georreferenciada de estaciones, línea y modo | Catálogo de estaciones y transferencias | No contiene demanda |
| GTFS del Metro de Medellín (ColombiaInfo, s.f.) | Rutas, paradas y horarios en formato GTFS | Orden de estaciones y frecuencias | Sus autores advierten errores en los tiempos de `frequencies.txt` y `stop_times.txt` |
| Informe del Metro a ALAMYS (Metro de Medellín, 2017) | Afluencia de 2016 y horas de mayor carga | Calibrar el orden de magnitud de la muestra (cerca de 713 000 usos diarios en las líneas A y B) | Dato puntual de 2016 |
| Calendario de festivos (Ley 51 de 1983) | Días festivos de Colombia | Variable `tipo_dia` | Ninguna relevante |
| Red de pluviómetros del SIATA (Sistema de Alerta Temprana de Medellín y el Valle de Aburrá [SIATA], s.f.) | Precipitación por hora | Variable `clima` | Fuente candidata; no se descargó en esta entrega |

*Nota.* Elaboración propia con base en las fuentes citadas.

### Conclusión de la búsqueda

Ninguna fuente pública contiene la afluencia por estación y por hora, que es el nivel
de detalle que necesita el modelo. La fuente más cercana publica los pasajeros por
línea (Metro de Medellín, s.f.-a). Por esa razón se aplicó la segunda opción del
enunciado de la actividad: construir un dataset con una muestra de los datos.

## Construcción del dataset de muestra

El script `data/generar_dataset.py` genera una muestra simulada con la estructura que
tendría el dato real si el Metro lo publicara por estación. Usa una semilla fija, de
modo que cualquier persona que lo ejecute obtiene el mismo archivo. La Tabla 2 separa
lo que proviene de la realidad de lo que es simulado.

**Tabla 2**

*Componentes reales y simulados del dataset*

| Real | Simulado |
|---|---|
| Nombres, orden y línea de las 27 estaciones (21 en la línea A y 7 en la B; San Antonio pertenece a ambas) | Número de pasajeros por hora |
| Estaciones de transferencia con otras líneas o con cable (San Antonio, Acevedo y San Javier) | Clima de cada hora |
| Calendario del 2 de marzo al 26 de abril de 2026, con sus tres festivos | Fechas de partidos en el estadio |
| Horario aproximado de operación: 4:00 a 22:59 de lunes a sábado y 5:00 a 21:59 los domingos y festivos | Tipo de zona, peso de demanda y capacidad de referencia de cada estación (clasificación propia del equipo) |
| Orden de magnitud de la demanda: cerca de 713 000 usos en un día laboral (Metro de Medellín, 2017) | Nivel de congestión resultante |

### Simulación de la demanda

Para cada estación y hora se calcula un índice de ocupación como el producto de seis
factores:

1. El peso de la estación: San Antonio, por ejemplo, tiene más demanda relativa que Madera.
2. El perfil horario según el tipo de zona: las zonas residenciales se cargan en la mañana, cuando las personas salen a trabajar, y las zonas de empleo en la tarde, cuando regresan. Los sábados, domingos y festivos no tienen picos marcados.
3. Un ajuste por día de la semana: 6 % más los viernes y 3 % más los lunes.
4. La lluvia, que aumenta la demanda en 12 %, bajo el supuesto de que con lluvia más personas prefieren el metro.
5. Los eventos masivos, que multiplican la demanda por 1,9 en las estaciones Estadio y Suramericana entre las 17:00 y las 21:59 de los días de partido.
6. Un ruido aleatorio log-normal con σ = 0,15, porque dos lunes a la misma hora nunca son idénticos.

Después se calcula el número de pasajeros como el índice multiplicado por la capacidad
de referencia de la estación.

### Asignación de la etiqueta

La etiqueta se obtiene del índice de ocupación con los umbrales de la Tabla 3.

**Tabla 3**

*Umbrales del índice de ocupación para asignar el nivel de congestión*

| Índice de ocupación | Nivel de congestión |
|---|---|
| Menor que 0,45 | Bajo |
| Desde 0,45 y menor que 0,80 | Medio |
| 0,80 o más | Alto |

## Diccionario de datos

### Archivo afluencia_metro_medellin.csv

El archivo tiene 29 176 filas y 13 columnas, con codificación UTF-8 y coma como
separador. Cada fila corresponde a una estación en una hora de un día. La Tabla 4
describe cada columna.

**Tabla 4**

*Diccionario de datos del archivo de afluencia*

| Columna | Tipo | Valores | Descripción | Uso en el modelo |
|---|---|---|---|---|
| `fecha` | Fecha | 2026-03-02 a 2026-04-26 | Día del registro | No se usa; se representa con `dia_semana` y `tipo_dia` |
| `dia_semana` | Categórica | Lunes a domingo | Día de la semana | Predictora |
| `tipo_dia` | Categórica | Laboral, Sábado, Domingo_Festivo | Los festivos operan como domingo | Predictora |
| `hora` | Entera | 4 a 22 | Hora de inicio del intervalo (18 equivale a 18:00–18:59) | Predictora |
| `linea` | Categórica | A, B | Línea del metro | Predictora |
| `estacion` | Categórica | 27 estaciones | Nombre de la estación | Predictora |
| `tipo_zona` | Categórica | Residencial, Centro_Empleo, Mixta | Uso predominante del entorno | Predictora |
| `es_transferencia` | Binaria | 0, 1 | 1 si conecta con otra línea férrea o de cable | Predictora |
| `clima` | Categórica | Seco, Lluvia | Condición en esa hora | Predictora |
| `evento_especial` | Binaria | 0, 1 | 1 si hay un evento masivo cerca en esa hora | Predictora |
| `pasajeros_hora` | Entera | 83 a 10 822 | Ingresos a la estación en la hora | Excluida, porque de ella se deriva la etiqueta |
| `indice_ocupacion` | Decimal | 0,043 a 3,491 | Pasajeros divididos entre la capacidad de referencia | Excluida, porque de ella se deriva la etiqueta |
| `nivel_congestion` | Categórica | Bajo, Medio, Alto | Etiqueta que se quiere predecir | Variable objetivo |

Las columnas `pasajeros_hora` e `indice_ocupacion` se conservan en el archivo porque son
la medición, pero se excluyen del entrenamiento. Si el árbol las recibiera, le bastaría
aprender los dos umbrales de la Tabla 3 para acertar siempre, sin haber aprendido nada
útil. Además, en la práctica no se conocen antes de que ocurra la hora que se quiere
predecir. Este problema se conoce como fuga de información.

### Archivo estaciones.csv

El catálogo tiene 28 filas porque San Antonio aparece una vez por cada línea. Sus
columnas se describen en la Tabla 5.

**Tabla 5**

*Diccionario de datos del catálogo de estaciones*

| Columna | Descripción |
|---|---|
| `estacion`, `linea` | Identifican la estación |
| `orden_en_linea` | Posición dentro de la línea (1 corresponde a Niquía en la línea A y a San Antonio en la B) |
| `tipo_zona` | Residencial, Centro_Empleo o Mixta |
| `es_transferencia` | 1 para San Antonio, Acevedo y San Javier |
| `peso_demanda` | Demanda relativa de la estación frente a su capacidad (simulado) |
| `capacidad_referencia_hora` | Pasajeros por hora que la estación atiende sin aglomeración (simulado) |

## Resumen estadístico

La Tabla 6 muestra cómo se distribuye la etiqueta. Las clases están desbalanceadas,
con pocos casos `Alto`, como ocurre en la realidad: la congestión alta se concentra en
pocas horas del día. Por eso la división entre entrenamiento y prueba se hace de forma
estratificada y, además de la exactitud, se reporta el F1 por clase.

**Tabla 6**

*Distribución del nivel de congestión*

| Nivel | Registros | Porcentaje |
|---|---|---|
| Bajo | 13 702 | 47,0 % |
| Medio | 11 008 | 37,7 % |
| Alto | 4 466 | 15,3 % |
| Total | 29 176 | 100,0 % |

La Tabla 7 resume las demás variables.

**Tabla 7**

*Distribución de las variables de contexto*

| Variable | Distribución |
|---|---|
| `tipo_dia` | Laboral: 19 684 registros (37 días); Domingo_Festivo: 5236 (11 días); Sábado: 4256 (8 días) |
| `clima` | Seco: 22 344 (76,6 %); Lluvia: 6832 (23,4 %) |
| `evento_especial` | Sin evento: 29 026; con evento: 150 (0,5 %) |
| `pasajeros_hora` | Media: 1232; mediana: 1025; máximo: 10 822 |

En cuanto a calidad, el archivo no tiene valores nulos ni registros duplicados, y todas
las categorías están dentro de los valores esperados. Esto lo verifican las pruebas D1
a D9 descritas en el documento de pruebas.

## Limitaciones

- Los datos son simulados. Los resultados demuestran que el flujo y el método funcionan, pero no describen la operación real del Metro.
- El modelo aprende, en parte, las mismas reglas con las que se generaron los datos. Con datos reales la exactitud sería distinta y habría que evaluarla de nuevo.
- Solo se cubren las líneas A y B del metro; no se incluyen cables, tranvía ni buses.
- Ocho semanas no alcanzan para capturar la estacionalidad anual, como las vacaciones o diciembre.
- El paso siguiente sería solicitar al Metro la afluencia por estación, obtenida de las validaciones de la tarjeta Cívica, y reemplazar el archivo simulado. El código no tendría que cambiar.

## Referencias

Alcaldía de Medellín. (2021). *Estaciones del Sistema de Transporte Masivo* [Conjunto de datos]. GeoMedellín. https://medellin.gov.co/giscatalogacion/srv/api/records/8dd3580b-d615-4981-9a1f-3ed357c74eee

ColombiaInfo. (s.f.). *ColombiaGTFS: Medellín - Metro* [Conjunto de datos]. GitHub. https://github.com/ColombiaInfo/ColombiaGTFS/tree/master/Medellin%20-%20Metro

Ley 51 de 1983. Por la cual se traslada el descanso remunerado de algunos días festivos. (1983). Congreso de la República de Colombia.

Metro de Medellín. (s.f.-a). *Pasajeros movilizados: afluencia* [Conjunto de datos]. Datos Abiertos Colombia. https://www.datos.gov.co/Transporte/Pasajeros-Movilizados-Afluencia/9dbb-kbnv

Metro de Medellín. (s.f.-b). *Pasajeros movilizados mensual Metro de Medellín* [Conjunto de datos]. MEData. http://medata.gov.co/dataset/pasajeros-movilizados-mensual-metro-de-medell%C3%ADn

Metro de Medellín. (s.f.-c). *Portal de datos abiertos del Metro de Medellín*. https://datosabiertos-metrodemedellin.opendata.arcgis.com/

Metro de Medellín. (2017). *Metro de Medellín* [Informe]. Asociación Latinoamericana de Metros y Subterráneos. https://alamys.org/wp-content/uploads/2021/04/Metro-de-Medellin.pdf

Palma Méndez, J. T., y Marín Morales, R. L. (Coords.). (2008). *Inteligencia artificial: Métodos, técnicas y aplicaciones*. McGraw-Hill.

Sistema de Alerta Temprana de Medellín y el Valle de Aburrá. (s.f.). *SIATA*. https://siata.gov.co/

TUMI. (2023). *Passengers moved - influence* [Conjunto de datos]. TUMI Data Hub. https://hub.tumidata.org/dataset/passengers_moved_influence_medelln
