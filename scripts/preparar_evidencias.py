"""Genera la especificación, los cuatro .jff y los casos documentados.

No necesita JFLAP para generar XML. La apertura real se comprueba por separado
con VerificarJFLAP.java. Ejecutar desde cualquier carpeta con Python 3.10+.
"""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from gramatica import VARIABLES, TERMINALES, producciones

ROOT = Path(__file__).resolve().parents[1]


def guardar_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def crear_casos():
    cases = []

    def add(id_, source, expected, start="I", extended=False, group="adicional", reason=""):
        cases.append(dict(id=id_, grupo=group, fuente=source, inicio=start,
                          extendida=extended, esperado=expected, justificacion=reason))

    q4 = [
        ("x = 10 #", True, "Asignación simple con número y terminador."),
        ("z = x + y #", True, "Asignación con dos operandos y operador infijo."),
        ("salida z #", True, "Salida de un identificador seguida de #."),
        ("x 10 #", False, "Falta = entre el destino y el operando."),
        ("z = + x y #", False, "El operador debe ir entre los operandos, no antes del primero."),
        ("salida #", False, "Falta el identificador después de salida."),
        ("x = 20", False, "Falta # al final de la instrucción."),
        ("Begin\nPrograma prueba\nx = 5 #\nsalida x #\nEnd", True,
         "Programa con nombre, dos instrucciones y cierre End. Las barras de la pauta se interpretan como saltos de línea."),
    ]
    for n, (source, expected, reason) in enumerate(q4, 1):
        add(f"P4_{n}", source, expected, "S" if n == 8 else "I", group="pregunta_4", reason=reason)
    for n, source in enumerate(["x = 20 #", "z = x * y #", "salida temporal #"], 1):
        add(f"P3_{n}", source, True, group="pregunta_3",
            reason="La forma corresponde a una alternativa de <instruccion>.")
    add("REF", (ROOT / "ejemplos/programa_referencia.txt").read_text(encoding="utf-8"), True,
        "S", group="referencia", reason="20 instrucciones: 13 asignaciones y 7 salidas.")
    add("EXT_V", "entero contador #", True, extended=True, group="extension",
        reason="Tipo reservado, identificador y terminador.")
    add("EXT_I", "entero #", False, extended=True, group="extension",
        reason="Falta el identificador entre el tipo y #.")
    add("EXT_PROG", (ROOT / "ejemplos/programa_extendido.txt").read_text(encoding="utf-8"),
        True, "S", True, group="extension", reason="Programa completo con declaraciones y operaciones previas.")
    extras = [
        ("ID_LARGO", "operativo_01_02 = z2 #", True),
        ("ID_MAYUSCULA", "Variable_A2 = temporal #", True),
        ("ID_GUION_INICIAL", "_x = 1 #", False),
        ("ID_DIGITO_INICIAL", "2x = 1 #", False),
        ("RESERVADA_ID", "salida = 1 #", False),
        ("ID_PREFIJO_RESERVADO", "salida2 = 1 #", True),
        ("NUM_CERO", "x = 0 #", True),
        ("NUM_REAL", "x = 1.345 #", True),
        ("NUM_CEROS", "x = 00.50 #", True),
        ("NUM_NEGATIVO", "x = -1 #", False),
        ("NUM_PUNTO_FINAL", "x = 1. #", False),
        ("NUM_PUNTO_INICIAL", "x = .5 #", False),
        ("NUM_EXPONENTE", "x = 2e3 #", False),
        ("NUM_DOBLE_PUNTO", "x = 1.2.3 #", False),
        ("SALIDA_NUMERO", "salida 20 #", False),
        ("INSTRUCCION_VACIA", "", False),
        ("DOBLE_TERMINADOR", "x = 1 ##", False),
        ("ASIG_SIN_VALOR", "x = #", False),
        ("DOS_OPERADORES", "x = y + z * t #", False),
        ("SIN_OPERADOR", "x = y z #", False),
        ("COMENTARIO", "x /* comentario */ = 1 #", True),
        ("COMENTARIO_MULTILINEA", "x = 1 # /* a\nb */", True),
        ("COMENTARIO_SIN_CIERRE", "x = 1 # /* comentario", False),
        ("COMENTARIO_ANIDADO", "/* exterior /* interior */ */ x = 1 #", False),
        ("NO_PEGAR_ID", "x y = 1 #", False),
        ("DOS_ID_POR_COMENTARIO", "x/* c */y = 1 #", False),
        ("CARACTER_AJENO", "x = @ #", False),
        ("PARENTESIS", "x = ( y + z ) #", False),
    ]
    for id_, source, expected in extras:
        add(id_, source, expected)
    for op in "+-*/%":
        for l in ("x", "10"):
            for r in ("y", "2.5"):
                add(f"OP_{ord(op)}_{l}_{r}", f"z = {l} {op} {r} #", True,
                    group="operadores", reason="Cada operador admite ID o NUM a ambos lados.")
    programs = [
        ("PROG_MINIMO", "Begin Programa a x = 0 # End", True),
        ("PROG_SOLO_SALIDA", "Begin Programa a salida x # End", True),
        ("PROG_VACIO", "Begin Programa a End", False),
        ("PROG_SIN_NOMBRE", "Begin Programa x = 1 # End", False),
        ("PROG_SIN_END", "Begin Programa a x = 1 #", False),
        ("PROG_END_EXTRA", "Begin Programa a x = 1 # End End", False),
        ("PROG_MINUSCULA", "begin Programa a x = 1 # End", False),
        ("P4_8_BARRAS_LITERALES", "Begin / Programa prueba / x = 5 # / salida x # / End", False),
        ("INSTRUCCION_NO_PROGRAMA", "x = 10 #", False),
        ("PROGRAMA_NO_INSTRUCCION", "Begin Programa a x = 1 # End", False),
    ]
    for id_, source, expected in programs:
        add(id_, source, expected, "I" if id_ == "PROGRAMA_NO_INSTRUCCION" else "S", group="contexto")
    for id_, source, expected in [
        ("EXT_REAL", "real temperatura #", True),
        ("EXT_ID_TIPO", "entero real #", False),
        ("EXT_SIN_TERMINADOR", "entero contador", False),
        ("EXT_CON_INICIALIZACION", "entero contador = 0 #", False),
        ("EXT_TIPO_DISTINTO", "cadena texto #", False),
        ("EXT_CONSERVA_ASIG", "x = y + 1 #", True),
        ("EXT_CONSERVA_SALIDA", "salida x #", True),
        ("EXT_TIPO_EN_MAYUSCULA", "Entero contador #", False),
    ]:
        add(id_, source, expected, extended=True, group="extension_adicional")
    add("BASE_NO_DECLARA", "entero contador #", False, group="extension_adicional")
    return cases


def main():
    for name in ["gramaticas", "ejemplos", "evidencias/derivaciones", "evidencias/validaciones"]:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    guardar_json(ROOT / "gramaticas/especificacion.json", {
        "variables": VARIABLES, "terminales": TERMINALES,
        "producciones_base": producciones(),
        "producciones_extendida": producciones(True),
        "inicio_programa": "S", "inicio_instruccion": "I",
        "id": "[A-Za-z][A-Za-z0-9_]*", "numero": "[0-9]+(?:\\.[0-9]+)?",
    })
    for extended in [False, True]:
        for start, suffix in [("S", ""), ("I", "_instrucciones")]:
            structure = ET.Element("structure")
            ET.SubElement(structure, "type").text = "grammar"
            rules = producciones(extended)
            # El formato XML de JFLAP 7.1 no guarda un inicio alternativo.
            # Las copias para instrucciones usan el adaptador S -> I.
            if start == "I":
                rules["S"] = ("I",)
            for lhs in rules:
                for rhs in rules[lhs]:
                    production = ET.SubElement(structure, "production")
                    ET.SubElement(production, "left").text = lhs
                    ET.SubElement(production, "right").text = rhs
            ET.indent(structure)
            name = "gramatica_" + ("extendida" if extended else "base") + suffix + ".jff"
            ET.ElementTree(structure).write(ROOT / "gramaticas" / name, encoding="utf-8", xml_declaration=True)
    guardar_json(ROOT / "ejemplos/casos_validacion.json", crear_casos())
    print("Generados: especificación, cuatro gramáticas JFLAP y corpus de validación.")


if __name__ == "__main__":
    main()
