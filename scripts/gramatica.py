"""Especificación única de la GLC, análisis léxico y dos reconocedores.

Python 3.10+, biblioteca estándar. No ejecuta el programa ni asigna tipos.
La codificación de JFLAP preserva un token por carácter; conserva los lexemas
por separado para mostrar las derivaciones del informe sin inventar reglas.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

VARIABLES = {
    "S": "programa", "L": "lista_instrucciones", "I": "instruccion",
    "A": "asignacion", "C": "asignacion_simple", "R": "asignacion_aritmetica",
    "V": "operando", "F": "operador", "O": "salida", "D": "identificador",
    "N": "numero", "J": "declaracion", "T": "tipo",
}
TERMINALES = {
    "b": "Begin", "p": "Programa", "e": "End", "s": "salida",
    "i": "ID", "n": "NUM", "=": "=", "#": "#",
    "+": "+", "-": "-", "*": "*", "/": "/", "%": "%",
    "t": "entero", "r": "real",
}
BASE = {
    "S": ["bpDLe"],
    "L": ["IL", "I"],
    "I": ["A", "O"],
    "A": ["C", "R"],
    "C": ["D=V#"],
    "R": ["D=VFV#"],
    "V": ["D", "N"],
    "F": ["+", "-", "*", "/", "%"],
    "O": ["sD#"],
    "D": ["i"],
    "N": ["n"],
}
RESERVADAS = {"Begin": "b", "Programa": "p", "End": "e", "salida": "s"}
PATRON_ID = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
PATRON_NUM = re.compile(r"[0-9]+(?:\.[0-9]+)?")


def producciones(extendida=False):
    result = {left: tuple(rights) for left, rights in BASE.items()}
    if extendida:
        result["I"] += ("J",)
        result["J"] = ("TD#",)
        result["T"] = ("t", "r")
    return result


@dataclass(frozen=True)
class Token:
    codigo: str
    lexema: str
    linea: int
    columna: int


class ErrorLexico(ValueError):
    pass


def tokenizar(fuente: str, extendida=False) -> tuple[Token, ...]:
    """Máxima coincidencia, reservadas antes de ID y comentarios no anidados.

    No se eliminan espacios pegando palabras: se recorre la fuente por posición.
    Así `x y` sigue siendo dos ID y `xy` uno. Comentarios conservan posiciones.
    """
    reserved = dict(RESERVADAS)
    if extendida:
        reserved.update({"entero": "t", "real": "r"})
    result = []
    pos = 0
    line = col = 1

    def advance(text):
        nonlocal pos, line, col
        pos += len(text)
        if "\n" in text:
            line += text.count("\n")
            col = len(text.rsplit("\n", 1)[1]) + 1
        else:
            col += len(text)

    while pos < len(fuente):
        c = fuente[pos]
        if c.isspace():
            advance(c)
            continue
        if fuente.startswith("/*", pos):
            end = fuente.find("*/", pos + 2)
            if end < 0:
                raise ErrorLexico(f"Comentario sin cierre en {line}:{col}.")
            text = fuente[pos:end + 2]
            if "/*" in text[2:-2]:
                raise ErrorLexico(f"Comentario anidado no admitido en {line}:{col}.")
            advance(text)
            continue
        match = PATRON_ID.match(fuente, pos)
        if match:
            lexeme = match.group()
            result.append(Token(reserved.get(lexeme, "i"), lexeme, line, col))
            advance(lexeme)
            continue
        match = PATRON_NUM.match(fuente, pos)
        if match:
            lexeme = match.group()
            # Evita fragmentar silenciosamente 12abc, 1.2.3, 2_3 y 2e3.
            end = match.end()
            if end < len(fuente) and (fuente[end].isascii() and
                    (fuente[end].isalnum() or fuente[end] in "_.")):
                raise ErrorLexico(f"Número o identificador mal formado en {line}:{col}.")
            result.append(Token("n", lexeme, line, col))
            advance(lexeme)
            continue
        if c in "=#+-*/%":
            result.append(Token(c, c, line, col))
            advance(c)
            continue
        raise ErrorLexico(f"Carácter no admitido {c!r} en {line}:{col}.")
    return tuple(result)


@dataclass(frozen=True)
class Nodo:
    simbolo: str
    hijos: tuple["Nodo", ...] = ()
    token: Token | None = None

    def hojas(self):
        if self.token is not None:
            return (self.token,)
        return tuple(t for c in self.hijos for t in c.hojas())

    def to_dict(self):
        if self.token is not None:
            return {"simbolo": self.simbolo, "lexema": self.token.lexema}
        return {"simbolo": self.simbolo, "hijos": [c.to_dict() for c in self.hijos]}


def analizar(tokens, inicio="S", extendida=False):
    """Analizador descendente con memoización que conserva un árbol concreto.

    Esta GLC no tiene ciclos vacíos ni recursión izquierda. El retorno enumera
    prefijos para poder retroceder entre la asignación simple y la aritmética.
    """
    rules = producciones(extendida)
    tokens = tuple(tokens)

    @lru_cache(None)
    def parse(symbol, position):
        if symbol not in rules:
            if position < len(tokens) and tokens[position].codigo == symbol:
                return ((position + 1, Nodo(symbol, token=tokens[position])),)
            return ()
        answers = []
        for rhs in rules[symbol]:
            pending = [(position, ())]
            for child in rhs:
                pending = [(end, prefix + (node,)) for at, prefix in pending
                           for end, node in parse(child, at)]
            answers.extend((end, Nodo(symbol, children)) for end, children in pending)
        return tuple(answers)

    answers = [node for end, node in parse(inicio, 0) if end == len(tokens)]
    if len(answers) > 1:
        raise AssertionError("Se encontraron varios árboles para la entrada probada.")
    return answers[0] if answers else None


def earley(palabra: str, inicio="S", extendida=False):
    """Reconocedor independiente de la GLC, también válido para λ.

    Cada ítem es (izquierda, derecha, punto, posición_origen). No utiliza los
    árboles ni las decisiones del analizador descendente.
    """
    rules = producciones(extendida)
    chart = [set() for _ in range(len(palabra) + 1)]
    chart[0].add(("@", inicio, 0, 0))
    for at in range(len(chart)):
        pending = list(chart[at])
        seen = 0
        while seen < len(pending):
            lhs, rhs, dot, start = pending[seen]
            seen += 1

            def add(state):
                if state not in chart[at]:
                    chart[at].add(state)
                    pending.append(state)

            if dot == len(rhs):
                for pl, pr, pd, ps in tuple(chart[start]):
                    if pd < len(pr) and pr[pd] == lhs:
                        add((pl, pr, pd + 1, ps))
            elif rhs[dot] in rules:
                for production in rules[rhs[dot]]:
                    add((rhs[dot], production, 0, at))
            elif at < len(palabra) and palabra[at] == rhs[dot]:
                chart[at + 1].add((lhs, rhs, dot + 1, start))
    return ("@", inicio, 1, 0) in chart[-1]


def derivacion_izquierda(arbol, extendida=False):
    """Devuelve las formas sentenciales y verifica cada sustitución de la GLC."""
    rules = producciones(extendida)
    frontier = [arbol]
    result = [(tuple(frontier), None)]
    while any(node.token is None for node in frontier):
        position = next(i for i, n in enumerate(frontier) if n.token is None)
        node = frontier[position]
        rhs = "".join(c.simbolo for c in node.hijos)
        assert rhs in rules[node.simbolo], (node.simbolo, rhs)
        frontier[position:position + 1] = node.hijos
        result.append((tuple(frontier), (node.simbolo, rhs)))
    assert tuple(n.token for n in frontier) == arbol.hojas()
    return result


def representar(frontier, lexemas=False):
    parts = []
    for node in frontier:
        if node.token is None:
            parts.append(f"<{VARIABLES[node.simbolo]}>")
        elif lexemas:
            parts.append(node.token.lexema)
        else:
            parts.append(TERMINALES[node.simbolo])
    return " ".join(parts)
