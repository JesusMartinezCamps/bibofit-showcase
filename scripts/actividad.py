#!/usr/bin/env python3
"""Calendario de commits de un repo, en dos SVG (claro y oscuro).

Uso: python3 scripts/actividad.py <ruta-al-repo> [rama=dev]
Escribe assets/actividad-claro.svg y assets/actividad-oscuro.svg.
Solo cuenta commits por día: ni mensajes ni autores salen del repo privado.
"""
import subprocess
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

CELL, GAP = 13, 3
STEP = CELL + GAP
LEFT, TOP, PAD = 28, 92, 20
MONTHS = "ene feb mar abr may jun jul ago sep oct nov dic".split()
BUCKETS = [(1, 9), (10, 24), (25, 49), (50, 99), (100, None)]
FONT = "-apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
# Rampa ordinal azul validada con dataviz/validate_palette.js --ordinal.
THEMES = {
    "claro": dict(bg="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#898781",
                  empty="#ebeae5",
                  ramp=["#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"]),
    "oscuro": dict(bg="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#898781",
                   empty="#2c2c2a",
                   ramp=["#184f95", "#2a78d6", "#5598e7", "#86b6ef", "#cde2fb"]),
}


def thousands(n):
    return f"{n:,}".replace(",", ".")


def day_label(d):
    return f"{d.day} {MONTHS[d.month - 1]}"


def bucket(n):
    for i, (lo, hi) in enumerate(BUCKETS):
        if n >= lo and (hi is None or n <= hi):
            return i
    return None


def svg(counts, first, last, t):
    start = first - timedelta(days=first.weekday())
    weeks = (last - start).days // 7 + 1
    width = PAD + LEFT + weeks * STEP + PAD
    height = TOP + 7 * STEP + 56
    total = sum(counts.values())
    span = (last - first).days + 1
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT}">',
        f'<title>{thousands(total)} commits entre el {day_label(first)} y el '
        f'{day_label(last)} de {last.year}</title>',
        f'<rect width="{width}" height="{height}" rx="10" fill="{t["bg"]}"/>',
        f'<text x="{PAD}" y="{PAD + 26}" font-size="28" font-weight="700" '
        f'fill="{t["ink"]}">{thousands(total)} commits</text>',
        f'<text x="{PAD}" y="{PAD + 50}" font-size="14" fill="{t["ink2"]}">'
        f'{day_label(first)} – {day_label(last)} {last.year} · '
        f'{len(counts)} de {span} días con commits</text>',
    ]
    x0, y0 = PAD + LEFT, TOP
    for row, name in ((0, "L"), (2, "X"), (4, "V")):
        out.append(f'<text x="{PAD}" y="{y0 + row * STEP + 10}" font-size="10" '
                   f'fill="{t["muted"]}">{name}</text>')
    month_labels = []  # (semana, mes); uno a menos de 3 semanas del siguiente se cae
    for w in range(weeks):
        monday = start + timedelta(weeks=w)
        month_start = next((monday + timedelta(days=i) for i in range(7)
                            if (monday + timedelta(days=i)).day == 1), None)
        if (w == 0 or month_start) and weeks - w > 2:
            if month_labels and w - month_labels[-1][0] < 3:
                month_labels.pop()
            month_labels.append((w, (month_start or first).month))
    for w, m in month_labels:
        out.append(f'<text x="{x0 + w * STEP}" y="{y0 - 8}" font-size="11" '
                   f'fill="{t["muted"]}">{MONTHS[m - 1]}</text>')
    for w in range(weeks):
        monday = start + timedelta(weeks=w)
        for dow in range(7):
            d = monday + timedelta(days=dow)
            if d < first or d > last:
                continue
            n = counts.get(d, 0)
            b = bucket(n)
            fill = t["empty"] if b is None else t["ramp"][b]
            out.append(f'<rect x="{x0 + w * STEP}" y="{y0 + dow * STEP}" width="{CELL}" '
                       f'height="{CELL}" rx="3" fill="{fill}"><title>{day_label(d)}: '
                       f'{n} commits</title></rect>')
    ly = y0 + 7 * STEP + 22
    labels = ["0"] + [f"{lo}–{hi}" if hi else f"{lo}+" for lo, hi in BUCKETS]
    fills = [t["empty"]] + t["ramp"]
    out.append(f'<text x="{PAD}" y="{ly + 10}" font-size="11" fill="{t["muted"]}">'
               f'Commits al día</text>')
    lx = PAD + 96
    for label, fill in zip(labels, fills):
        out.append(f'<rect x="{lx}" y="{ly}" width="{CELL}" height="{CELL}" rx="3" '
                   f'fill="{fill}"/>')
        out.append(f'<text x="{lx + CELL + 5}" y="{ly + 10}" font-size="11" '
                   f'fill="{t["ink2"]}">{label}</text>')
        lx += CELL + 5 + 7 * len(label) + 14
    out.append("</svg>")
    return "\n".join(out) + "\n"


def main():
    repo = sys.argv[1]
    branch = sys.argv[2] if len(sys.argv) > 2 else "dev"
    dates = subprocess.run(
        ["git", "-C", repo, "log", branch, "--no-merges", "--format=%ad",
         "--date=short"], check=True, capture_output=True, text=True).stdout.split()
    counts = Counter(date.fromisoformat(d) for d in dates)
    first, last = min(counts), max(counts)
    assets = Path(__file__).resolve().parent.parent / "assets"
    for name, theme in THEMES.items():
        (assets / f"actividad-{name}.svg").write_text(svg(counts, first, last, theme))
    by_month = Counter(f"{d:%Y-%m}" for d in counts.elements())
    print(f"{len(dates)} commits, {len(counts)} días, {first} → {last}")
    for m, n in sorted(by_month.items()):
        print(m, n)


if __name__ == "__main__":
    main()
