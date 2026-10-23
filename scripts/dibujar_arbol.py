"""Dibuja el árbol anotado desde la evidencia JSON verificada, sin inventar nodos.

Solo para regenerar la figura: requiere Pillow. La validación no lo necesita.
"""
from pathlib import Path
import json
from html import escape
from PIL import Image, ImageDraw, ImageFont
from gramatica import VARIABLES, TERMINALES

ROOT = Path(__file__).resolve().parents[1]


def main():
    data = json.loads((ROOT / "evidencias/derivaciones/asignacion.json").read_text(encoding="utf-8"))
    tree = data["arbol"]
    leaves = []

    def collect(n):
        if "lexema" in n:
            leaves.append(n)
        for c in n.get("hijos", []):
            collect(c)

    collect(tree)
    assert [n["lexema"] for n in leaves] == ["z", "=", "x", "+", "y", "#"]
    W, H = 2100, 920
    image = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(image)
    candidates = [Path("C:/Windows/Fonts/consola.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")]
    font_path = next((p for p in candidates if p.exists()), None)
    if font_path is None:
        raise FileNotFoundError("Se requiere Consolas o DejaVu Sans Mono para regenerar la figura.")
    font = ImageFont.truetype(str(font_path), 43)
    small = ImageFont.truetype(str(font_path), 30)
    nodes, edges = [], []
    cursor = 0

    def visit(n, depth=0):
        nonlocal cursor
        children = n.get("hijos", [])
        child_nodes = [visit(c, depth + 1) for c in children]
        if not children:
            x = 145 + cursor * 360
            cursor += 1
            y = 90 + depth * 132
            code = n["simbolo"]
            label = f"ID[{n['lexema']}]" if code == "i" else n["lexema"]
        else:
            x = sum(c[0] for c in child_nodes) / len(child_nodes)
            y = 90 + depth * 132
            label = n["simbolo"]
        nodes.append((x, y, label, not children))
        for c in child_nodes:
            edges.append(((x, y), c))
        return x, y

    visit(tree)
    for (x1, y1), (x2, y2) in edges:
        draw.line((x1, y1 + 32, x2, y2 - 32), fill="#59636e", width=3)
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<rect width="100%" height="100%" fill="white"/>']
    for (x1, y1), (x2, y2) in edges:
        svg.append(f'<line x1="{x1}" y1="{y1+32}" x2="{x2}" y2="{y2-32}" stroke="#59636e" stroke-width="3"/>')
    for x, y, label, terminal in nodes:
        width = max(100, draw.textbbox((0, 0), label, font=font)[2] + 36)
        color = "#fff3c4" if terminal else "#daeaf5"
        draw.rounded_rectangle((x-width/2, y-32, x+width/2, y+32), radius=12, fill=color, outline="#305f94", width=2)
        draw.text((x, y), label, fill="#152d47", font=font, anchor="mm")
        svg.append(f'<rect x="{x-width/2}" y="{y-32}" width="{width}" height="64" rx="12" fill="{color}" stroke="#305f94" stroke-width="2"/>')
        svg.append(f'<text x="{x}" y="{y+14}" text-anchor="middle" font-family="monospace" font-size="43" fill="#152d47">{escape(label)}</text>')
    legend = "I: instruccion  |  A: asignacion  |  R: asignacion_aritmetica"
    legend2 = "D: identificador  |  V: operando  |  F: operador"
    for y, text in [(840, legend), (885, legend2)]:
        draw.text((W/2, y), text, font=small, anchor="mm", fill="#374151")
        svg.append(f'<text x="{W/2}" y="{y+10}" text-anchor="middle" font-family="monospace" font-size="30" fill="#374151">{text}</text>')
    svg.append("</svg>")
    image.save(ROOT / "evidencias/arbol_z_x_mas_y.png", dpi=(240, 240))
    (ROOT / "evidencias/arbol_z_x_mas_y.svg").write_text("\n".join(svg) + "\n", encoding="utf-8")
    print("Árbol anotado generado desde las producciones y hojas verificadas.")


if __name__ == "__main__":
    main()
