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
    """Exporta el trabajo acumulado respetando directorios y sobreescribiendo en la ruta original si se desea."""
    if not session.is_loaded() or not session.original_path:
        print("\nx No hay ningún documento en memoria para guardar.")
        return

    print("\n--- Guardar PDF ---")
    print(f"Ruta actual del archivo cargado: {session.original_path}")
    out_str = input("Nombre/ruta para el archivo (deja en blanco para sobrescribir el archivo original): ").strip()

    try:
        if not out_str:
            # Sobrescribir exactamente el archivo en su carpeta de origen
            out_path = session.original_path
            session.save_to_disk(out_path, overwrite=True)
            print(f"\n✓ Archivo sobrescrito con éxito en su ubicación original:")
            print(f"  -> {out_path}")
            print("✓ El archivo sobrescrito es ahora el documento activo en la sesión.")
        else:
            # Si el usuario introduce solo un nombre o una ruta nueva
            target_path = Path(out_str)
            if target_path.suffix.lower() != ".pdf":
                target_path = target_path.with_suffix(".pdf")

            # Si introdujo una ruta relativa simple (sin carpeta), la guardamos en la misma carpeta que el original
            if not target_path.is_absolute() and len(target_path.parts) == 1:
                out_path = session.original_path.parent / target_path
            else:
                out_path = target_path.resolve()

            session.save_to_disk(out_path, overwrite=False)
            print(f"\n✓ Nuevo archivo guardado con éxito en:")
            print(f"  -> {out_path}")
            print(f"✓ Se mantiene cargado en la sesión el documento base: '{session.original_path.name}'")

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

def run_merge_pdfs(session: PDFEditorSession) -> None:
    """Submenú para unir varios archivos PDF en uno solo."""
    print("\n--- Unir Varios PDFs ---")
    if session.has_unsaved_changes:
        confirm = input("¡Atención! Tienes cambios sin guardar en la sesión actual. ¿Deseas reemplazar el documento cargado? (s/n): ").strip().lower()
        if confirm != 's':
            return

    print("1) Pasar una lista de archivos PDF (separados por comas)")
    print("2) Seleccionar un directorio (unirá todos los PDF en orden alfabético)")
    print("0) Cancelar")

    opt = input("Selecciona una opción: ").strip()
    pdf_list: list[Path] = []

    if opt == "1":
        raw_input = input("Introduce las rutas de los archivos PDF separadas por comas:\n> ").strip()
        if not raw_input:
            return
        
        paths = [p.strip() for p in raw_input.split(",") if p.strip()]
        pdf_list = [Path(p).resolve() for p in paths]

    elif opt == "2":
        dir_str = input("Introduce la ruta del directorio: ").strip()
        dir_path = Path(dir_str).resolve()

        if not dir_path.is_dir():
            print("x Error: La ruta introducida no es un directorio válido.")
            return

        # Buscar todos los archivos .pdf y ordenarlos alfabéticamente
        pdf_list = sorted([f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"])

        if not pdf_list:
            print(f"x No se encontraron archivos PDF en el directorio: {dir_path.name}")
            return

        print(f"✓ Se han encontrado {len(pdf_list)} archivos PDF en el directorio.")

    else:
        return

    try:
        session.merge_pdfs(pdf_list)
        print(f"\n✓ Se han unido {len(pdf_list)} archivos correctamente.")
        print(f"  Total páginas en la nueva sesión: {session.get_total_pages()}")
    except Exception as e:
        print(f"x Error durante la unión de archivos: {e}")