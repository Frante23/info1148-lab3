# Correspondencia con la pauta y la rúbrica

La comprobación de abajo indica dónde se desarrolla cada exigencia. No es una calificación: permite revisar que el PDF, las gramáticas y las evidencias describan el mismo trabajo.

| Exigencia | Ubicación del informe | Evidencia verificable |
|---|---|---|
| Terminales clasificados, no terminales, inicio y G=(V,Σ,P,S), 20 puntos | 2.1 a–e | Especificación y reglas léxicas de `scripts/gramatica.py` |
| Explicar por qué no enumerar identificadores y números | 2.1 e | Patrones, reservadas, valores nuevos, casos de límites |
| Encabezado, asignaciones simples y aritméticas, salida, cinco operadores, una o más instrucciones, 30 puntos | 2.2 a–b y justificación de la construcción | 19 alternativas base; explicación inductiva de la lista; comparación de tres formas de instrucción; restricciones de cada regla |
| Función de cada no terminal | 2.2 b | Tabla individual de los 11 no terminales |
| Programa de referencia completo | 2.2 c | Caso REF; derivación íntegra y árbol en evidencias/derivaciones/programa_referencia; 20 instrucciones, 6 simples, 7 aritméticas y 7 salidas |
| Derivaciones por la izquierda, 25 puntos | 2.3 a–b | JSON y tablas generadas; cada sustitución se verifica |
| Árbol de `z = x + y #` y relación entre nodos | 2.3 c–d | Árbol anotado, SVG y árbol del BruteParser original |
| Tres cadenas adicionales | 2.3 e | P3_1 a P3_3, aceptadas y justificadas |
| Ocho casos y errores concretos, 25 puntos | 2.4 | P4_1 a P4_8; tabla con posición conceptual del error y corrección |
| Extensión creativa incorporada formalmente | 3 | Nuevos terminales, no terminales, cuatro alternativas, G', ejemplo válido, inválido, derivación y programa completo |
| Conclusiones concretas | 4 | Hallazgos sobre orden, terminadores, contexto de análisis y límite entre sintaxis y semántica |
| Informe PDF y enlace a archivos de JFLAP | 5 y anexos | PDF final; cuatro JFF; repositorio público |
| Consistencia de notación y evidencia legible | Todo el documento | Tabla de equivalencias, adaptador S→I documentado, comprobación de XML y árboles |

## Decisiones que deben conservarse

- El inicio principal es programa, no una unión informal de programa e instrucción. Para fragmentos se deriva desde I; las copias JFLAP emplean el adaptador S→I.
- ID y NUM son terminales de categoría. Sus lexemas son atributos, no producciones añadidas después de diseñar la gramática.
- La gramática acepta una sola operación binaria por asignación y no define precedencia ni paréntesis.
- Se admite cero porque aparece en la pauta. No se admite signo unario ni exponentes.
- Los comentarios del programa se reconocen antes del parser y no se borran pegando identificadores.
- La barra del caso 8 se interpreta como separador de línea. La lectura literal se documenta y se rechaza por separado.
- `entero` y `real` se reservan en la extensión; la conservación de producciones no implica que esas palabras sigan siendo identificadores válidos.
- Las vistas JFLAP se generan con su componente original, y las validaciones no dependen de lo que diga una imagen.
- La prueba de 82 casos no se presenta como una demostración de equivalencia general. El informe justifica el alcance de cada regla.
