import math
from collections import Counter

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages
import streamlit as st


def generar_piezas(ancho, alto, az_ancho, az_alto, junta):
    piezas = []
    paso_x = az_ancho + junta
    paso_y = az_alto + junta

    inicio_x = (ancho - az_ancho) / 2
    inicio_y = (alto - az_alto) / 2

    columnas = math.ceil(ancho / paso_x) + 3
    filas = math.ceil(alto / paso_y) + 3
    tol = 1e-6

    for fila in range(-filas, filas + 1):
        y = inicio_y + fila * paso_y

        for columna in range(-columnas, columnas + 1):
            x = inicio_x + columna * paso_x

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


def generar_pdf_bytes(ancho, alto, az_ancho, az_alto, junta):
    piezas = generar_piezas(ancho, alto, az_ancho, az_alto, junta)

    enteras = sum(p["entera"] for p in piezas)
    cortadas = len(piezas) - enteras

    cortes = Counter(
        (round(p["w"], 1), round(p["h"], 1))
        for p in piezas if not p["entera"]
    )

    pdf_path = "plano_azulejos.pdf"
    with PdfPages(pdf_path) as pdf:
        fig = plt.figure(figsize=(16.5, 11.7))

        ax = fig.add_axes([0.07, 0.12, 0.55, 0.76])
        info = fig.add_axes([0.68, 0.10, 0.29, 0.82])
        info.axis("off")

        for p in piezas:
            x, y = p["x"], p["y"]
            w, h = p["w"], p["h"]

            ax.add_patch(Rectangle(
                (x, y), w, h,
                facecolor="#F3F3F3",
                edgecolor="#222222",
                linewidth=0.7
            ))

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
                ax.annotate(
                    etiqueta,
                    (x + w / 2, y + h / 2),
                    xytext=(3, 3),
                    textcoords="offset points",
                    fontsize=4,
                    clip_on=True
                )

        ax.add_patch(Rectangle(
            (0, 0), ancho, alto,
            fill=False, edgecolor="black",
            linewidth=2
        ))

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

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()
    return pdf_bytes, piezas, enteras, cortadas


def main():
    st.set_page_config(page_title="Calculador de Alicatado", layout="centered")
    
    st.title("🧱 Calculador y Plano de Alicatado")
    st.write("Introduce las medidas para generar el plano de colocación y el resumen de piezas.")

    st.sidebar.header("Parámetros de Medida")
    
    # Entradas en centímetros para mayor precisión web
    ancho_m = st.sidebar.number_input("Ancho de la pared (cm)", min_value=1.0, value=250.0, step=1.0)
    alto_m = st.sidebar.number_input("Alto de la pared (cm)", min_value=1.0, value=220.0, step=1.0)
    
    az_ancho = st.sidebar.number_input("Ancho del azulejo (cm)", min_value=1.0, value=30.0, step=0.5)
    az_alto = st.sidebar.number_input("Alto del azulejo (cm)", min_value=1.0, value=60.0, step=0.5)
    junta_mm = st.sidebar.number_input("Junta (mm)", min_value=0.0, value=2.0, step=0.5)
    junta = junta_mm / 10.0  # Pasar a cm

    if st.sidebar.button("Generar Plano", type="primary"):
        with st.spinner("Calculando y generando plano..."):
            pdf_bytes, piezas, enteras, cortadas = generar_pdf_bytes(ancho_m, alto_m, az_ancho, az_alto, junta)
            
            st.success("¡Plano generado con éxito!")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Piezas Totales", len(piezas))
            col2.metric("Enteras", enteras)
            col3.metric("Cortadas", cortadas)

            st.download_button(
                label="📥 Descargar Plano en PDF",
                data=pdf_bytes,
                file_name="plano_azulejos.pdf",
                mime="application/pdf"
            )


if __name__ == "__main__":
    main()