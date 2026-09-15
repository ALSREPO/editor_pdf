"""
main.py - Aplicación principal con soporte para cambios acumulativos.
"""

import sys
from pathlib import Path
from pdf_ops import PDFEditorSession
from cli_menu import (
    select_pdf_file,
    run_extract_range,
    run_modify_header,
    run_modify_footer,
    run_save_pdf,
)


def main():
    session = PDFEditorSession()

    # Cargar archivo inicial si se pasa como argumento de consola
    if len(sys.argv) > 1:
        arg_path = Path(sys.argv[1]).resolve()
        if session.load_pdf(arg_path):
            print(f"PDF cargado desde argumento: {arg_path.name} ({session.get_total_pages()} páginas)")
        else:
            print(f"Advertencia: '{sys.argv[1]}' no es un archivo PDF válido.")

    while True:
        if session.is_loaded():
            status = f"[{session.original_name}.pdf | {session.get_total_pages()} pág.]"
            if session.has_unsaved_changes:
                status += " *"  # Asterisco indica cambios pendientes de guardar
        else:
            status = "[Ninguno seleccionado]"

        print("\n==================================")
        print("        EDITOR MODULAR DE PDF     ")
        print("==================================")
        print(f"1) Cargar / Cambiar PDF {status}")
        print("2) Extraer / Recortar rango de páginas")
        print("3) Modificar o ocultar cabecera")
        print("4) Modificar, ocultar o renumerar pie de página")
        print("5) Guardar PDF final en disco")
        print("0) Salir")
        print("----------------------------------")

        option = input("Selecciona una opción: ").strip()

        if option == "1":
            select_pdf_file(session)
        elif option == "2":
            run_extract_range(session)
        elif option == "3":
            run_modify_header(session)
        elif option == "4":
            run_modify_footer(session)
        elif option == "5":
            run_save_pdf(session)
        elif option == "0":
            if session.has_unsaved_changes:
                confirm = input("¡Tienes cambios sin guardar! ¿Seguro que deseas salir? (s/n): ").strip().lower()
                if confirm != 's':
                    continue
            print("\n¡Hasta luego!")
            break
        else:
            print("x Opción no válida. Inténtalo de nuevo.")


if __name__ == "__main__":
    main()

# pdf_original\Libro_paginas_37-38.pdf