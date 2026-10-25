
import os
import math
from collections import Counter

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages


def pedir_numero(texto):
    while True:
        try:
            v = float(input(texto).replace(",", "."))
            if v <= 0:
                print("Introduce un valor mayor que cero.")
                continue
            return v
        except ValueError:
            print("Introduce un número válido.")


def medida_pared(texto):
    v = pedir_numero(texto)

    # Permite introducir 1.8 m o 180 cm.
    if v <= 10:
        v *= 100

    return v


def generar_piezas(ancho, alto, az_ancho, az_alto, junta):
    piezas = []
    paso_x = az_ancho + junta
    paso_y = az_alto + junta

    # Centrar el replanteo en la pared.
    inicio_x = (ancho - az_ancho) / 2
    inicio_y = (alto - az_alto) / 2

    columnas = math.ceil(ancho / paso_x) + 3
    filas = math.ceil(alto / paso_y) + 3
    tol = 1e-6

    for fila in range(-filas, filas + 1):
        y = inicio_y + fila * paso_y

        for columna in range(-columnas, columnas + 1):
            x = inicio_x + columna * paso_x

            # Coordenadas visibles dentro de la pared.
            x1 = max(0.0, x)
            y1 = max(0.0, y)
            x2 = min(ancho, x + az_ancho)
            y2 = min(alto, y + az_alto)

            w = x2 - x1
            h = y2 - y1

            if w <= tol or h <= tol:
                continue

            entera = (
                abs(w - az_ancho) < tol
                and abs(h - az_alto) < tol
            )

            piezas.append({
                "x": x1,
                "y": y1,
                "w": w,
                "h": h,
                "entera": entera,
                "fila": fila,
                "columna": columna
            })

    return piezas


def generar_pdf(ancho, alto, az_ancho, az_alto, junta):
    os.makedirs("planos", exist_ok=True)
    archivo = os.path.abspath("planos/plano_azulejos.pdf")

    piezas = generar_piezas(
        ancho, alto, az_ancho, az_alto, junta
    )

    enteras = sum(p["entera"] for p in piezas)
    cortadas = len(piezas) - enteras

    cortes = Counter(
        (round(p["w"], 1), round(p["h"], 1))
        for p in piezas if not p["entera"]
    )

    with PdfPages(archivo) as pdf:
        fig = plt.figure(figsize=(16.5, 11.7))

        # Pared a la izquierda; información a la derecha.
        ax = fig.add_axes([0.07, 0.12, 0.55, 0.76])
        info = fig.add_axes([0.68, 0.10, 0.29, 0.82])
        info.axis("off")

        # Dibujar cada azulejo y su recorte.
        for p in piezas:
            x, y = p["x"], p["y"]
            w, h = p["w"], p["h"]

            ax.add_patch(Rectangle(
                (x, y), w, h,
                facecolor="#F3F3F3",
                edgecolor="#222222",
                linewidth=0.7
            ))

            # Las medidas aparecen dentro de cada pieza.
            etiqueta = f'{w:.1f} x {h:.1f} cm'

            if w >= 7 and h >= 7:
                fs = 6 if w >= 15 and h >= 15 else 4
                ax.text(
                    x + w / 2, y + h / 2,
                    etiqueta,
                    ha="center", va="center",
                    fontsize=fs, clip_on=True
                )
            else:
                # Etiqueta exterior para cortes muy estrechos.
                ax.annotate(
                    etiqueta,
                    (x + w / 2, y + h / 2),
                    xytext=(3, 3),
                    textcoords="offset points",
                    fontsize=4,
                    clip_on=True
                )

        # Contorno real de la pared.
        ax.add_patch(Rectangle(
            (0, 0), ancho, alto,
            fill=False, edgecolor="black",
            linewidth=2
        ))

        # Cotas generales.
        margen_x = ancho * 0.08
        margen_y = alto * 0.08

        ax.set_xlim(-margen_x, ancho + margen_x)
        ax.set_ylim(-margen_y, alto + margen_y)
        ax.set_aspect("equal")
        ax.axis("off")

        ax.annotate(
            "", xy=(0, alto + margen_y * 0.45),
            xytext=(ancho, alto + margen_y * 0.45),
            arrowprops=dict(arrowstyle="<->")
        )
        ax.text(
            ancho / 2, alto + margen_y * 0.65,
            f"ANCHO: {ancho:.1f} cm",
            ha="center", fontsize=9
        )

        ax.annotate(
            "", xy=(-margen_x * 0.4, 0),
            xytext=(-margen_x * 0.4, alto),
            arrowprops=dict(arrowstyle="<->")
        )
        ax.text(
            -margen_x * 0.58, alto / 2,
            f"ALTO: {alto:.1f} cm",
            rotation=90, ha="center",
            va="center", fontsize=9
        )

        # Panel informativo.
        y = 0.97

        def linea(texto, size=9, negrita=False, salto=0.045):
            nonlocal y
            info.text(
                0, y, texto,
                transform=info.transAxes,
                fontsize=size,
                fontweight="bold" if negrita else "normal",
                va="top"
            )
            y -= salto

        linea("PLANO DE ALICATADO", 15, True, 0.085)
        linea("DATOS GENERALES", 10, True)
        linea(f"Pared: {ancho:.1f} x {alto:.1f} cm")
        linea(f"Azulejo: {az_ancho:.1f} x {az_alto:.1f} cm")
        linea(f"Junta: {junta * 10:.1f} mm")
        y -= 0.025

        linea("RESUMEN DE PIEZAS", 10, True)
        linea(f"Total: {len(piezas)}")
        linea(f"Enteras: {enteras}")
        linea(f"Cortadas: {cortadas}")
        y -= 0.025

        linea("LISTA DE CORTES", 10, True)

        if cortes:
            for (w, h), cantidad in sorted(cortes.items()):
                linea(f"{w:.1f} x {h:.1f} cm: {cantidad} ud.")
        else:
            linea("No hay cortes.")

        y -= 0.025
        linea("COLOCACION", 10, True)
        linea("El dibujo muestra la posición")
        linea("de cada pieza dentro de la pared.")
        linea("Verifica las medidas en obra")
        linea("antes de realizar los cortes.")

        fig.suptitle(
            "PLANO DE COLOCACIÓN DE AZULEJOS",
            fontsize=14, fontweight="bold"
        )

        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    print("\nPDF generado:", archivo)
    print("Piezas totales:", len(piezas))
    print("Piezas enteras:", enteras)
    print("Piezas cortadas:", cortadas)


def main():
    print("=" * 45)
    print("       CALCULADOR DE ALICATADO")
    print("=" * 45)
    print("Pared: introduce metros (1.8) o centímetros (180).")
    print("Azulejos: centímetros.")
    print("Junta: centímetros; 2 mm = 0.2 cm.\n")

    ancho = medida_pared("Ancho de la pared: ")
    alto = medida_pared("Alto de la pared: ")

    az_ancho = pedir_numero("Ancho del azulejo (cm): ")
    az_alto = pedir_numero("Alto del azulejo (cm): ")
    junta = pedir_numero("Junta (cm): ")

    generar_pdf(ancho, alto, az_ancho, az_alto, junta)


if __name__ == "__main__":
    main()
