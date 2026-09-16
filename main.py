"""
main.py - Punto de entrada unificado para el Editor de PDF (GUI PySide6 / CLI Terminal).
"""

import sys
from pathlib import Path


def run_cli():
    """Ejecuta el menú de consola interactivo tradicional."""
    from pdf_ops import PDFEditorSession
    from cli_menu import (
        select_pdf_file, run_extract_range, run_delete_pages,
        run_insert_blank_pages, run_merge_pdfs, run_adjust_margins,
        run_insert_front_matter, run_modify_header, run_modify_footer,
        run_save_pdf, run_insert_index, run_insert_pdf_at, run_impose_booklet
    )

    session = PDFEditorSession()

    if len(sys.argv) > 2:
        arg_path = Path(sys.argv[2]).resolve()
        if session.load_pdf(arg_path):
            print(f"PDF cargado desde argumento: {arg_path.name} ({session.get_total_pages()} páginas)")

    while True:
        if session.is_loaded():
            status = f"[{session.original_name}.pdf | {session.get_total_pages()} pág.]"
            if session.has_unsaved_changes:
                status += " *"
        else:
            status = "[Ninguno seleccionado]"

        print("\n==================================")
        print("         EDITOR MODULAR DE PDF     ")
        print("==================================")
        print(f"1) Cargar / Cambiar PDF {status}")
        print("2) Extraer / Recortar rango de páginas")
        print("3) Eliminar páginas (listas o rangos)")
        print("4) Insertar hojas en blanco")
        print("5) Unir varios archivos PDF")
        print("6) Insertar otro PDF en una posición específica")
        print("7) Ajustar márgenes para encuadernación")
        print("8) Insertar páginas de portada iniciales")
        print("9) Insertar índice desde archivo TXT")
        print("10) Modificar o ocultar cabecera")
        print("11) Modificar, ocultar o renumerar pie de página")
        print("12) Preparar cuadernillos para impresión")
        print("13) Guardar PDF final en disco")
        print("0) Salir")
        print("----------------------------------")

        option = input("Selecciona una opción: ").strip()

        if option == "1":
            select_pdf_file(session)
        elif option == "2":
            run_extract_range(session)
        elif option == "3":
            run_delete_pages(session)
        elif option == "4":
            run_insert_blank_pages(session)
        elif option == "5":
            run_merge_pdfs(session)
        elif option == "6":
            run_insert_pdf_at(session)
        elif option == "7":
            run_adjust_margins(session)
        elif option == "8":
            run_insert_front_matter(session)
        elif option == "9":
            run_insert_index(session)
        elif option == "10":
            run_modify_header(session)
        elif option == "11":
            run_modify_footer(session)
        elif option == "12":
            run_impose_booklet(session)
        elif option == "13":
            run_save_pdf(session)
        elif option == "0":
            if session.has_unsaved_changes:
                confirm = input("¡Tienes cambios sin guardar! ¿Seguro que deseas salir? (s/n): ").strip().lower()
                if confirm != 's':
                    continue
            print("\n¡Hasta luego!")
            break


def run_gui():
    """Arranca la interfaz gráfica PySide6."""
    from PySide6.QtWidgets import QApplication
    from gui.main_window import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Si se pasa la ruta de un PDF como argumento adicional al arrancar la GUI: python main.py ruta.pdf
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        pdf_arg = Path(sys.argv[1]).resolve()
        if pdf_arg.exists() and pdf_arg.suffix.lower() == ".pdf":
            window.session.load_pdf(pdf_arg)
            window.refresh_ui()

    sys.exit(app.exec())


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()