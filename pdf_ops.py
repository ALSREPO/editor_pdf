"""
pdf_ops.py - Módulo para la manipulación de archivos PDF.
"""

import io
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import white
from reportlab.pdfgen import canvas


def modify_headers_and_footers(
    input_pdf: str | Path,
    output_pdf: str | Path,
    header_mode: str = "keep",      # Options: 'keep', 'hide', 'custom'
    header_even: str = "",
    header_odd: str = "",
    header_italic: bool = False,    # Nueva opción para cursiva
    footer_mode: str = "keep",      # Options: 'keep', 'hide', 'number'
    start_number: int = 1
) -> bool:
    """
    Modifica de forma independiente la cabecera y/o el pie de página de un PDF.
    - header_mode: 
        'keep' -> No modifica la cabecera.
        'hide' -> Tapa la cabecera con una franja blanca.
        'custom' -> Tapa la cabecera y escribe textos distintos para páginas pares e impares.
    - footer_mode:
        'keep' -> No modifica el pie de página.
        'hide' -> Tapa el pie de página con una franja blanca.
        'number' -> Tapa el pie de página y añade nueva numeración.
    """
    input_path = Path(input_pdf)
    output_path = Path(output_pdf)

    if not input_path.exists():
        raise FileNotFoundError(f"El archivo '{input_path}' no existe.")

    reader = PdfReader(input_path)
    writer = PdfWriter()

    for idx, page in enumerate(reader.pages):
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        page_num = idx + 1  # Página actual (1-based)

        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))

        # --- GESTIÓN DE LA CABECERA ---
        if header_mode in ("hide", "custom"):
            tamano_cabecera = 50
            c.setFillColor(white)
            c.setStrokeColor(white)
            c.rect(0, page_height - tamano_cabecera, page_width, tamano_cabecera, fill=True, stroke=False)

            if header_mode == "custom":
                c.setFillColorRGB(0, 0, 0)
                # Seleccionar fuente en cursiva (Oblique) o normal
                font_name = "Helvetica-Oblique" if header_italic else "Helvetica"
                c.setFont(font_name, 9)

                text = header_even if page_num % 2 == 0 else header_odd
                if text:
                    c.drawCentredString(page_width / 2.0, page_height - 45, text)

        # --- GESTIÓN DEL PIE DE PÁGINA ---
        if footer_mode in ("hide", "number"):
            tamano_pie = 55
            c.setFillColor(white)
            c.setStrokeColor(white)
            c.rect(0, 0, page_width, tamano_pie, fill=True, stroke=False)

            if footer_mode == "number":
                c.setFillColorRGB(0, 0, 0)
                c.setFont("Helvetica", 9)

                current_page_label = start_number + idx
                label_text = f"- {current_page_label} -"
                margin = 40  # Margen lateral en puntos (pt) desde el borde de la página

                if page_num % 2 == 0:
                    # Página PAR: Esquina izquierda
                    c.drawString(margin + 20, 40, label_text)
                else:
                    # Página IMPAR: Esquina derecha
                    c.drawRightString(page_width - margin, 40, label_text)

        # Aplicar la capa con las modificaciones si aplica
        if header_mode != "keep" or footer_mode != "keep":
            c.save()
            packet.seek(0)
            overlay_pdf = PdfReader(packet)
            page.merge_page(overlay_pdf.pages[0])

        writer.add_page(page)

    with open(output_path, "wb") as f_out:
        writer.write(f_out)

    return True


def extract_page_range(input_pdf: str | Path, output_pdf: str | Path, start_page: int, end_page: int) -> bool:
    """
    Extrae un rango de páginas (incluyente, basado en índice 1) de un PDF a otro.
    """
    input_path = Path(input_pdf)
    output_path = Path(output_pdf)

    if not input_path.exists():
        raise FileNotFoundError(f"El archivo '{input_path}' no existe.")

    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    # Validar rangos (convertimos de 1-based a 0-based)
    if start_page < 1 or end_page > total_pages or start_page > end_page:
        raise ValueError(f"Rango inválido. El PDF tiene {total_pages} página(s).")

    writer = PdfWriter()

    # pypdf usa índices 0-based; el rango en Python es excluyente en el límite superior
    for i in range(start_page - 1, end_page):
        writer.add_page(reader.pages[i])

    with open(output_path, "wb") as f_out:
        writer.write(f_out)

    return True