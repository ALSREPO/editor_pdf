"""
main.py - Aplicación principal del editor modular de PDF.
"""

import sys
from pathlib import Path
from cli_menu import (
    select_pdf_file,
    run_extract_range,
    run_modify_header,
    run_modify_footer,
)


def main():
    selected_pdf: Path | None = None

    if len(sys.argv) > 1:
        arg_path = Path(sys.argv[1]).resolve()
        if arg_path.is_file() and arg_path.suffix.lower() == ".pdf":
            selected_pdf = arg_path
            print(f"PDF cargado desde argumento: {selected_pdf.name}")
        else:
            print(f"Advertencia: '{sys.argv[1]}' no es un archivo PDF válido.")

    while True:
        pdf_status = f"[{selected_pdf.name}]" if selected_pdf else "[Ninguno seleccionado]"

        print("\n==================================")
        print("        EDITOR MODULAR DE PDF     ")
        print("==================================")
        print(f"1) Seleccionar/Cambiar PDF {pdf_status}")
        print("2) Extraer un rango de páginas")
        print("3) Modificar o ocultar cabecera")
        print("4) Modificar, ocultar o renumerar pie de página")
        print("0) Salir")
        print("----------------------------------")

        option = input("Selecciona una opción: ").strip()

        if option == "1":
            selected_pdf = select_pdf_file(selected_pdf)
        elif option == "2":
            run_extract_range(selected_pdf)
        elif option == "3":
            run_modify_header(selected_pdf)
        elif option == "4":
            run_modify_footer(selected_pdf)
        elif option == "0":
            print("\n¡Hasta luego!")
            break
        else:
            print("x Opción no válida. Inténtalo de nuevo.")


if __name__ == "__main__":
    main()

# pdf_original\Libro_paginas_37-38.pdf