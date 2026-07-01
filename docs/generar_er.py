import os, matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

# Tables: (name, schema, columns)
# column = (name, type, is_pk, is_fk, is_nn)
SCHEMA = "exploracolombia"

tables = [
    ("destinos", [
        ("id",         "INTEGER",    True,  False, True),
        ("nombre",     "VARCHAR",    False, False, True),
        ("departamento","VARCHAR",   False, False, True),
        ("tipo",       "VARCHAR",    False, False, True),
        ("descripcion","TEXT",       False, False, False),
        ("imagen",     "VARCHAR",    False, False, False),
        ("imagenes",   "TEXT",       False, False, False),
    ]),
    ("paquetes", [
        ("id",          "INTEGER",   True,  False, True),
        ("nombre",      "VARCHAR",   False, False, True),
        ("duracion",    "VARCHAR",   False, False, False),
        ("precio",      "INTEGER",   False, False, True),
        ("cupo",        "INTEGER",   False, False, True),
        ("descripcion", "TEXT",      False, False, False),
        ("estado",      "VARCHAR",   False, False, False),
        ("imagen",      "VARCHAR",   False, False, False),
        ("precio_oferta","INTEGER",  False, False, False),
        ("en_oferta",   "INTEGER",   False, False, False),
    ]),
    ("paquete_destinos", [
        ("id",          "INTEGER",   True,  False, True),
        ("paquete_id",  "INTEGER",   False, True,  True),
        ("destino_id",  "INTEGER",   False, True,  True),
    ]),
    ("guias", [
        ("id",       "INTEGER",  True,  False, True),
        ("nombre",   "VARCHAR",  False, False, True),
        ("email",    "VARCHAR",  False, False, False),
        ("telefono", "VARCHAR",  False, False, False),
        ("estado",   "VARCHAR",  False, False, False),
    ]),
    ("guia_idiomas", [
        ("id",      "INTEGER",  True,  False, True),
        ("guia_id", "INTEGER",  False, True,  True),
        ("idioma",  "VARCHAR",  False, False, True),
    ]),
    ("reservas", [
        ("id",              "INTEGER",  True,  False, True),
        ("paquete_id",      "INTEGER",  False, True,  True),
        ("destino_id",      "INTEGER",  False, True,  False),
        ("guia_id",         "INTEGER",  False, True,  True),
        ("fecha_salida",    "VARCHAR",  False, False, True),
        ("estado",          "VARCHAR",  False, False, False),
        ("total",           "INTEGER",  False, False, True),
        ("pagado",          "INTEGER",  False, False, True),
        ("cliente_nombre",  "VARCHAR",  False, False, False),
        ("cliente_email",   "VARCHAR",  False, False, False),
        ("cliente_telefono","VARCHAR",  False, False, False),
    ]),
    ("usuarios", [
        ("id",                "INTEGER",  True,  False, True),
        ("username",          "VARCHAR",  False, False, True),
        ("email",             "VARCHAR",  False, False, True),
        ("password",          "VARCHAR",  False, False, True),
        ("nombre",            "VARCHAR",  False, False, False),
        ("role",              "VARCHAR",  False, False, True),
        ("verified",          "INTEGER",  False, False, True),
        ("verification_code", "VARCHAR",  False, False, False),
        ("verification_expiry","VARCHAR", False, False, False),
        ("reset_code",        "VARCHAR",  False, False, False),
        ("reset_expiry",      "VARCHAR",  False, False, False),
    ]),
    ("registros_pendientes", [
        ("id",                "INTEGER",  True,  False, True),
        ("username",          "VARCHAR",  False, False, True),
        ("email",             "VARCHAR",  False, False, True),
        ("password",          "VARCHAR",  False, False, True),
        ("nombre",            "VARCHAR",  False, False, False),
        ("role",              "VARCHAR",  False, False, True),
        ("verification_code", "VARCHAR",  False, False, False),
        ("verification_expiry","VARCHAR", False, False, False),
        ("created_at",        "VARCHAR",  False, False, False),
    ]),
    ("pagos", [
        ("id",         "INTEGER",   True,  False, True),
        ("reserva_id", "INTEGER",   False, True,  True),
        ("metodo",     "VARCHAR",   False, False, True),
        ("monto",      "INTEGER",   False, False, True),
        ("estado",     "VARCHAR",   False, False, False),
        ("referencia", "VARCHAR",   False, False, False),
        ("creada",     "TIMESTAMP", False, False, False),
    ]),
    ("notificaciones", [
        ("id",          "INTEGER",  True,  False, True),
        ("usuario_id",  "INTEGER",  False, True,  True),
        ("tipo",        "VARCHAR",  False, False, True),
        ("mensaje",     "TEXT",     False, False, True),
        ("relacion_id", "INTEGER",  False, False, False),
        ("leida",       "INTEGER",  False, False, True),
        ("creada",      "TIMESTAMP",False, False, True),
    ]),
]

relationships = [
    ("paquete_destinos", "paquete_id", "paquetes", "id"),
    ("paquete_destinos", "destino_id", "destinos", "id"),
    ("guia_idiomas", "guia_id", "guias", "id"),
    ("reservas", "paquete_id", "paquetes", "id"),
    ("reservas", "destino_id", "destinos", "id"),
    ("reservas", "guia_id", "guias", "id"),
    ("pagos", "reserva_id", "reservas", "id"),
    ("notificaciones", "usuario_id", "usuarios", "id"),
]

# Grid layout
NCOLS = 4
pos = [(0,0),(1,0),(2,0),(3,0),(0,1),(1,1),(2,1),(3,1),(0,2),(1,2)]

TW = 2.8
RH = 0.26
HH = 0.38
PAD = 0.06
XGAP = 0.7
YGAP = 1.2
ML = 0.5
MT = 0.5

def table_height(cols):
    return HH + len(cols) * RH + PAD * 2

heights = {}
positions = {}
rows_data = {}

for i, (name, cols) in enumerate(tables):
    cx, cy = pos[i]
    h = table_height(cols)
    x = ML + cx * (TW + XGAP)
    y = 9.5 - cy * 4.2
    heights[name] = h
    positions[name] = (x, y)
    rows_data[name] = cols

WW = ML + NCOLS * (TW + XGAP) + 0.3
WH = 0.5 + 3 * 4.2 + 0.5

fig, ax = plt.subplots(1, 1, figsize=(WW * 2, WH * 2))
ax.set_xlim(0, WW)
ax.set_ylim(0, WH)
ax.axis("off")
ax.set_facecolor("#e8ecf0")
fig.patch.set_facecolor("#e8ecf0")

# Title
ax.text(WW / 2, WH - 0.15, f"Modelo EER — {SCHEMA}",
        ha="center", va="center", fontsize=13, fontweight="bold", color="#2c3e50",
        fontfamily="sans-serif")

# Draw tables
for name, (x, y) in positions.items():
    cols = rows_data[name]
    h = heights[name]
    col_count = len(cols)

    # Shadow
    sh = FancyBboxPatch((x+0.03, y-h+0.03), TW, h,
                         boxstyle="round,pad=0.06", facecolor="#b0b8c4", edgecolor="none", zorder=0)
    ax.add_patch(sh)

    # Table body
    tb = FancyBboxPatch((x, y-h), TW, h,
                         boxstyle="round,pad=0.06", facecolor="#ffffff", edgecolor="#7f8c9b", linewidth=0.6, zorder=1)
    ax.add_patch(tb)

    # Header bar
    hdr = FancyBboxPatch((x, y-HH), TW, HH,
                          boxstyle="round,pad=0.06", facecolor="#4a5b6b", edgecolor="none", zorder=2)
    ax.add_patch(hdr)
    # Table icon (tiny square)
    hdr_sq = FancyBboxPatch((x+0.06, y-HH+0.08), 0.14, HH-0.16,
                             boxstyle="round,pad=0.02", facecolor="#84a4c8", edgecolor="none", zorder=3)
    ax.add_patch(hdr_sq)
    ax.text(x+TW/2, y-HH/2, name,
            ha="center", va="center", fontsize=7.5, fontweight="bold", color="#ffffff", zorder=3)

    # Column rows
    for j, (col_name, col_type, is_pk, is_fk, is_nn) in enumerate(cols):
        ry = y - HH - PAD - (j+1) * RH
        if j % 2 == 1:
            bg = FancyBboxPatch((x+0.04, ry), TW-0.08, RH,
                                 boxstyle="round,pad=0.02", facecolor="#f2f4f6", edgecolor="none", zorder=1)
            ax.add_patch(bg)

        pk_x = x + 0.04
        col_name_x = x + 0.24
        type_x = x + TW - 0.06

        # PK diamond (yellow key indicator)
        if is_pk:
            diamond = Polygon([
                (pk_x+0.04, ry+RH/2),
                (pk_x+0.08, ry+RH/2-0.06),
                (pk_x+0.12, ry+RH/2),
                (pk_x+0.08, ry+RH/2+0.06),
            ], closed=True, facecolor="#f1c40f", edgecolor="#d4a017", linewidth=0.4, zorder=3)
            ax.add_patch(diamond)

        # FK diamond (red diamond)
        if is_fk:
            diamond = Polygon([
                (pk_x+0.04, ry+RH/2),
                (pk_x+0.08, ry+RH/2-0.06),
                (pk_x+0.12, ry+RH/2),
                (pk_x+0.08, ry+RH/2+0.06),
            ], closed=True, facecolor="#e74c3c", edgecolor="#c0392b", linewidth=0.4, zorder=3)
            ax.add_patch(diamond)

        # Column name
        cname = col_name
        if is_nn:
            cname = f"{col_name} (NN)"
        ax.text(col_name_x, ry+RH/2-0.01, cname,
                ha="left", va="center", fontsize=5.5,
                fontweight="bold" if (is_pk or is_fk) else "normal",
                color="#1e293b", zorder=3)

        # Column type
        ax.text(type_x, ry+RH/2-0.01, col_type,
                ha="right", va="center", fontsize=5, color="#64748b", zorder=3)

# Draw relationships with crow's foot
for src, src_col, dst, dst_col in relationships:
    sx, sy = positions[src]
    dx, dy = positions[dst]

    # Find the row index for the FK column in src
    src_cols = rows_data[src]
    src_row = next(j for j, (n, *_) in enumerate(src_cols) if n == src_col)

    # Find the row index for the PK column in dst
    dst_cols = rows_data[dst]
    dst_row = next(j for j, (n, *_) in enumerate(dst_cols) if n == dst_col)

    # Calculate FK point (bottom of the FK column row)
    fx = sx + TW
    fy = sy - HH - PAD - (src_row + 1) * RH + RH/2

    # Calculate PK point (top of the PK column row)
    pkx = dx
    pky = dy - HH - PAD - (dst_row + 1) * RH + RH/2

    # Draw bezier curve from FK to PK
    mid_x = (fx + pkx) / 2
    ax.annotate("", xy=(pkx, pky), xytext=(fx, fy),
                arrowprops=dict(
                    arrowstyle="-|>", color="#5a6b7a", lw=0.5,
                    connectionstyle="arc3,rad=0.12"
                ))

    # Crow's foot at FK end (many side) - three short lines
    # Actually, for simplicity we draw a small marker
    # For a proper crow's foot, we'd need more complex drawing
    # Let's just use the arrow for now

# Legend
leg_y = 0.15
legend_items = [
    ("gold", "PK (Primary Key)"),
    ("red", "FK (Foreign Key)"),
    ("gray", "NN (Not Null)"),
]
for li, (color, text) in enumerate(legend_items):
    lx = 0.5 + li * 3.0
    if color == "gold":
        d = Polygon([(lx, leg_y+0.04), (lx+0.04, leg_y), (lx+0.08, leg_y+0.04), (lx+0.04, leg_y+0.08)],
                    closed=True, facecolor="#f1c40f", edgecolor="#d4a017", zorder=3)
        ax.add_patch(d)
    else:
        ax.plot(lx+0.04, leg_y+0.04, marker="o", color="#e74c3c" if color == "red" else "#94a3b8",
                markersize=4, linestyle="none")
    ax.text(lx+0.14, leg_y+0.04, text, fontsize=5.5, color="#334155", va="center")

out_dir = os.path.dirname(__file__)
for ext in ["jpg", "pdf"]:
    path = os.path.join(out_dir, f"modelo_relacional.{ext}")
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor(),
                format="pdf" if ext == "pdf" else "jpeg")
    print(f"Guardado: {path}")

plt.close()
