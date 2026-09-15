"""
cli_menu.py - Interfaz por consola para el editor de PDF acumulativo.
"""

from pathlib import Path
from pdf_ops import PDFEditorSession


def select_pdf_file(session: PDFEditorSession) -> None:
    """Pide al usuario la ruta de un archivo PDF y lo carga en la sesión."""
    print("\n--- Cargar / Cambiar PDF ---")
    if session.has_unsaved_changes:
        confirm = input("¡Atención! Tienes cambios sin guardar en la sesión actual. ¿Deseas descartarlos y abrir uno nuevo? (s/n): ").strip().lower()
        if confirm != 's':
            return

    path_str = input("Introduce la ruta del archivo PDF (o 'c' para cancelar): ").strip()
    if path_str.lower() == 'c':
        return

    new_path = Path(path_str).resolve()
    if session.load_pdf(new_path):
        print(f"✓ Archivo cargado en memoria: {new_path.name} ({session.get_total_pages()} páginas)")
    else:
        print("x Error: La ruta introducida no es un archivo PDF válido.")


def run_extract_range(session: PDFEditorSession) -> None:
    """Extrae un rango de páginas sobre la sesión actual."""
    if not session.is_loaded():
        print("\nx Primero debes seleccionar un archivo PDF válido.")
        return

    try:
        total = session.get_total_pages()
        print(f"\n--- Extraer Rango de Páginas (Total páginas actuales: {total}) ---")

        start = int(input(f"Página inicial (1 - {total}): "))
        end = int(input(f"Página final ({start} - {total}): "))

        session.extract_page_range(start, end)
        print(f"\n✓ Rango aplicado en memoria. Páginas actuales: {session.get_total_pages()}")

    except ValueError as ve:
        print(f"x Error en los datos introducidos: {ve}")
    except Exception as e:
        print(f"x Error inesperado: {e}")


def run_modify_header(session: PDFEditorSession) -> None:
    """Modifica la cabecera en la sesión actual."""
    if not session.is_loaded():
        print("\nx Primero debes seleccionar un archivo PDF válido.")
        return

    print("\n--- Modificar Cabecera ---")
    print("1) Ocultar cabecera (dejar en blanco)")
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

    session.modify_headers_and_footers(
        header_mode=header_mode,
        header_even=header_even,
        header_odd=header_odd,
        header_italic=header_italic,
        footer_mode="keep"
    )
    print("\n✓ Cambios de cabecera aplicados en memoria.")


def run_modify_footer(session: PDFEditorSession) -> None:
    """Modifica el pie de página en la sesión actual."""
    if not session.is_loaded():
        print("\nx Primero debes seleccionar un archivo PDF válido.")
        return

    print("\n--- Modificar Pie de Página ---")
    print("1) Ocultar pie de página (dejar en blanco)")
    print("2) Añadir nueva numeración (pares a la izq., impares a la der.)")
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

    session.modify_headers_and_footers(
        header_mode="keep",
        footer_mode=footer_mode,
        start_number=start_num
    )
    print("\n✓ Cambios de pie de página aplicados en memoria.")


def run_save_pdf(session: PDFEditorSession) -> None:
    """Exporta el trabajo acumulado a un archivo en el disco duro."""
    if not session.is_loaded():
        print("\nx No hay ningún documento en memoria para guardar.")
        return

    default_out = f"{session.original_name}_editado.pdf"
    out_str = input(f"Nombre/ruta para guardar el archivo final [{default_out}]: ").strip()
    out_path = Path(out_str) if out_str else Path.cwd() / default_out

    try:
        session.save_to_disk(out_path)
        print(f"\n✓ Archivo guardado con éxito en: {out_path.name}")
    except Exception as e:
        print(f"x Error al guardar el archivo: {e}")

def run_insert_blank_pages(session: PDFEditorSession) -> None:
    """Submenú para insertar hojas en blanco en el PDF."""
    if not session.is_loaded():
        print("\nx Primero debes seleccionar un archivo PDF válido.")
        return

    total = session.get_total_pages()
    print(f"\n--- Insertar Páginas en Blanco (Total páginas actuales: {total}) ---")
    print("¿Dónde deseas insertar las hojas en blanco?")
    print("1) Al principio del documento")
    print("2) Al final del documento")
    print("3) Después de una página específica")
    print("0) Cancelar")

    opt = input("Selecciona una opción: ").strip()

    if opt == "1":
        pos_index = 0
    elif opt == "2":
        pos_index = total
    elif opt == "3":
        try:
            target_page = int(input(f"Insertar después de la página (1 - {total}): "))
            if target_page < 1 or target_page > total:
                print("x Número de página fuera de rango.")
                return
            pos_index = target_page
        except ValueError:
            print("x Entrada no válida.")
            return
    else:
        return

    # Cantidad de hojas (por defecto 1)
    count_str = input("¿Cuántas hojas en blanco deseas insertar? [1]: ").strip()
    count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 1

    try:
        session.insert_blank_pages(position_index=pos_index, count=count)
        print(f"\n✓ Se han insertado {count} página(s) en blanco. Total actual: {session.get_total_pages()} páginas.")
    except Exception as e:
        print(f"x Error al insertar páginas: {e}")