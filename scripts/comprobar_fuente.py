"""Comprueba una fuente propia con la misma gramática del informe."""
from pathlib import Path
import argparse
from gramatica import ErrorLexico, analizar, tokenizar, derivacion_izquierda, representar


def main():
    p = argparse.ArgumentParser(description=__doc__)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--archivo", type=Path)
    source.add_argument("--texto")
    p.add_argument("--inicio", choices=["programa", "instruccion"], default="programa")
    p.add_argument("--extendida", action="store_true")
    p.add_argument("--derivar", action="store_true")
    args = p.parse_args()
    text = args.archivo.read_text(encoding="utf-8") if args.archivo else args.texto
    try:
        tokens = tokenizar(text, args.extendida)
    except ErrorLexico as exc:
        print(f"RECHAZADA: error léxico. {exc}")
        return 1
    print("Entrada JFLAP:", "".join(t.codigo for t in tokens) or "(vacía)")
    tree = analizar(tokens, "S" if args.inicio == "programa" else "I", args.extendida)
    if tree is None:
        print(f"RECHAZADA: no se deriva como {args.inicio} con esta gramática.")
        return 1
    print("ACEPTADA: se consumieron todos los tokens.")
    if args.derivar:
        for frontier, _ in derivacion_izquierda(tree, args.extendida):
            print(representar(frontier, lexemas=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
