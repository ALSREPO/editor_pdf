"""
cli_menu.py - Interfaz por consola para el editor de PDF acumulativo.
"""

from pathlib import Path
from pdf_ops import PDFEditorSession
from math import ceil


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

def parse_page_selection(input_str: str, max_pages: int) -> set[int]:
    """
    Parsea cadenas del tipo '3, 8, 10-12, 15' y devuelve un conjunto de números de página (1-based).
    """
    pages_to_delete = set()
    parts = [p.strip() for p in input_str.split(",") if p.strip()]

    for part in parts:
        if "-" in part:
            bounds = part.split("-")
            if len(bounds) != 2 or not bounds[0].isdigit() or not bounds[1].isdigit():
                raise ValueError(f"Rango no válido: '{part}'")
            start, end = int(bounds[0]), int(bounds[1])
            if start > end:
                raise ValueError(f"Rango invertido no válido: '{part}'")
            pages_to_delete.update(range(start, end + 1))
        else:
            if not part.isdigit():
                raise ValueError(f"Número de página no válido: '{part}'")
            pages_to_delete.add(int(part))

    return pages_to_delete


def run_delete_pages(session: PDFEditorSession) -> None:
    """Submenú para eliminar páginas individuales o rangos."""
    if not session.is_loaded():
        print("\nx No hay ningún documento en memoria.")
        return

    total = session.get_total_pages()
    print("\n--- Eliminar Páginas ---")
    print(f"Páginas totales actuales: {total}")
    print("Introduce las páginas/rangos a borrar separados por comas (ejemplo: 3, 8, 10-12, 15):")
    raw_input = input("> ").strip()

    if not raw_input:
        return

    try:
        pages_to_delete = parse_page_selection(raw_input, total)
        
        # Confirmación de las páginas que se van a eliminar
        sorted_pages = sorted(list(pages_to_delete))
        print(f"\nSe eliminarán las siguientes {len(sorted_pages)} página(s): {sorted_pages}")
        confirm = input("¿Confirmas la eliminación? (s/n): ").strip().lower()
        
        if confirm == 's':
            session.delete_pages(pages_to_delete)
            print(f"✓ Páginas eliminadas correctamente.")
            print(f"  Total de páginas restantes: {session.get_total_pages()}")
        else:
            print("Operación cancelada.")

    except Exception as e:
        print(f"x Error: {e}")

def run_adjust_margins(session: PDFEditorSession) -> None:
    """Submenú para ajustar márgenes horizontales (impares y pares)."""
    if not session.is_loaded():
        print("\nx No hay ningún documento en memoria.")
        return

    print("\n--- Ajustar Márgenes para Encuadernación ---")
    print("1) Modo Simétrico (mismo desplazamiento en sentidos opuestos)")
    print("2) Modo Asimétrico Independiente (desplazamiento personalizado para impares y pares)")
    print("3) Ajustar solo páginas IMPARES")
    print("4) Ajustar solo páginas PARES")
    print("0) Cancelar")

    opt = input("Selecciona una opción: ").strip()

    shift_odd = 0.0
    shift_even = 0.0

    try:
        if opt == "1":
            val = float(input("Introduce los mm a mover (+ desplaza a la derecha, - a la izquierda): ").strip())
            shift_odd = val
            shift_even = -val

        elif opt == "2":
            shift_odd = float(input("Desplazamiento para páginas IMPARES en mm (+ derecha / - izquierda): ").strip())
            shift_even = float(input("Desplazamiento para páginas PARES en mm (+ derecha / - izquierda): ").strip())

        elif opt == "3":
            shift_odd = float(input("Desplazamiento para páginas IMPARES en mm (+ derecha / - izquierda): ").strip())

        elif opt == "4":
            shift_even = float(input("Desplazamiento para páginas PARES en mm (+ derecha / - izquierda): ").strip())

        else:
            return

        print(f"\nResumen de ajustes:")
        print(f"  - Páginas IMPARES: {shift_odd:+.2f} mm")
        print(f"  - Páginas PARES:   {shift_even:+.2f} mm")

        confirm = input("¿Aplicar cambios? (s/n): ").strip().lower()
        if confirm == 's':
            session.adjust_margins(shift_odd, shift_even)
            print("✓ Márgenes ajustados correctamente.")
        else:
            print("Operación cancelada.")

    except ValueError:
        print("x Error: Por favor, introduce un número válido (ejemplo: 6 u 1.5).")
    except Exception as e:
        print(f"x Error al ajustar márgenes: {e}")

def run_insert_front_matter(session: PDFEditorSession) -> None:
    """Submenú para generar e insertar las 4 páginas de presentación al inicio."""
    print("\n--- Insertar Páginas de Portada (A4) ---")
    title = input("Título del libro: ").strip()
    if not title:
        print("x El título es obligatorio.")
        return

    subtitle = input("Subtítulo (opcional): ").strip()
    author = input("Nombre del autor: ").strip()
    isbn = input("ISBN [ - ]: ").strip() or "-"
    year_pub = input("Fecha/Año de publicación [2026]: ").strip() or "2026"
    year_print = input("Año de impresión [2026]: ").strip() or "2026"
    printed_by = input("Impreso por [ALS]: ").strip() or "ALS"

    try:
        session.insert_book_front_matter(
            title=title,
            subtitle=subtitle,
            author=author,
            isbn=isbn,
            year_pub=year_pub,
            year_print=year_print,
            printed_by=printed_by
        )
        print("\n✓ Se han generado e insertado las 4 páginas de portada al inicio en formato A4.")
        print(f"  Total páginas en la sesión: {session.get_total_pages()}")
    except Exception as e:
        print(f"x Error al generar la portada: {e}")

def run_insert_index(session: PDFEditorSession) -> None:
    """Submenú para cargar un archivo txt e insertar el índice maquetado."""
    print("\n--- Generar e Insertar Índice desde TXT ---")
    path_str = input("Ruta al archivo .txt del índice (ej: indice.txt): ").strip()

    if not path_str:
        print("x Error: Debes especificar el nombre o la ruta del archivo .txt.")
        return

    txt_path = Path(path_str).resolve()

    if not txt_path.exists() or not txt_path.is_file():
        print(f"x Error: No se encontró el archivo '{txt_path}'. Asegúrate de incluir la extensión .txt.")
        return

    print("\n¿Dónde deseas insertar el índice?")
    print("1) Al final del todo [Predeterminado]")
    print("2) Tras la portada (después de la página 4)")
    print("3) Al principio del todo (Página 1)")
    
    opt_pos = input("Selecciona posición [1]: ").strip() or "1"

    if opt_pos == "2":
        pos = "after_front_matter"
    elif opt_pos == "3":
        pos = "at_start"
    else:
        pos = "at_end"

    print("\n¿Qué disposición de márgenes debe tener la primera página del índice?")
    print("1) Página Impar (Lomo a la izquierda: 1.8cm izq / 1.2cm der) [Predeterminado]")
    print("2) Página Par (Lomo a la derecha: 1.2cm izq / 1.8cm der)")
    print("3) Centrado (Márgenes iguales: 1.5cm izq / 1.5cm der)")

    opt_margin = input("Selecciona disposición [1]: ").strip() or "1"

    if opt_margin == "2":
        margin_mode = "even"
    elif opt_margin == "3":
        margin_mode = "centered"
    else:
        margin_mode = "odd"

    try:
        session.insert_index_from_txt(txt_path, position=pos, margin_mode=margin_mode)
        print("\n✓ Índice generado e insertado correctamente.")
        print(f"  Total páginas en la sesión: {session.get_total_pages()}")
    except Exception as e:
        print(f"x Error al procesar el índice: {e}")

def run_insert_pdf_at(session: PDFEditorSession) -> None:
    """Submenú para insertar un archivo PDF completo en una posición específica."""
    if not session.is_loaded():
        print("x Primero debes cargar un PDF base.")
        return

    print("\n--- Insertar otro PDF en una posición específica ---")
    path_str = input("Ruta al archivo PDF que deseas insertar: ").strip()

    if not path_str:
        print("x Operación cancelada. Debes especificar una ruta.")
        return

    insert_path = Path(path_str).resolve()
    if not insert_path.exists() or not insert_path.is_file():
        print(f"x Error: No se encontró el archivo '{insert_path}'.")
        return

    total_pages = session.get_total_pages()
    print("\n¿Dónde deseas insertar este PDF?")
    print("1) Al principio del todo (Página 1)")
    print("2) Al final del todo [Predeterminado]")
    print(f"3) Después de una página específica (1 a {total_pages})")

    opt = input("Selecciona una opción [2]: ").strip() or "2"

    position = "end"
    target_page = 1

    if opt == "1":
        position = "start"
    elif opt == "3":
        position = "after_page"
        try:
            page_inp = input(f"Insertar después de la página (1-{total_pages}): ").strip()
            target_page = int(page_inp)
            if target_page < 1 or target_page > total_pages:
                print(f"x Número fuera de rango. Se ajustará entre 1 y {total_pages}.")
                target_page = max(1, min(target_page, total_pages))
        except ValueError:
            print("x Entrada inválida. Se insertará al final.")
            position = "end"

    try:
        session.insert_pdf_at(insert_path, position=position, page_num=target_page)
        print("\n✓ Documento PDF insertado correctamente.")
        print(f"  Total páginas actualizadas en la sesión: {session.get_total_pages()}")
    except Exception as e:
        print(f"x Error al insertar el PDF: {e}")

def run_impose_booklet(session: PDFEditorSession) -> None:
    """Submenú para realizar la imposición de cuadernillos."""
    if not session.is_loaded():
        print("x Primero debes cargar un PDF base.")
        return

    total_p = session.get_total_pages()
    print(f"\n--- Imposición de Cuadernillos (Folleto) ---")
    print(f"Páginas actuales del documento: {total_p}")

    print("\n¿Cómo deseas definir la estructura de cuadernillos?")
    print("1) Tamaño fijo para todos los cuadernillos (ej: 7 hojas / 28 pág por cuadernillo)")
    print("2) Lista personalizada por cuadernillo (ej: 7,7,7,7,7,6,7,7,7,7,7)")

    opt = input("Selecciona una opción [1]: ").strip() or "1"
    sheets_list = []

    if opt == "2":
        raw = input("Introduce las hojas de cada cuadernillo separadas por comas (ej: 7,7,7,7,7,6,7,7,7,7,7): ").strip()
        try:
            sheets_list = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            print("x Error: Introduce una lista válida de números enteros.")
            return
    else:
        try:
            h = int(input("Número de hojas por cuadernillo [7]: ").strip() or "7")
            total_needed = ceil(total_p / (h * 4))
            sheets_list = [h] * total_needed
        except ValueError:
            print("x Entrada no válida.")
            return

    # Cálculo informativo
    total_pages_covered = sum(s * 4 for s in sheets_list)
    print(f"\nResumen de imposición:")
    print(f"  * Cuadernillos a generar: {len(sheets_list)}")
    print(f"  * Páginas que cubrirá: {total_pages_covered} (Páginas originales: {total_p})")
    if total_pages_covered > total_p:
        print(f"  * Se añadirán {total_pages_covered - total_p} páginas en blanco al final para completar el último cuadernillo.")

    confirm = input("\n¿Proceder con la imposición? (s/n) [s]: ").strip().lower() or "s"
    if confirm != 's':
        print("Operación cancelada.")
        return

    try:
        session.impose_booklet(sheets_list)
        print("\n✓ Imposición completada correctamente.")
        print("  El PDF resultante está listo para imprimir a doble cara por el borde corto.")
    except Exception as e:
        print(f"x Error durante la imposición: {e}")