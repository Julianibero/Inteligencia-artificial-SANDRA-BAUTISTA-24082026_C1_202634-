# Agrupamiento de los patrones de demanda de las estaciones del Metro de Medellín mediante k-means y agrupamiento jerárquico

## Introducción

En las actividades anteriores construimos sobre el sistema de transporte masivo de
Medellín un buscador de rutas entre estaciones y un árbol de decisión que predice la
congestión de cada estación por hora. Ambos trabajos parten de categorías que nosotros
definimos de antemano, como el tipo de zona de cada estación. En esta actividad
invertimos la pregunta: si miramos solo cómo se reparte la demanda a lo largo del día,
sin decirle al computador qué tipo de estación o de día es cada caso, ¿qué patrones
aparecen por sí solos?

Esa es la tarea del aprendizaje no supervisado, que busca estructura en datos que no
tienen una respuesta conocida (Hastie et al., 2009). Su técnica más usada es el
agrupamiento, que reúne en un mismo grupo los casos parecidos y separa los distintos
(Palma Méndez y Marín Morales, 2008). Para un operador de transporte, conocer esos
patrones permite programar la frecuencia de los trenes y el personal de cada estación
según su comportamiento real, y no según una clasificación supuesta.

Este documento presenta el modelo que desarrollamos: un agrupamiento de los perfiles
horarios de demanda de las estaciones de las líneas A y B del Metro de Medellín. Primero
se exponen los objetivos y el marco teórico; después se describen los datos, la
implementación en Python y las pruebas; y al final se presentan los resultados, los
enlaces de la entrega y las conclusiones.

## Objetivos

### Objetivo general

Identificar, mediante técnicas de agrupamiento, los patrones de demanda horaria que
presentan las estaciones del Metro de Medellín, sin utilizar etiquetas previas.

### Objetivos específicos

1. Identificar y describir las fuentes de datos disponibles sobre la demanda del sistema de transporte masivo de Medellín.
2. Transformar la afluencia horaria por estación en perfiles diarios comparables entre estaciones de distinto tamaño.
3. Implementar en Python el agrupamiento con k-means y con el método jerárquico de Ward, y determinar el número de grupos adecuado.
4. Validar la calidad y el significado de los grupos mediante medidas internas, medidas externas y pruebas automáticas.

## Marco teórico

### Aprendizaje no supervisado

En el aprendizaje supervisado cada ejemplo de entrenamiento trae la respuesta correcta,
y el modelo aprende a reproducirla. En el aprendizaje no supervisado los ejemplos no
tienen respuesta: el algoritmo debe encontrar regularidades en los datos por sí mismo
(Russell y Norvig, 2021). Como no hay una salida correcta con la cual comparar, evaluar
estos modelos exige criterios propios, que miden la estructura encontrada o la
contrastan con conocimiento externo (Hastie et al., 2009).

### Técnicas de agrupamiento

El agrupamiento divide un conjunto de casos en grupos de modo que los casos de un mismo
grupo se parezcan entre sí más que a los de otros grupos (Palma Méndez y Marín Morales,
2008). Para ello necesita una medida de distancia entre casos; la más común es la
distancia euclidiana, que exige que las variables estén en escalas comparables. Las
técnicas se dividen en dos familias principales: las de partición, que dividen los
datos en un número fijo de grupos, y las jerárquicas, que construyen una secuencia de
agrupamientos anidados (Jain, 2010).

### El algoritmo k-means

K-means es el método de partición más utilizado (Jain, 2010). Recibe el número de grupos
k y repite dos pasos hasta que los grupos dejan de cambiar: asigna cada caso al centro
más cercano y recalcula cada centro como el promedio de los casos asignados (Lloyd,
1982; MacQueen, 1967). El resultado minimiza la inercia, que es la suma de las
distancias al cuadrado de cada caso al centro de su grupo. Como el resultado depende de
los centros iniciales, se acostumbra ejecutarlo varias veces y conservar la mejor
solución.

### Agrupamiento jerárquico

El agrupamiento jerárquico aglomerativo parte de cada caso como un grupo independiente
y en cada paso une los dos grupos más cercanos, hasta formar uno solo. El criterio de
Ward une en cada paso el par de grupos cuya fusión aumenta menos la variación interna
(Ward, 1963). El proceso se representa con un dendrograma, un diagrama en forma de árbol
que muestra a qué distancia se une cada par de grupos; cortarlo a una altura dada
produce un número determinado de grupos (Palma Méndez y Marín Morales, 2008).

### Elección del número de grupos y validación

El método del codo grafica la inercia contra el número de grupos y elige el punto donde
la curva deja de bajar de forma pronunciada (Thorndike, 1953). El coeficiente de silueta
compara, para cada caso, su distancia promedio a los miembros de su grupo con su
distancia al grupo vecino; varía entre −1 y 1, y valores más altos indican grupos más
compactos y mejor separados (Rousseeuw, 1987). Cuando se dispone de información
externa, el índice de Rand ajustado mide la coincidencia entre dos agrupamientos: vale 1
si coinciden por completo y cerca de 0 si coinciden solo por azar (Hubert y Arabie,
1985). Finalmente, el análisis de componentes principales permite proyectar datos de
muchas dimensiones en un plano para visualizarlos (Jolliffe, 2002).

## Desarrollo

### Fuentes de datos

Revisamos las fuentes públicas sobre la demanda del sistema. El Metro de Medellín
publica la afluencia de pasajeros por línea, día y hora (Metro de Medellín, s.f.), y su
informe a la Asociación Latinoamericana de Metros y Subterráneos reporta cerca de
713 000 usos diarios en las líneas A y B (Metro de Medellín, 2017). Ninguna fuente
contiene la afluencia por estación y por hora, así que reutilizamos el dataset de
muestra de la actividad anterior: 29 176 registros horarios de 27 estaciones entre el
2 de marzo y el 26 de abril de 2026, con estaciones, calendario y orden de magnitud
reales y número de pasajeros simulado. El detalle está en el documento de descripción
de los datos.

### Construcción de los perfiles

El caso que agrupamos es el perfil de una estación en un día. Para cada estación y día
sumamos los pasajeros de cada hora entre las 4:00 y las 22:00 y los dividimos entre el
total del día. Así obtuvimos 1568 perfiles de 19 valores que suman 1. Usamos fracciones
y no pasajeros para que el algoritmo compare la forma de la demanda y no el tamaño de la
estación. El tipo de día, el tipo de zona y los eventos se guardaron aparte y no se le
entregaron al algoritmo; los usamos solo para interpretar y validar los grupos.

### Implementación del modelo

El modelo está en `src/agrupamiento.py` y usa las bibliotecas scikit-learn (Pedregosa et
al., 2011) y SciPy. Sigue seis pasos:

1. Construye los perfiles y los guarda en `data/perfiles_estacion_dia.csv`.
2. Estandariza cada hora para que todas pesen lo mismo en la distancia.
3. Ejecuta k-means con valores de k entre 2 y 10, diez arranques cada uno, y calcula la inercia y la silueta.
4. Detecta el codo de la curva de inercia de forma automática y agrupa con ese valor de k.
5. Repite el agrupamiento con el método jerárquico de Ward y compara ambos resultados.
6. Nombra cada grupo según el tipo de día y de zona que predomina en él, y guarda las métricas, las asignaciones y los gráficos.

El archivo `src/consultar.py` permite ver desde la línea de comandos en qué grupos queda
una estación según el día.

### Pruebas

Verificamos el componente con la evaluación del agrupamiento, con 17 pruebas automáticas
en pytest (6 sobre la calidad de los perfiles y 11 sobre el comportamiento del
agrupamiento) y con consultas manuales. Las 17 pruebas se aprobaron. El detalle está en
el documento de pruebas realizadas.

## Resultados

El codo de la curva de inercia se encuentra en k = 5: de 4 a 5 grupos la inercia cae
1481 unidades, y de 5 a 6, solo 266. La silueta con cinco grupos es 0,308. La Tabla 1
describe los grupos encontrados.

**Tabla 1**

*Grupos encontrados por k-means*

| Grupo | Nombre | Perfiles | Porcentaje | Hora pico |
|---|---|---|---|---|
| 1 | Laboral residencial | 444 | 28,3 % | 6:00 |
| 2 | Laboral centro | 401 | 25,6 % | 17:00 |
| 3 | Laboral mixta | 205 | 13,1 % | 17:00 |
| 4 | Sábado | 214 | 13,6 % | 12:00 |
| 5 | Domingo y festivo | 304 | 19,4 % | 17:00 |

La Figura 1 muestra el perfil medio de cada grupo. Las estaciones de barrios
residenciales concentran su demanda a las 6:00, cuando la gente sale a trabajar; las del
centro, a las 17:00, cuando regresa; las mixtas tienen dos picos moderados; y los fines
de semana reparten la demanda a lo largo del día.

**Figura 1**

*Perfil horario medio de cada grupo*

![Perfiles por grupo](../resultados/perfiles_por_grupo.png)

El método jerárquico de Ward produjo prácticamente los mismos grupos: el índice de Rand
ajustado entre ambos métodos es 0,999. Al comparar los grupos con el tipo de día y de
zona, información que el algoritmo nunca vio, el índice es 0,955. Las pocas diferencias
tienen una explicación: 30 perfiles de las estaciones Estadio y Suramericana en días de
partido quedaron en el grupo del centro, porque el evento les produce un pico de tarde
igual al de una estación de oficinas. El algoritmo descubrió ese efecto por su cuenta.

## Enlaces de la entrega

La Tabla 2 presenta los enlaces al repositorio y al video. La docente fue agregada como
colaboradora del repositorio para que pueda revisar el código y dejar comentarios.

**Tabla 2**

*Enlaces de la entrega*

| Elemento | Enlace |
|---|---|
| Repositorio Git | {{REPO}} |
| Video explicativo | {{VIDEO}} |

Los cinco elementos solicitados se encuentran en el repositorio, como lo muestra la Tabla 3.

**Tabla 3**

*Ubicación de los entregables en el repositorio*

| N.º | Entregable | Ubicación |
|---|---|---|
| 1 | Archivos de fuentes de datos | {{ARCHIVO:data/afluencia_metro_medellin.csv}}, {{ARCHIVO:data/perfiles_estacion_dia.csv}}, {{ARCHIVO:data/estaciones.csv}}, {{ARCHIVO:data/generar_dataset.py}} |
| 2 | Código fuente en Python | {{ARCHIVO:src/agrupamiento.py}}, {{ARCHIVO:src/consultar.py}} |
| 3 | Documento con la descripción de los datos | {{ARCHIVO:docs/Descripcion_de_los_datos.pdf}} |
| 4 | Documento con las pruebas realizadas | {{ARCHIVO:docs/Pruebas_realizadas.pdf}}, {{CARPETA:tests}} |
| 5 | Video | {{VIDEO}} |

## Conclusiones

El agrupamiento encontró cinco patrones de demanda claros sin recibir ninguna etiqueta:
días laborales en zonas residenciales, en el centro y en zonas mixtas, sábados, y
domingos y festivos. Que dos métodos tan distintos como k-means y el agrupamiento
jerárquico de Ward llegaran casi a los mismos grupos indica que esa estructura está en
los datos y no es un efecto del algoritmo elegido.

Elegir el número de grupos requirió combinar criterios. La silueta favorecía tres
grupos, una división correcta pero gruesa que mezcla las estaciones del centro con las
mixtas; el codo indicaba cinco, con una silueta casi igual y grupos más útiles para la
operación. En el aprendizaje no supervisado las medidas orientan la decisión, pero la
interpretación del dominio la completa.

El hallazgo de los días de partido muestra el valor práctico del método: sin saber que
había eventos, el algoritmo notó que esas estaciones cambian de comportamiento. En un
sistema real, ese tipo de hallazgo sirve para detectar situaciones atípicas y ajustar la
operación.

La principal limitación es que los perfiles provienen de datos simulados, construidos
a partir de los mismos tipos de zona y de día que el algoritmo terminó recuperando. Con
la afluencia real por estación los grupos serían menos nítidos y podrían aparecer
patrones nuevos. El paso siguiente es usar estos grupos como variable en el modelo de
congestión de la actividad anterior y en el buscador de rutas.

## Referencias

Hastie, T., Tibshirani, R., y Friedman, J. (2009). *The elements of statistical learning: Data mining, inference, and prediction* (2.ª ed.). Springer. https://doi.org/10.1007/978-0-387-84858-7

Hubert, L., y Arabie, P. (1985). Comparing partitions. *Journal of Classification, 2*(1), 193–218. https://doi.org/10.1007/BF01908075

Jain, A. K. (2010). Data clustering: 50 years beyond K-means. *Pattern Recognition Letters, 31*(8), 651–666. https://doi.org/10.1016/j.patrec.2009.09.011

Jolliffe, I. T. (2002). *Principal component analysis* (2.ª ed.). Springer. https://doi.org/10.1007/b98835

Lloyd, S. (1982). Least squares quantization in PCM. *IEEE Transactions on Information Theory, 28*(2), 129–137. https://doi.org/10.1109/TIT.1982.1056489

MacQueen, J. (1967). Some methods for classification and analysis of multivariate observations. En L. M. Le Cam y J. Neyman (Eds.), *Proceedings of the Fifth Berkeley Symposium on Mathematical Statistics and Probability* (Vol. 1, pp. 281–297). University of California Press.

Metro de Medellín. (s.f.). *Pasajeros movilizados: afluencia* [Conjunto de datos]. Datos Abiertos Colombia. https://www.datos.gov.co/Transporte/Pasajeros-Movilizados-Afluencia/9dbb-kbnv

Metro de Medellín. (2017). *Metro de Medellín* [Informe]. Asociación Latinoamericana de Metros y Subterráneos. https://alamys.org/wp-content/uploads/2021/04/Metro-de-Medellin.pdf

Palma Méndez, J. T., y Marín Morales, R. L. (Coords.). (2008). *Inteligencia artificial: Métodos, técnicas y aplicaciones*. McGraw-Hill.

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., y Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830.

Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics, 20*, 53–65. https://doi.org/10.1016/0377-0427(87)90125-7

Russell, S., y Norvig, P. (2021). *Artificial intelligence: A modern approach* (4.ª ed.). Pearson.

Thorndike, R. L. (1953). Who belongs in the family? *Psychometrika, 18*(4), 267–276. https://doi.org/10.1007/BF02289263

Ward, J. H., Jr. (1963). Hierarchical grouping to optimize an objective function. *Journal of the American Statistical Association, 58*(301), 236–244. https://doi.org/10.1080/01621459.1963.10500845
