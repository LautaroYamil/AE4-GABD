# Hallazgos y recomendación

Las cifras salen de `sql/05_consultas_analiticas.sql` y son las mismas que muestra el dashboard.

## P1 · ¿Cuánto rinden los cultivos del NEA en campañas secas, normales y húmedas?

Rendimiento comparado con el promedio de las 5 campañas anteriores del mismo departamento, entre 2000/01 y 2024/25:

| Cultivo | Seca | Normal | Húmeda |
|---|---|---|---|
| Maíz | 82 % | 101 % | 116 % |
| Sorgo | 83 % | 96 % | 108 % |
| Soja | 84 % | 98 % | 114 % |
| Algodón | 90 % | 108 % | 115 % |
| Arroz (con riego) | 102 % | 107 % | 95 % |

- En una campaña seca, los cultivos de secano rinden entre un 10 % y un 18 % menos que su promedio reciente. En una húmeda, entre un 8 % y un 16 % más.
- El arroz, que se riega, no sigue ese patrón. Eso confirma que la diferencia viene del agua.
- **La soja del NEA en las últimas campañas:**
  - 2022/23 rindió 78 %, con 62 % de la lluvia normal.
  - 2023/24 rindió 53 %, aunque llovió 126 %. La caída no se explica por la lluvia (ver limitaciones).
  - 2024/25 rindió 51 %, con 73 % de la lluvia normal.

## P2 · ¿Qué parte de lo sembrado no se cosechó?

- En los cultivos de secano del NEA, la superficie perdida queda por debajo del 9 % en 15 de las 25 campañas.
- **Se dispara en campañas secas:**
  - 2008/09: 19,6 %
  - 2011/12: 34,0 %
  - 2024/25: 32,9 % (476.661 ha)
- También fue alta en 2012/13 (18,5 %) y 2023/24 (21,9 %), con lluvia normal o alta: la sequía no es la única causa de pérdida.
- **Los departamentos con más hectáreas perdidas en campañas secas son todos del Chaco:**
  - Almirante Brown: 340.650 ha, el 23,7 % de lo sembrado
  - 12 de Octubre: 133.723 ha
  - Chacabuco: 127.856 ha

## P3 · ¿Qué campañas fueron secas, y en qué meses faltó la lluvia?

- **La campaña 2022/23 fue la más seca del período:**
  - Llovió el 62 % de lo normal entre octubre y marzo.
  - Los 25 departamentos de Chaco y los 25 de Corrientes quedaron en "seca".
  - Lo que faltó fue la lluvia de noviembre a febrero, los meses clave para la siembra y el crecimiento: noviembre 43 %, diciembre 44 %, enero 58 % y febrero 50 % de lo normal.
- **Otras campañas secas:** 2011/12, 2024/25 y 2021/22. En 2024/25, los 17 departamentos de Misiones quedaron en "seca".

## P4 · ¿Qué participación tiene el NEA en la producción nacional?

Promedio de 5 campañas al comienzo y al final del período:

| Cultivo | 2000/01 – 2004/05 | 2020/21 – 2024/25 |
|---|---|---|
| Yerba mate y té | 100 % | 100 % |
| Arroz | 50,3 % | 51,3 % |
| **Algodón** | **70,3 %** | **25,4 %** |
| Girasol | 9,2 % | 6,0 % |
| Soja | 3,4 % | 2,4 % |

El NEA perdió el liderazgo del algodón: pasó de producir 7 de cada 10 toneladas del país a producir 1 de cada 4.

## Recomendación

1. **Agricultura de secano y sequía.** En el Chaco, la sequía es el principal riesgo productivo. En campañas secas se pierde hasta un tercio de lo sembrado. Conviene priorizar los departamentos con más pérdidas (Almirante Brown, 12 de Octubre, Chacabuco) para seguros agrícolas, reservas de agua y siembra de variedades tolerantes.
2. **Seguimiento de la lluvia.** El déficit se ve en noviembre–diciembre, antes de la cosecha. Seguir la lluvia de esos meses permite anticipar la caída de rendimiento y de superficie cosechada.
3. **Algodón.** Habría que investigar por qué el algodón se desplazó fuera del NEA: este análisis no lo explica.

**Limitaciones:** ver `docs/decisiones.md`. La caída de 2023/24 con lluvia normal muestra que el clima no explica todo. Hay que verificar con otra fuente qué pasó esa campaña (por ejemplo, la chicharrita del maíz) antes de afirmarlo.
