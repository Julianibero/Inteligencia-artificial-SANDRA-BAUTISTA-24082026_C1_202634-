# Descripción de los datos para el agrupamiento de patrones de demanda del Metro de Medellín

## Introducción

Este documento describe los datos del modelo de aprendizaje no supervisado de la
Actividad 4. A diferencia de la actividad anterior, aquí no hay una respuesta que
predecir: el objetivo es descubrir, sin etiquetas, qué patrones de demanda horaria
existen en las estaciones de las líneas A y B del Metro de Medellín. Para eso se usan
técnicas de agrupamiento, que reúnen en un mismo grupo los casos parecidos entre sí y
separan los distintos (Palma Méndez y Marín Morales, 2008).

El caso que se agrupa es el perfil de una estación en un día: qué parte de los
pasajeros de ese día ingresó en cada hora. Dos perfiles se parecen si la demanda se
reparte de forma parecida a lo largo del día, sin importar el tamaño de la estación.

## Fuentes de datos identificadas

Para esta actividad se revisaron las mismas fuentes públicas de la actividad anterior,
porque el agrupamiento también requiere la afluencia por estación y por hora. La Tabla 1
las resume.

**Tabla 1**

*Fuentes de datos identificadas para el proyecto*

| Fuente | Contenido | Uso en el proyecto | Limitación |
|---|---|---|---|
| Pasajeros movilizados: afluencia (Metro de Medellín, s.f.-a; TUMI, 2023) | Pasajeros por línea, día y hora | Base de los perfiles de demanda | Está agregada por línea, no por estación; el enlace de datos.gov.co respondió "no encontrado" el día de la consulta |
| Pasajeros movilizados mensual (Metro de Medellín, s.f.-b) | Total de pasajeros por mes | Tendencia y estacionalidad | Demasiado agregada para perfiles horarios |
| Estaciones y líneas del sistema (Metro de Medellín, s.f.-c; Alcaldía de Medellín, 2021) | Ubicación georreferenciada de estaciones, línea y modo | Catálogo de estaciones | No contiene demanda |
| GTFS del Metro de Medellín (ColombiaInfo, s.f.) | Rutas, paradas y horarios en formato GTFS | Orden de estaciones y horario de operación | Sus autores advierten errores en los tiempos |
| Informe del Metro a ALAMYS (Metro de Medellín, 2017) | Afluencia de 2016 y horas de mayor carga | Calibrar el orden de magnitud de la demanda (cerca de 713 000 usos diarios en las líneas A y B) | Dato puntual de 2016 |
| Calendario de festivos (Ley 51 de 1983) | Días festivos de Colombia | Variable `tipo_dia` | Ninguna relevante |
| Red de pluviómetros del SIATA (Sistema de Alerta Temprana de Medellín y el Valle de Aburrá [SIATA], s.f.) | Precipitación por hora | Contexto climático | Fuente candidata; no se descargó |

*Nota.* Elaboración propia con base en las fuentes citadas.

Ninguna fuente pública contiene la afluencia por estación y por hora. Por eso se
reutilizó el dataset de muestra construido en la actividad anterior, tal como lo
permite el enunciado: "en caso de no existir dichas fuentes de datos, desarrolle un
dataset con una muestra de dichos datos".

## Datos de partida: afluencia horaria por estación

El archivo `data/afluencia_metro_medellin.csv` tiene 29 176 registros, uno por estación,
hora y día, entre el 2 de marzo y el 26 de abril de 2026. Lo genera el script
`data/generar_dataset.py` con semilla fija. La Tabla 2 separa lo real de lo simulado.

**Tabla 2**

*Componentes reales y simulados del dataset de afluencia*

| Real | Simulado |
|---|---|
| Nombres, orden y línea de las 27 estaciones (21 en la línea A y 7 en la B; San Antonio pertenece a ambas) | Número de pasajeros por hora |
| Calendario del 2 de marzo al 26 de abril de 2026, con sus tres festivos | Clima de cada hora y fechas de partidos en el estadio |
| Horario aproximado de operación: 4:00 a 22:59 de lunes a sábado y 5:00 a 21:59 los domingos y festivos | Tipo de zona y peso de demanda de cada estación (clasificación propia del equipo) |
| Orden de magnitud de la demanda: cerca de 713 000 usos en un día laboral (Metro de Medellín, 2017) | Perfil horario de cada tipo de zona |

La demanda se simuló con perfiles horarios distintos según el tipo de zona: las zonas
residenciales concentran sus ingresos en la mañana y las zonas de empleo en la tarde,
mientras que los sábados, domingos y festivos no tienen picos marcados. A eso se suman
el efecto de la lluvia, el de los partidos en el estadio y un ruido aleatorio. El
detalle completo está en la documentación de la actividad anterior.

## Datos para el agrupamiento: perfiles estación-día

El script `src/agrupamiento.py` transforma la afluencia en el archivo
`data/perfiles_estacion_dia.csv`. Para cada estación y cada día suma los pasajeros de
cada hora y los divide entre el total del día. El resultado son 1568 perfiles (28
combinaciones de estación y línea por 56 días), cada uno con 19 fracciones que suman 1.

Se usan fracciones, y no pasajeros, para que el algoritmo compare la forma de la
demanda y no su tamaño. Sin esta normalización, San Antonio quedaría sola en un grupo
por ser la estación más grande, aunque su patrón horario sea igual al de otras
estaciones del centro. La Tabla 3 describe las columnas.

**Tabla 3**

*Diccionario de datos del archivo de perfiles*

| Columna | Tipo | Descripción | Uso en el agrupamiento |
|---|---|---|---|
| `fecha` | Fecha | Día del perfil (2026-03-02 a 2026-04-26) | Identificación |
| `linea`, `estacion` | Categórica | Línea y estación | Identificación |
| `dia_semana` | Categórica | Lunes a domingo | Solo para interpretar los grupos |
| `tipo_dia` | Categórica | Laboral, Sábado o Domingo_Festivo | Solo para interpretar los grupos |
| `tipo_zona` | Categórica | Residencial, Centro_Empleo o Mixta | Solo para interpretar los grupos |
| `hubo_evento` | Binaria | 1 si hubo partido en el estadio ese día cerca de la estación | Solo para interpretar los grupos |
| `pasajeros_dia` | Entera | Total de ingresos del día (5917 a 68 793) | Solo para describir los grupos |
| `h04` a `h22` | Decimal | Fracción de los ingresos del día que entró en cada hora, de 4:00 a 22:00 | Variables del agrupamiento |

El algoritmo solo recibe las 19 columnas `h04` a `h22`. El tipo de día, el tipo de zona y
el evento se guardan para comprobar después si los grupos que encontró tienen sentido;
si se los entregáramos, el agrupamiento perdería su carácter no supervisado.

## Resumen estadístico

La Tabla 4 muestra cuántos perfiles hay de cada tipo de día y de zona. Esta distribución
no se le entrega al algoritmo; sirve para interpretar sus resultados.

**Tabla 4**

*Distribución de los perfiles por tipo de día y tipo de zona*

| Tipo de día | Residencial | Centro y empleo | Mixta | Total |
|---|---|---|---|---|
| Laboral | 444 | 370 | 222 | 1036 |
| Sábado | 96 | 80 | 48 | 224 |
| Domingo o festivo | 132 | 110 | 66 | 308 |
| Total | 672 | 560 | 336 | 1568 |

De los 1568 perfiles, 30 corresponden a días con partido en las estaciones Estadio o
Suramericana. Los domingos y festivos no tienen ingresos a las 4:00 ni a las 22:00,
porque el sistema opera de 5:00 a 21:59 esos días.

En cuanto a calidad, cada perfil suma 1, no hay valores nulos ni perfiles duplicados, y
el total de pasajeros coincide con el del archivo de afluencia. Esto lo verifican las
pruebas D1 a D6 descritas en el documento de pruebas.

## Limitaciones

- Los datos son simulados. Los grupos encontrados demuestran que el método funciona, pero no describen la operación real del Metro.
- Como los perfiles se simularon a partir de tipos de zona y de día, es esperable que el algoritmo los recupere. Con datos reales los grupos serían menos nítidos y podrían aparecer patrones nuevos.
- Ocho semanas no permiten observar la estacionalidad anual.
- Solo se cubren las líneas A y B del metro.

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
