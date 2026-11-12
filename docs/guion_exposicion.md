# Guion de la exposición · 15 minutos

**Reparto:** cada integrante habla unos 5 minutos.
- **Integrante 1:** abre, presenta el negocio y cierra con la recomendación.
- **Integrante 2:** explica las fuentes y el ETL.
- **Integrante 3:** presenta el DW y hace la demo del dashboard.

**Qué hay en pantalla:**
- la presentación (`docs/presentacion/Presentacion_AE4_Agro_NEA.pptx`, 13 diapositivas más 3 de respaldo). El texto de cada bloque está en las notas del orador;
- el dashboard en vivo durante la demo.

El que no habla maneja la computadora.

## Antes de empezar (15 minutos antes)

- [ ] Docker Desktop abierto y `docker compose up -d` corriendo. Esperar a que http://localhost:8088 cargue.
- [ ] Iniciar sesión en Superset (`admin` / `admin`) y dejar abierto el dashboard con los filtros por defecto: campaña **2024/2025**, cultivo **soja total**, sin provincia.
- [ ] Tener la presentación abierta en modo presentación, en la diapositiva 1.
- [ ] **Plan B:** si falla Docker o la red, la demo se hace con las diapositivas de respaldo 14 a 16.
- [ ] Un cronómetro a la vista.

## Cronograma

| Tiempo | Quién | Bloque | Pantalla |
|---|---|---|---|
| 0:00 – 1:00 | Integrante 1 | Apertura | Diapositivas 1 a 3 |
| 1:00 – 3:00 | Integrante 1 | Definición del negocio | Diapositivas 4 y 5 |
| 3:00 – 4:30 | Integrante 2 | Las dos fuentes | Diapositiva 6 |
| 4:30 – 8:00 | Integrante 2 | ETL: problemas, limpieza y merge | Diapositivas 7 y 8 |
| 8:00 – 10:00 | Integrante 3 | Data Warehouse | Diapositiva 9 |
| 10:00 – 13:00 | Integrante 3 | Dashboard en vivo y hallazgos P1–P3 | Diapositiva 10, después Superset |
| 13:00 – 14:30 | Integrante 1 | P4 y recomendación | Diapositivas 11 y 12 |
| 14:30 – 15:00 | Integrante 1 | Limitaciones y cierre | Diapositiva 13 |

**Controles de tiempo:**
- a los **4:30** tiene que empezar el ETL;
- a los **8:00**, el DW;
- a los **10:00**, el dashboard;
- a los **13:00**, la recomendación.

Si van atrasados, recorten lo marcado con ✂. Si van adelantados, agreguen lo marcado con ➕.

---

## 1. Apertura · 0:00 – 1:00 · Integrante 1

> Buenos días. Somos [nombres] y les vamos a presentar nuestro trabajo integrador: *Producción agrícola del NEA y lluvia*.
> La pregunta que guía todo el trabajo es simple: ¿cuánto depende de la lluvia la agricultura del noreste argentino?
> Elegimos el tema porque nos toca de cerca. El NEA produce toda la yerba mate y el té del país y la mitad del arroz, y en el Chaco hay una agricultura grande de soja, maíz y algodón que es casi toda de secano, o sea, sin riego. En los últimos años hubo sequías muy fuertes.
> Para responder la pregunta cruzamos dos fuentes de datos abiertos, armamos un ETL en Python, un Data Warehouse en PostgreSQL y un dashboard en Superset. Vamos por partes.

## 2. Definición del negocio · 1:00 – 3:00 · Integrante 1

> Planteamos cuatro preguntas concretas.
> - **P1:** cuánto rinden la soja, el maíz, el algodón y el sorgo en campañas secas frente a las normales y las húmedas.
> - **P2:** qué parte de lo sembrado no se cosechó, y en qué departamentos.
> - **P3:** qué campañas fueron secas, y en qué meses faltó la lluvia.
> - **P4:** qué peso tiene el NEA en la producción nacional.
>
> Para medirlo definimos tres KPIs.
>
> El **principal** es el rendimiento comparado con las cinco campañas anteriores: toneladas sobre hectáreas cosechadas de la campaña, dividido por lo mismo de las cinco campañas anteriores, en el mismo cultivo y departamento. Si da 100 %, rindió igual que siempre.
> ¿Por qué las cinco anteriores y no el promedio de todo el período? Porque el rendimiento crece con la tecnología: el maíz hoy rinde casi el doble que en 2000. Comparar contra un promedio fijo castigaría a los primeros años.
>
> El segundo KPI es la lluvia de octubre a marzo comparada con lo normal del departamento. El tercero es la superficie perdida: lo que se sembró y no se cosechó.
>
> Trabajamos con tres supuestos:
> 1. La campaña va de julio a junio.
> 2. Para los cultivos de verano importa la lluvia de octubre a marzo. Llamamos *seca* a una campaña con menos del 80 % de lo normal, y *húmeda* a una con más del 120 %.
> 3. La lluvia de un departamento es la que estima la NASA en su punto central.
>
> El alcance va de la campaña 2000/01 a la 2024/25.

## 3. Las dos fuentes · 3:00 – 4:30 · Integrante 2

> Usamos dos fuentes reales, como pide la consigna.
>
> La primera son las **Estimaciones agrícolas** de la Secretaría de Agricultura: un CSV de 160 mil filas con superficie sembrada, cosechada y producción por cultivo, campaña y departamento, desde 1969.
>
> La segunda es el **clima diario de la NASA**, de su servicio POWER. Le pedimos la lluvia de cada día, de 2000 a 2025, en el punto central de cada uno de los 76 departamentos del NEA. Son 76 archivos y casi 700 mil filas.
>
> Lo importante es la **clave que las une: el código INDEC del departamento**. Son cinco dígitos: dos de provincia y tres de departamento. En las estimaciones está en una columna; en la NASA lo usamos como nombre de cada archivo al descargarlo. Por ejemplo, 54098 es San Ignacio, en Misiones.
>
> Los archivos originales están en `data/raw`, tal cual se descargaron, así que no hace falta internet para reproducir el trabajo.

## 4. ETL · 4:30 – 8:00 · Integrante 2

> Antes de limpiar, exploramos los datos con un script y encontramos varias trampas.
>
> **La más importante es un doble conteo.** El archivo trae "soja total", pero también "soja primera" y "soja segunda". Comprobamos que el total es la suma de las dos en el 99,6 % de los casos, así que si sumábamos todo, la soja contaba doble. Pasa lo mismo con el trigo y el poroto. Por eso nos quedamos solo con los totales.
>
> **La columna año cambia de significado según el cultivo:** en yerba y té es el año en que termina la campaña, y en el resto, el año en que empieza. Por eso usamos la columna campaña.
>
> **Hay departamentos "sin definir"**, con código terminado en 000, cuando la Secretaría solo sabe la provincia. Los mantuvimos como un departamento especial de cada provincia, para que los totales provinciales den exactos.
>
> **Con los ceros decidimos con criterio.** Excluimos 24 filas que tenían todo en cero, porque no aportan nada. Pero conservamos 2.533 filas donde se sembró y no se cosechó nada: son pérdidas totales por sequía, justo lo que queremos medir.
> También rechazamos 4 rendimientos imposibles. Por ejemplo, una soja de casi 20 mil kilos por hectárea, ocho veces lo normal.
>
> **Ahora, el merge.** El problema es que las fuentes tienen distinto detalle: la producción es una fila por campaña y la lluvia, una por día. Si las cruzábamos así nomás, cada fila de producción se repetía 365 veces. Entonces primero sumamos la lluvia de octubre a marzo de cada departamento y campaña, y después cruzamos por **departamento más campaña**.
>
> **Usamos LEFT JOIN** porque la producción no puede perder filas. Si una fila no encuentra lluvia, queda con un nulo que se cuenta y se informa. Con un INNER JOIN, esa fila desaparecería sin que nadie se entere.
>
> **Después de cada cruce validamos** filas antes y después, duplicados, nulos y claves sin match. El cruce de producción con lluvia dio 97,75 %. Lo que no cruza son justo los cuatro "sin definir", que no tienen un punto para pedirle el clima a la NASA. Todo eso queda impreso y guardado en la carpeta `validaciones`.

✂ Si van atrasados, salteen el ejemplo de la soja de 20 mil kilos.
➕ Si van adelantados, abran `data/processed/validaciones/log_etl.txt` y muestren el bloque de un merge.

## 5. Data Warehouse · 8:00 – 10:00 · Integrante 3

> Con los datos limpios armamos el Data Warehouse en PostgreSQL. Es un **modelo estrella con dos tablas de hechos** que comparten dimensiones.
> ¿Por qué dos? Porque tienen distinto grano: `fact_produccion` tiene una fila por cultivo, departamento y campaña, y `fact_clima_diario` una fila por departamento y día. No pueden ir en la misma tabla.
>
> Las dimensiones son tres:
> - `dim_tiempo`, con un registro por día y los atributos día, mes, trimestre, año y campaña;
> - `dim_departamento`, que es la que une las dos fuentes;
> - `dim_cultivo`.
>
> Hay dos decisiones para destacar.
> - **Uno:** como la producción es anual, la anclamos al 1 de julio en que empieza la campaña. Así las dos tablas de hechos usan la misma dimensión de tiempo y se cruzan por campaña.
> - **Dos:** el rendimiento no se guarda en la tabla de hechos, porque es un cociente y no se puede sumar. Guardamos hectáreas y toneladas, que sí son aditivas, y el rendimiento se calcula siempre como cociente de sumas.
>
> Además hay claves primarias y foráneas, controles CHECK, índices, un usuario de solo lectura para Superset y tres vistas que alimentan el dashboard.
> Después de cargar corremos un script de validación: da cero claves huérfanas, y los totales coinciden con los del ETL.

## 6. Dashboard en vivo · 10:00 – 13:00 · Integrante 3

**Paso 1. Vista general** (arriba de todo):

> Este es el dashboard en Superset. Arriba están los tres KPIs, con el principal destacado, y a la izquierda tres filtros: campaña, provincia y cultivo. Por defecto muestra la última campaña, 2024/25, y la soja.
> En 2024/25 la soja del NEA rindió apenas el **51 %** de lo que venía rindiendo, llovió el **73 %** de lo normal y se perdió el **35,4 %** de lo sembrado.

**Paso 2. Gráfico P1** (barras verde, gris y rojo):

> Este gráfico responde la P1. Agrupa todas las campañas según cuánto llovió.
> En las campañas secas, en rojo, la soja rinde 84 %, el maíz 82 % y el sorgo 83 %. En las húmedas, en verde, rinden entre 107 y 116 %.
> El arroz, que se riega, no sigue el patrón: funciona como grupo de control y confirma que la diferencia viene del agua.

**Paso 3. Cambiar filtros:** campaña **2022/2023** y cultivo **maíz**, después *Aplicar*. Los KPIs pasan a **67 %**, **62 %** y **24,2 %**.

> 2022/23 fue la campaña más seca del período: llovió el 62 % de lo normal. El maíz rindió 67 % y se perdió casi un cuarto de lo sembrado.

**Paso 4. Mapa de calor P3:**

> Este mapa responde la P3: cada fila es una campaña y cada columna, un mes. Marrón significa que llovió menos de lo normal. En 2022/23 se ve que faltó la lluvia de noviembre a febrero, justo los meses de siembra y crecimiento.

**Paso 5. Tabla P2:** volver a campaña **2024/2025** y cultivo **soja total**.

> La P2: esta tabla muestra los departamentos que más perdieron en la campaña elegida. Son todos del Chaco: Almirante Brown, 12 de Octubre, Chacabuco. Y el gráfico de barras muestra que la pérdida de soja se dispara en las campañas secas: 42 % en 2011/12 y 35 % en 2024/25.

✂ Si van atrasados, salteen el paso 3 y cuenten el dato de 2022/23 directamente en el mapa.
➕ Si van adelantados, filtren la provincia **Chaco**: los KPIs pasan a 48 %, 76 % y 37 %.

## 7. P4 y recomendación · 13:00 – 14:30 · Integrante 1

Bajen hasta el gráfico P4 (las líneas).

> La P4 es sobre el peso del NEA en el país. Mantiene el 100 % de la yerba y el té, y la mitad del arroz, pero perdió el algodón: pasó de producir el 70 % del país al 25 %.
>
> Con todo esto, nuestra recomendación tiene tres puntos:
> 1. Tratar la sequía como el principal riesgo de la agricultura de secano del Chaco. En campañas secas se pierde hasta un tercio de lo sembrado, así que hay que priorizar los departamentos que más pierden para seguros, reservas de agua y variedades tolerantes.
> 2. Usar la lluvia de noviembre a febrero como alerta temprana, porque el déficit aparece meses antes de la cosecha.
> 3. Investigar por qué el algodón se fue del NEA: nuestros datos lo muestran, pero no lo explican.

## 8. Limitaciones y cierre · 14:30 – 15:00 · Integrante 1

> Somos honestos con los límites del trabajo. La lluvia sale de un modelo satelital, la producción es anual, y en 2023/24 llovió normal y aun así la soja rindió la mitad: el clima no explica todo.
> Todo el trabajo se reproduce desde cero con un solo comando. Muchas gracias; quedamos atentos a sus preguntas.

---

## Preguntas probables (las tienen que poder responder los tres)

| Pregunta | Respuesta corta |
|---|---|
| ¿Cuáles son las dos fuentes y cómo se cruzan? | Las estimaciones agrícolas y la lluvia de la NASA. Se cruzan por el código INDEC del departamento, y para el análisis por departamento + campaña, después de sumar la lluvia por campaña. |
| ¿Por qué LEFT JOIN y no INNER? | Para no perder producción. Lo que no cruza queda con un nulo y se informa. Con INNER desaparecería sin aviso. |
| ¿Cómo saben que el merge no duplicó filas? | Se controlan las filas antes y después, y `validate="many_to_one"` frena el ETL si la clave de la derecha está repetida. Dio 0 duplicados en los cuatro cruces. |
| ¿Por qué no guardan el rendimiento? | Es un cociente y no se puede sumar. Se guardan hectáreas y toneladas, y el rendimiento se calcula como Σ toneladas ÷ Σ hectáreas. |
| ¿Por qué dos tablas de hechos? | Tienen distinto grano: campaña y día. Comparten tiempo y departamento. |
| ¿Por qué la producción tiene fecha 1 de julio? | La campaña empieza el 1 de julio. Así las dos tablas de hechos usan la misma DimTiempo y se cruzan por el atributo campaña. |
| ¿Cómo evitaron el doble conteo? | Soja total = soja 1ra + 2da (verificado en el 99,6 %). Usamos solo los totales. |
| ¿Por qué comparan contra las 5 campañas anteriores? | Por la tendencia tecnológica: el maíz rinde casi el doble que en 2000. Contra un promedio fijo, los primeros años darían siempre bajos. |
| ¿Por qué octubre a marzo, y 80 % / 120 %? | Octubre a marzo es el ciclo de los cultivos de verano. Los umbrales son un criterio simple y simétrico, documentado como supuesto. |
| ¿Qué pasa con los departamentos "sin definir"? | Se cargan como un departamento especial de cada provincia, para que los totales den exactos. No tienen clima. |
| ¿Por qué el arroz no cae en las campañas secas? | Se riega: no depende de la lluvia. Funciona como grupo de control. |
| ¿Qué es Superset y por qué Docker? | Superset es una herramienta de dashboards de código abierto (equivalente a Power BI) que consulta el DW por SQL. Docker levanta PostgreSQL y Superset con un comando, igual en cualquier PC. |
| ¿Qué limitaciones tiene? | Lluvia modelada (grilla de unos 55 km), producción anual, yerba y té solo hasta 2023/24, y factores que no están en los datos (plagas, calor, precios). |

**Consejo:** ensayen dos veces con cronómetro antes del día. Si un bloque se pasa más de 20 segundos, recorten la parte marcada con ✂ en vez de hablar más rápido.
