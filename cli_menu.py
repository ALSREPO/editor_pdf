"""
cli_menu.py - Interfaz por consola para el editor de PDF.
"""

from pathlib import Path
from pypdf import PdfReader
from pdf_ops import extract_page_range, modify_headers_and_footers


def select_pdf_file(current_pdf: Path | None) -> Path | None:
    """Pide al usuario la ruta de un archivo PDF y valida su existencia."""
    print("\n--- Seleccionar PDF ---")
    if current_pdf:
        print(f"PDF actual: {current_pdf.name}")
    
    path_str = input("Introduce la ruta del archivo PDF (o 'c' para cancelar): ").strip()
    if path_str.lower() == 'c':
        return current_pdf

    new_path = Path(path_str).resolve()
    if new_path.is_file() and new_path.suffix.lower() == ".pdf":
        print(f"✓ Archivo cargado: {new_path.name}")
        return new_path
    else:
        print("x Error: La ruta introducida no es un archivo PDF válido.")
        return current_pdf


def run_extract_range(current_pdf: Path | None) -> None:
    """Solicita los datos necesarios y llama a la función de extracción de páginas."""
    if not current_pdf or not current_pdf.exists():
        print("\nx Primero debes seleccionar un archivo PDF válido.")
        return

    try:
        reader = PdfReader(current_pdf)
        total = len(reader.pages)
        print(f"\n--- Extraer Rango de Páginas (Total páginas: {total}) ---")

        start = int(input(f"Página inicial (1 - {total}): "))
        end = int(input(f"Página final ({start} - {total}): "))

        default_out = current_pdf.stem + f"_paginas_{start}-{end}.pdf"
        out_str = input(f"Nombre/ruta del archivo de salida [{default_out}]: ").strip()
        out_path = Path(out_str) if out_str else current_pdf.parent / default_out

        extract_page_range(current_pdf, out_path, start, end)
        print(f"\n✓ Páginas {start} a {end} extraídas con éxito en: {out_path.name}")

    except ValueError as ve:
        print(f"x Error en los datos introducidos: {ve}")
    except Exception as e:
        print(f"x Error inesperado durante la extracción: {e}")

def run_modify_header(current_pdf: Path | None) -> None:
    """Submenú independiente para modificar o tapar la cabecera."""
    if not current_pdf or not current_pdf.exists():
        print("\nx Primero debes seleccionar un archivo PDF válido.")
        return

    print("\n--- Modificar Cabecera ---")
    print("1) Simplemente ocultar cabecera (dejar en blanco)")
    print("2) Personalizar cabecera (texto distinto en páginas pares/impares)")
    print("0) Cancelar")
    opt = input("Selecciona una opción: ").strip()

    header_italic = False
    if opt == "1":
        header_mode = "hide"
        header_even, header_odd = "", ""
    elif opt == "2":
        header_mode = "custom"
        header_even = input("Texto para la cabecera de páginas PARES: ").strip()
        header_odd = input("Texto para la cabecera de páginas IMPARES: ").strip()
        
        italic_opt = input("¿Deseas que el texto esté en cursiva? (s/n) [n]: ").strip().lower()
        header_italic = italic_opt == 's'
    else:
        return

    default_out = current_pdf.stem + "_cabecera_mod.pdf"
    out_str = input(f"Nombre del archivo de salida [{default_out}]: ").strip()
    out_path = Path(out_str) if out_str else current_pdf.parent / default_out

    modify_headers_and_footers(
        current_pdf, out_path,
        header_mode=header_mode,
        header_even=header_even,
        header_odd=header_odd,
        header_italic=header_italic,
        footer_mode="keep"
    )
    print(f"\n✓ Cabecera modificada correctamente en: {out_path.name}")


def run_modify_footer(current_pdf: Path | None) -> None:
    """Submenú independiente para modificar, tapar o renumerar el pie de página."""
    if not current_pdf or not current_pdf.exists():
        print("\nx Primero debes seleccionar un archivo PDF válido.")
        return

    print("\n--- Modificar Pie de Página ---")
    print("1) Simplemente ocultar pie de página (dejar en blanco / borrar número viejo)")
    print("2) Añadir nueva numeración de páginas")
    print("0) Cancelar")
    opt = input("Selecciona una opción: ").strip()

    start_num = 1
    if opt == "1":
        footer_mode = "hide"
    elif opt == "2":
        footer_mode = "number"
        start_input = input("¿Desde qué número empezar a contar? [1]: ").strip()
        start_num = int(start_input) if start_input.isdigit() else 1
    else:
        return

    default_out = current_pdf.stem + "_pie_mod.pdf"
    out_str = input(f"Nombre del archivo de salida [{default_out}]: ").strip()
    out_path = Path(out_str) if out_str else current_pdf.parent / default_out

    modify_headers_and_footers(
        current_pdf, out_path,
        header_mode="keep",
        footer_mode=footer_mode,
        start_number=start_num
    )
    print(f"\n✓ Pie de página modificado correctamente en: {out_path.name}")