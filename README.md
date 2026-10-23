# Laboratorio 3 Diseño y validación de gramáticas

INFO1148 Teoría de la Computación, segundo semestre de 2026. Profesor Marcos Lévano.

Franco Oyarzo Calisto y Vicente Rivera Sánchez (**jefe de pareja**).

Diseñamos una GLC para programas con asignaciones simples, operaciones binarias y salidas. La extensión agrega declaraciones con `entero` y `real`. El informe desarrolla cada pregunta de la pauta, con producciones, derivaciones por la izquierda, árbol, diagnóstico de los ocho casos y ejemplos de la extensión.

## Entrega

- **[Informe final en PDF](informe/Lab_03_JefeGrupo_vicente_rivera.pdf)**
- [Fuente LaTeX](informe/main.tex)
- [Gramática base para programas](gramaticas/gramatica_base.jff)
- [Gramática extendida para programas](gramaticas/gramatica_extendida.jff)
- [Gramática base para instrucciones](gramaticas/gramatica_base_instrucciones.jff)
- [Gramática extendida para instrucciones](gramaticas/gramatica_extendida_instrucciones.jff)
- [Correspondencia con la rúbrica](docs/revision_rubrica.md)

El PDF se entrega con el nombre `Lab_03_JefeGrupo_vicente_rivera.pdf`. El repositorio es público y el enlace se incluye en el informe. La fecha indicada por la actividad es el **25 de octubre de 2026 a las 15:00, hora de Chile**.

## Qué reconoce la gramática

Un programa comienza con `Begin Programa ID`, contiene **una o más instrucciones** y termina con `End`. Las instrucciones base son:

```text
x = 20 #
temporal = x #
z = x + y #
salida z #
```

Las operaciones admitidas son `+`, `-`, `*`, `/` y `%`; cada asignación aritmética contiene exactamente una operación binaria. Ambos operandos pueden ser identificadores o números. No se definen operaciones encadenadas, precedencia, paréntesis, signo unario ni exponentes. `salida` recibe un identificador.

Los identificadores siguen `[A-Za-z][A-Za-z0-9_]*`; los números, `[0-9]+(?:\.[0-9]+)?`. Se acepta `0`, como en el ejemplo de la pauta. Las palabras reservadas se distinguen por mayúsculas y se reconocen antes de clasificar un lexema como `ID`. Los comentarios `/* ... */` no anidados y los espacios se descartan sin unir palabras adyacentes.

El informe justifica la ausencia de ambigüedad sobre tokens: `#` fija los límites de cada instrucción, su primer token distingue salida, asignación y declaración, y el contenido después del primer operando distingue asignación simple de aritmética. Cada operando, operador y tipo tiene una alternativa determinada por su token. Esta justificación estructural cubre ambas gramáticas; la coincidencia de las pruebas por sí sola no se usa como prueba general de unicidad.

La sintaxis de las declaraciones es:

```text
entero contador #
real temperatura #
```

No incluye inicialización dentro de la declaración ni comprobación de tipos, uso previo, inicialización o ejecución de operaciones. `entero` y `real` quedan reservadas en la versión extendida.

## Cómo revisar en JFLAP 7.1

JFLAP recibe códigos de un carácter, **no el texto fuente sin transformar**. Esta correspondencia evita confundir las palabras reservadas con los nombres de los no terminales:

| Terminal | Código | Terminal | Código |
|---|---|---|---|
| `Begin` | `b` | `Programa` | `p` |
| `End` | `e` | `salida` | `s` |
| `ID` | `i` | `NUM` | `n` |
| `entero` | `t` | `real` | `r` |

Los operadores y `#` conservan su escritura. Los lexemas de `ID` y `NUM` quedan registrados por separado; no se afirma que `i` distinga `x` de `y`.

1. Abrir un `.jff` con **File → Open**.
2. Para una instrucción aislada, elegir el archivo que termina en `_instrucciones.jff`.
3. Elegir **Input → Brute Force Parse**, ingresar la cadena codificada y comenzar el análisis.
4. Avanzar hasta completar el árbol. Para verlo con más claridad se puede ampliar la ventana.

| Fuente | Entrada JFLAP | Archivo |
|---|---|---|
| `z = x + y #` | `i=i+i#` | Base para instrucciones |
| `salida z #` | `si#` | Base para instrucciones |
| `entero contador #` | `ti#` | Extendida para instrucciones |
| `Begin Programa prueba x = 5 # salida x # End` | `bpii=n#si#e` | Base para programas |

El inicio del lenguaje principal es `S → bpDLe`. Las copias para instrucciones reemplazan **solo esa regla** por `S → I`, porque el XML de JFLAP 7.1 no conserva un inicio alternativo al abrirlo. El subárbol desde `I` no cambia. Esa regla auxiliar no se añade al lenguaje de programas completos.

En el caso 8 de la pauta, interpretamos `/` como separadores de línea. La versión con saltos se acepta; si las barras se leen literalmente como división, se rechaza. Ambos resultados están documentados.

## Comprobaciones automáticas

Se requiere **Python 3.10 o posterior**, sin paquetes externos para validar:

```bash
python scripts/validar_gramatica.py --comprobar
```

Se comprueban **82 casos: 43 aceptados y 39 rechazados**. Incluyen los ocho casos de la pregunta 4, los tres de la pregunta 3, el programa completo, la extensión, los cinco operadores con combinaciones de operandos, errores de números e identificadores y los límites del programa. Dos reconocedores independientes —descendente con memoización y Earley— coinciden en cada entrada que supera el análisis léxico. Se verifican también los cuatro JFF, las producciones de cada árbol, sus hojas y los pasos por la izquierda.

El programa de referencia tiene **20 instrucciones: seis asignaciones simples, siete aritméticas y siete salidas**. No se cuenta por líneas: los conteos salen del árbol analizado.

La [derivación completa del programa](evidencias/derivaciones/programa_referencia.txt) registra cada sustitución por la izquierda, sin omitir instrucciones. Su [árbol completo en JSON](evidencias/derivaciones/programa_referencia.json) conserva los tokens, los lexemas y sus posiciones en la fuente. La sección 2.2 del informe justifica además la lista no vacía, la separación de las dos asignaciones y las restricciones del encabezado, la salida y el terminador.

Para probar otra fuente:

```bash
python scripts/comprobar_fuente.py --archivo ejemplos/programa_referencia.txt
python scripts/comprobar_fuente.py --texto "z = x + y #" --inicio instruccion --derivar
python scripts/comprobar_fuente.py --archivo ejemplos/programa_extendido.txt --extendida
```

El comando devuelve código `0` si acepta y `1` si rechaza. Una instrucción aislada necesita `--inicio instruccion`; el modo predeterminado exige un programa completo.

### Comprobación con el analizador original de JFLAP

Se requiere JDK 21 y el JAR de JFLAP 7.1, que **no se redistribuye** en el repo. Colocarlo en `.herramientas/JFLAP7.1.jar` y ejecutar desde la raíz:

```powershell
javac -encoding UTF-8 -cp ".herramientas/JFLAP7.1.jar" -d .herramientas scripts/VerificarJFLAP.java
java "-Djava.awt.headless=true" -cp ".herramientas;.herramientas/JFLAP7.1.jar" VerificarJFLAP .
```

En Linux o macOS, reemplazar `;` por `:` en el classpath de `java`.

El verificador reabre los cuatro `.jff`, elimina reglas unitarias y convierte a forma normal de Chomsky **en memoria** con los convertidores de JFLAP, y ejecuta su CYK en 72 entradas. Los diez errores léxicos restantes se detectan antes del parser. También obtiene los tres árboles principales con `BruteParser`, sobre las producciones originales. El log completo está en [jflap_resultados.txt](evidencias/validaciones/jflap_resultados.txt).

Las imágenes en `evidencias/jflap/` se renderizan con componentes originales de JFLAP al reabrir los archivos; no son ventanas imitadas ni resultados escritos a mano. El árbol anotado del informe se dibuja desde el JSON de la misma derivación comprobada. El verificador Java regenera sus vistas sin abrir ventanas en el escritorio.

## Organización y regeneración

```text
informe/       PDF final y main.tex
gramaticas/    cuatro .jff y especificacion.json
evidencias/    árbol anotado, vistas JFLAP, derivaciones y resultados
ejemplos/      programa de referencia, programa extendido y corpus
scripts/       especificación común, reconocedores y regeneradores
docs/          comprobación de cobertura de la rúbrica
```

`scripts/gramatica.py` define las producciones y la codificación; no hay reglas diferentes escritas a mano en cada reconocedor. Si se cambia la gramática, hay que regenerar y revisar también el informe:

```bash
python scripts/preparar_evidencias.py
python scripts/validar_gramatica.py
python scripts/dibujar_arbol.py
```

El último comando requiere Pillow, solo para dibujar la figura. Después se ejecuta el verificador Java y se compila el PDF **dos veces** desde `informe/`:

```text
pdflatex -interaction=nonstopmode -halt-on-error -jobname=Lab_03_JefeGrupo_vicente_rivera main.tex
```

Para Overleaf, subir el repositorio completo y seleccionar `informe/main.tex` como documento principal. Los archivos generados se mantienen versionados para que las evidencias se puedan consultar sin instalar las herramientas.
