"""Comprueba corpus, JFF, árboles y derivaciones; escribe evidencias auditables.

Uso: python scripts/validar_gramatica.py [--comprobar]
--comprobar compara las evidencias guardadas sin modificarlas (apto para CI).
"""
from pathlib import Path
from collections import Counter
import csv
import io
import json
import sys
import xml.etree.ElementTree as ET
from gramatica import (TERMINALES, VARIABLES, ErrorLexico, tokenizar, analizar,
                       earley, producciones, derivacion_izquierda, representar)

ROOT = Path(__file__).resolve().parents[1]


def verificar_jff():
    for extended in (False, True):
        for start, suffix in [("S", ""), ("I", "_instrucciones")]:
            name = "gramatica_" + ("extendida" if extended else "base") + suffix + ".jff"
            doc = ET.parse(ROOT / "gramaticas" / name).getroot()
            assert doc.findtext("type") == "grammar"
            actual = [(p.findtext("left"), p.findtext("right") or "") for p in doc.findall("production")]
            assert actual[0][0] == "S"
            expected_rules = producciones(extended)
            if start == "I":
                expected_rules["S"] = ("I",)
            expected = [(left, right) for left, rights in expected_rules.items() for right in rights]
            assert Counter(actual) == Counter(expected), name
    spec = json.loads((ROOT / "gramaticas/especificacion.json").read_text(encoding="utf-8"))
    assert spec["producciones_base"] == {k: list(v) for k, v in producciones().items()}
    assert spec["producciones_extendida"] == {k: list(v) for k, v in producciones(True).items()}


def verificar_arbol(node, extended):
    if node.token is not None:
        assert not node.hijos
        assert node.simbolo == node.token.codigo
        return
    assert "".join(c.simbolo for c in node.hijos) in producciones(extended)[node.simbolo]
    for child in node.hijos:
        verificar_arbol(child, extended)


def main():
    check = "--comprobar" in sys.argv
    verificar_jff()
    cases = json.loads((ROOT / "ejemplos/casos_validacion.json").read_text(encoding="utf-8"))
    results = []
    products = {}
    by_id = {}
    for case in cases:
        error = ""
        tree = None
        tokens = ()
        try:
            tokens = tokenizar(case["fuente"], case["extendida"])
            code = "".join(t.codigo for t in tokens)
            tree = analizar(tokens, case["inicio"], case["extendida"])
            accepted = tree is not None
            assert accepted == earley(code, case["inicio"], case["extendida"]), case["id"]
            if tree:
                verificar_arbol(tree, case["extendida"])
                assert tree.hojas() == tokens
                derivacion_izquierda(tree, case["extendida"])
            else:
                error = "sintáctico"
        except ErrorLexico as exc:
            accepted = False
            code = ""
            error = str(exc)
        assert accepted == case["esperado"], (case["id"], case["fuente"], error)
        result = {**case, "codigo_jflap": code, "aceptada": accepted,
                  "tipo_error": error, "tokens": len(tokens)}
        results.append(result)
        by_id[case["id"]] = (case, tokens, tree)
    # Regresión de las reglas léxicas y posiciones de fuente reales.
    ts = tokenizar("/* a\nb */\nx = 1 #")
    assert (ts[0].linea, ts[0].columna) == (3, 1)
    assert [t.codigo for t in tokenizar("salida salida2")] == ["s", "i"]
    assert [t.codigo for t in tokenizar("entero real")] == ["i", "i"]
    assert [t.codigo for t in tokenizar("entero real", True)] == ["t", "r"]
    assert len(tokenizar("x/* c */y")) == 2
    # El contador se obtiene del árbol, no de líneas ni de expresiones regulares.
    ref_tree = by_id["REF"][2]

    def count(node):
        c = Counter({node.simbolo: 1})
        for child in node.hijos:
            c.update(count(child))
        return c

    counts = count(ref_tree)
    assert counts["I"] == 20 and counts["A"] == 13 and counts["O"] == 7
    assert counts["C"] == 6 and counts["R"] == 7
    for name, case_id, ext in [("asignacion", "P4_2", False), ("salida", "P4_3", False),
                               ("declaracion", "EXT_V", True)]:
        case, tokens, tree = by_id[case_id]
        steps = derivacion_izquierda(tree, ext)
        data = {
            "fuente": case["fuente"], "inicio": "I", "extendida": ext,
            "codigo_jflap": "".join(t.codigo for t in tokens),
            "arbol": tree.to_dict(),
            "pasos": [{"forma_codificada": "".join(n.simbolo for n in frontier),
                       "forma_tokens": representar(frontier),
                       "forma_lexemas": representar(frontier, True),
                       "produccion": list(rule) if rule else None}
                      for frontier, rule in steps],
        }
        products[f"evidencias/derivaciones/{name}.json"] = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        # Fragmento LaTeX generado de los mismos pasos que se comprueban.
        def esc(text):
            for old, new in [("\\", "\\textbackslash{}"), ("_", "\\_"), ("#", "\\#"), ("%", "\\%")]:
                text = text.replace(old, new)
            return text

        rows = []
        for idx, step in enumerate(data["pasos"]):
            rule = step["produccion"]
            label = "Inicio" if rule is None else f"{rule[0]} $\\to$ \\texttt{{{esc(rule[1])}}}"
            rows.append(f"{idx} & {label} & \\texttt{{{esc(step['forma_codificada'])}}} \\\\")
        table = [r"\begin{tabular}{|c|l|l|}\hline",
                 r"\rowcolor{cabecera}\textbf{Paso}&\textbf{Producción aplicada}&\textbf{Forma sentencial}\\\hline"]
        products[f"evidencias/derivaciones/{name}_pasos.tex"] = "\n".join(table + rows + [r"\hline\end{tabular}"]) + "\n"
    products["evidencias/validaciones/resultados.json"] = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    buf = io.StringIO(newline="")
    fields = ["id", "grupo", "inicio", "extendida", "fuente", "codigo_jflap", "esperado", "aceptada", "tipo_error", "tokens"]
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(results)
    products["evidencias/validaciones/resultados.csv"] = buf.getvalue()
    # TSV mínimo para la comprobación con el simulador original de JFLAP.
    tsv = ["id\tinicio\textendida\tcodigo\tesperado"]
    for r in results:
        if not r["tipo_error"] or r["tipo_error"] == "sintáctico":
            tsv.append(f"{r['id']}\t{r['inicio']}\t{int(r['extendida'])}\t{r['codigo_jflap']}\t{int(r['esperado'])}")
    products["evidencias/validaciones/entradas_jflap.tsv"] = "\n".join(tsv) + "\n"
    summary = {"casos": len(results), "aceptadas": sum(r["aceptada"] for r in results),
               "rechazadas": sum(not r["aceptada"] for r in results),
               "errores_lexicos": sum(bool(r["tipo_error"] and r["tipo_error"] != "sintáctico") for r in results),
               "casos_sintacticos_jflap": len(tsv) - 1,
               "programa_referencia": {"instrucciones": counts["I"], "asignaciones": counts["A"],
                                       "simples": counts["C"], "aritmeticas": counts["R"], "salidas": counts["O"]},
               "gramatica_base": {"variables": len(producciones()), "producciones": sum(map(len, producciones().values()))},
               "gramatica_extendida": {"variables": len(producciones(True)), "producciones": sum(map(len, producciones(True).values()))}}
    products["evidencias/validaciones/resumen.json"] = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    for relative, content in products.items():
        path = ROOT / relative
        if check:
            assert path.read_text(encoding="utf-8") == content, f"Evidencia desactualizada: {relative}"
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("OK: corpus, dos reconocedores, cuatro JFF, árboles, hojas y pasos por la izquierda coherentes.")


if __name__ == "__main__":
    main()
