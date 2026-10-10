# Guion del video · Actividad 4 (máximo 10 minutos)

Julian: bloques 1 y 2 (0:00 – 3:30). Alejo: bloques 3 y 4 (3:30 – 9:30).
En **negrita**, lo que se hace en pantalla; entre comillas, lo que se dice.

**Antes de grabar, Alejo deja abiertos:**
- VS Code con la carpeta del proyecto (**File → Open Folder**, la carpeta que tiene `src`, `data` y `tests`) y la terminal abajo (**Terminal → New Terminal**);
- el archivo `src/agrupamiento.py`;
- el archivo `docs/Pruebas_realizadas.pdf` en el navegador.

Si las librerías no están instaladas, primero corre:
```
python -m pip install -r requirements.txt
```

---

## JULIAN

### Bloque 1 · El proyecto (0:00 – 1:30)

**Pantalla: página del repo en GitHub, en la rama de la actividad 4, con el README.**

> "Hola, somos Julian Vega y Alejandro Mora, y esta es la actividad 4 de Inteligencia Artificial: métodos de aprendizaje no supervisado.
>
> En la actividad anterior hicimos un árbol de decisión que predecía la congestión de las estaciones del Metro de Medellín. Ese modelo era supervisado: le dábamos ejemplos con la respuesta y aprendía a repetirla. Pero esa respuesta partía de categorías que nosotros inventamos, como decir que una estación es residencial o del centro.
>
> Ahora hicimos la pregunta al revés: si solo miramos cómo se reparte la demanda durante el día, sin decirle nada más al computador, ¿qué grupos de estaciones aparecen solos? Eso es aprendizaje no supervisado, y la técnica se llama agrupamiento, que es el tema del capítulo 16 del libro de Palma Méndez."

### Bloque 2 · Los datos (1:30 – 3:30)

**Pantalla: entra a `docs` → `Descripcion_de_los_datos.pdf`, Tabla 1.**

> "Revisamos las mismas fuentes públicas de la actividad anterior. El Metro publica la afluencia por línea, pero no por estación, así que reutilizamos nuestro dataset de muestra: 29 mil registros horarios de las 27 estaciones de las líneas A y B durante ocho semanas. Las estaciones y el calendario son reales; los pasajeros, simulados."

**Pantalla: entra a `data` → `perfiles_estacion_dia.csv`.**

> "Para agrupar transformamos esos datos en perfiles. Cada fila es una estación en un día, y las columnas de h04 a h22 dicen qué porcentaje de la gente de ese día entró en cada hora. Son 1568 perfiles.
>
> Usamos porcentajes y no número de pasajeros para que el algoritmo compare la forma del día y no el tamaño. Si no, San Antonio quedaría sola por ser la más grande.
>
> Las columnas de tipo de día y tipo de zona están en el archivo, pero NO se las damos al algoritmo. Solo las usamos al final para comprobar si los grupos tienen sentido.
>
> Ahora Alejo les muestra el código y los resultados."

**Dejas de compartir pantalla.**

---

## ALEJO

### Bloque 3 · El código (3:30 – 6:30)

**Pantalla: `src/agrupamiento.py`, bajando despacio.**

> "El código hace seis pasos. Uno, construye los perfiles. Dos, estandariza cada hora para que todas pesen igual. Tres, prueba k-means con 2 hasta 10 grupos. K-means pone k centros, asigna cada perfil al centro más cercano y mueve los centros al promedio, hasta que no cambia nada. Cuatro, elige el número de grupos con el método del codo. Cinco, repite todo con otro método, el agrupamiento jerárquico de Ward, para comparar. Y seis, guarda los resultados y los gráficos."

**Pantalla: terminal. Escribe y da Enter:**
```
python src/agrupamiento.py
```

**Cuando termine:**
> "Aquí está la tabla de inercia y silueta para cada número de grupos. El programa detecta que el codo está en 5 grupos."

**Pantalla: abre `resultados/codo_silueta.png`.**

> "A la izquierda está el codo: la inercia baja mucho hasta 5 grupos y después casi no baja. A la derecha está la silueta, que mide qué tan separados están los grupos. La silueta más alta es con 3, pero esos 3 grupos son muy gruesos; con 5 la silueta es casi igual a la de 4 y los grupos dicen mucho más. Por eso elegimos 5."

**Pantalla: abre `resultados/perfiles_por_grupo.png`.**

> "Estos son los 5 grupos que encontró solo. Uno: días laborales en barrios residenciales, con el pico a las 6 de la mañana, cuando la gente sale a trabajar. Dos: días laborales en el centro, con el pico a las 5 de la tarde, cuando regresa. Tres: zonas mixtas, con dos picos. Cuatro: sábados. Y cinco: domingos y festivos, sin picos marcados."

### Bloque 4 · Resultados y pruebas (6:30 – 9:30)

**Pantalla: abre `resultados/dendrograma.png`.**

> "Este es el agrupamiento jerárquico. Va uniendo los perfiles más parecidos hasta formar un árbol, y si lo cortamos en la línea punteada quedan 5 grupos. Lo importante: coincide casi por completo con k-means, con un índice de Rand ajustado de 0,999. Dos métodos distintos llegaron a lo mismo, así que los grupos están en los datos."

**Pantalla: `Pruebas_realizadas.pdf` → Tabla 3, la del cruce de grupos.**

> "Aquí comparamos los grupos con el tipo de día y de zona, que el algoritmo nunca vio. El índice de coincidencia es de 0,955, casi total. Y lo interesante son las diferencias: 30 perfiles de las estaciones Estadio y Suramericana quedaron en el grupo del centro. ¿Por qué? Porque eran días de partido. El algoritmo descubrió solo que con partido esas estaciones se llenan en la tarde como una estación de oficinas."

**Pantalla: terminal.**
```
python src/consultar.py --estacion Estadio --dia Sábado
```

> "Aquí se ve en un caso: los sábados sin partido, Estadio se comporta como sábado; con partido, como el centro."

**Pantalla: terminal.**
```
python -m pytest tests -v
```

> "Y tenemos 17 pruebas automáticas: 6 revisan los perfiles y 11 el agrupamiento. Todas pasan.
>
> Para cerrar: sin darle ninguna etiqueta, el agrupamiento encontró cinco patrones claros de demanda y hasta detectó los días de partido. La limitación es que los datos son simulados; con datos reales los grupos serían menos nítidos. Todo está en el repositorio. Gracias."

**Detienen la grabación.**
