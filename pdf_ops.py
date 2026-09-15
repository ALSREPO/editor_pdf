"""
pdf_ops.py - Módulo para la manipulación en memoria de archivos PDF.
"""

import io
from pathlib import Path
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.lib.colors import white
from reportlab.pdfgen import canvas


class PDFEditorSession:
    """Clase que mantiene el documento PDF actual en memoria y permite aplicar cambios acumulativos."""

    def __init__(self):
        self.writer: PdfWriter | None = None
        self.original_path: Path | None = None  # Ruta completa del archivo cargado
        self.original_name: str = ""
        self.has_unsaved_changes: bool = False
        self._original_bytes: bytes | None = None  # Resguardo del PDF original intacto

    def load_pdf(self, pdf_path: str | Path) -> bool:
        """Carga un archivo PDF del disco reteniendo su ruta original."""
        path = Path(pdf_path).resolve()
        if not path.exists() or path.suffix.lower() != ".pdf":
            return False

        with open(path, "rb") as f:
            self._original_bytes = f.read()

        self.original_path = path
        self.original_name = path.stem
        self.reset_to_original()
        return True

    def reset_to_original(self) -> None:
        """Restaura la sesión en memoria al estado original del archivo cargado."""
        if not self._original_bytes:
            return

        reader = PdfReader(io.BytesIO(self._original_bytes))
        self.writer = PdfWriter()
        for page in reader.pages:
            self.writer.add_page(page)

        self.has_unsaved_changes = False

    def is_loaded(self) -> bool:
        """Indica si hay un PDF cargado en la sesión."""
        return self.writer is not None and len(self.writer.pages) > 0

    def get_total_pages(self) -> int:
        """Devuelve el número total de páginas del PDF en memoria."""
        return len(self.writer.pages) if self.is_loaded() else 0

    def extract_page_range(self, start_page: int, end_page: int) -> None:
        """Conserva únicamente el rango de páginas indicado, descartando el resto."""
        if not self.is_loaded():
            raise RuntimeError("No hay ningún PDF cargado.")

        total = self.get_total_pages()
        # Validar rangos (convertimos de 1-based a 0-based)
        if start_page < 1 or end_page > total or start_page > end_page:
            raise ValueError(f"Rango inválido. El documento actual tiene {total} página(s).")

        new_writer = PdfWriter()
        # pypdf usa índices 0-based
        for i in range(start_page - 1, end_page):
            new_writer.add_page(self.writer.pages[i])

        self.writer = new_writer
        self.has_unsaved_changes = True

    def modify_headers_and_footers(
        self,
        header_mode: str = "keep",      # 'keep', 'hide', 'custom'
        header_even: str = "",
        header_odd: str = "",
        header_italic: bool = False,
        footer_mode: str = "keep",      # 'keep', 'hide', 'number'
        start_number: int = 1
    ) -> None:
        """
        Aplica modificaciones de cabecera y/o pie de página sobre el documento en memoria.
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
        if not self.is_loaded():
            raise RuntimeError("No hay ningún PDF cargado.")

        new_writer = PdfWriter()

        for idx, page in enumerate(self.writer.pages):
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            page_num = idx + 1  # 1-based

            packet = io.BytesIO()
            c = canvas.Canvas(packet, pagesize=(page_width, page_height))

            # --- GESTIÓN DE LA CABECERA ---
            if header_mode in ("hide", "custom"):
                tamano_cabecera = 50
                #tamano_cabecera = 60
                c.setFillColor(white)
                c.setStrokeColor(white)
                c.rect(0, page_height - tamano_cabecera, page_width, tamano_cabecera, fill=True, stroke=False)

                if header_mode == "custom":
                    c.setFillColorRGB(0, 0, 0)
                    font_name = "Helvetica-Oblique" if header_italic else "Helvetica"
                    c.setFont(font_name, 9)

                    text = header_even if page_num % 2 == 0 else header_odd
                    if text:
                        c.drawCentredString(page_width / 2.0, page_height - 45, text)

            # --- GESTIÓN DEL PIE DE PÁGINA ---
            if footer_mode in ("hide", "number"):
                tamano_pie = 55
                #tamano_pie = 75
                c.setFillColor(white)
                c.setStrokeColor(white)
                c.rect(0, 0, page_width, tamano_pie, fill=True, stroke=False)

                if footer_mode == "number":
                    c.setFillColorRGB(0, 0, 0)
                    c.setFont("Helvetica", 9)

                    current_page_label = start_number + idx
                    label_text = f"- {current_page_label} -"
                    margin = 40 # Margen lateral en puntos (pt) desde el borde de la página

                    if page_num % 2 == 0:
                        # Página PAR: Esquina izquierda
                        c.drawString(margin + 20, 40, label_text)
                    else:
                        # Página IMPAR: Esquina derecha
                        c.drawRightString(page_width - margin, 40, label_text)

            # Si se aplicó alguna capa, se combina
            if header_mode != "keep" or footer_mode != "keep":
                c.save()
                packet.seek(0)
                overlay_pdf = PdfReader(packet)
                page.merge_page(overlay_pdf.pages[0])

            new_writer.add_page(page)

        self.writer = new_writer
        self.has_unsaved_changes = True

    def update_original_from_bytes(self, new_bytes: bytes, new_path: Path) -> None:
        """Actualiza la copia original almacenada en memoria con un nuevo estado/archivo."""
        self._original_bytes = new_bytes
        self.original_path = new_path.resolve()
        self.original_name = self.original_path.stem
        self.reset_to_original()

    def save_to_disk(self, output_path: str | Path, overwrite: bool = False) -> None:
        """
        Guarda la versión modificada en disco.
        - overwrite=True: Sobrescribe el original en disco y actualiza la sesión con el nuevo estado.
        - overwrite=False: Guarda en un archivo nuevo y mantiene la copia original base en memoria.
        """
        if not self.is_loaded():
            raise RuntimeError("No hay nada que guardar.")

        out = Path(output_path).resolve()

        # Generar los bytes del documento actual en memoria
        buffer = io.BytesIO()
        self.writer.write(buffer)
        saved_bytes = buffer.getvalue()

        # Asegurar que el directorio destino existe antes de escribir
        out.parent.mkdir(parents=True, exist_ok=True)

        # Escribir en el disco
        with open(out, "wb") as f_out:
            f_out.write(saved_bytes)

        if overwrite:
            # Pasa a ser el nuevo documento base de la sesión
            self.update_original_from_bytes(saved_bytes, out)
        else:
            # Mantiene cargado el documento base original previa a la modificación
            self.reset_to_original()

    def insert_blank_pages(self, position_index: int, count: int = 1) -> None:
        """
        Inserta 'count' páginas en blanco en la posición deseada.
        - position_index: Índice 0-based donde se insertarán las páginas
          (0 = al principio, len(pages) = al final).
        """
        if not self.is_loaded():
            raise RuntimeError("No hay ningún PDF cargado.")

        total_pages = self.get_total_pages()
        if position_index < 0 or position_index > total_pages:
            raise ValueError(f"Posición inválida. Debe estar entre 0 y {total_pages}.")

        # Obtener las dimensiones de la primera página como referencia para las páginas en blanco
        first_page = self.writer.pages[0]
        page_width = float(first_page.mediabox.width)
        page_height = float(first_page.mediabox.height)

        new_writer = PdfWriter()
        current_pages = list(self.writer.pages)

        # Copiar páginas anteriores a la posición de inserción
        for i in range(position_index):
            new_writer.add_page(current_pages[i])

        # Insertar las páginas en blanco
        for _ in range(count):
            new_writer.add_blank_page(width=page_width, height=page_height)

        # Copiar las páginas restantes
        for i in range(position_index, total_pages):
            new_writer.add_page(current_pages[i])

        self.writer = new_writer
        self.has_unsaved_changes = True

    def merge_pdfs(self, pdf_paths: list[str | Path]) -> None:
        """
        Une una lista de archivos PDF e integra el resultado en la sesión activa.
        - pdf_paths: Lista de rutas a los archivos PDF que se van a fusionar.
        """
        if not pdf_paths:
            raise ValueError("La lista de archivos PDF a unir está vacía.")

        valid_paths = [Path(p).resolve() for p in pdf_paths if Path(p).is_file() and Path(p).suffix.lower() == ".pdf"]
        if not valid_paths:
            raise FileNotFoundError("No se encontraron archivos PDF válidos.")

        new_writer = PdfWriter()
        for path in valid_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                new_writer.add_page(page)

        out_buffer = io.BytesIO()
        new_writer.write(out_buffer)
        self._original_bytes = out_buffer.getvalue()
        
        # Al unir, asignamos como ruta de referencia la ubicación del primer PDF de la lista
        self.original_path = valid_paths[0].parent / f"merged_{valid_paths[0].stem}.pdf"
        self.original_name = self.original_path.stem
        self.reset_to_original()

    def delete_pages(self, pages_to_delete: set[int]) -> None:
        """
        Elimina las páginas especificadas (basado en números de página de 1 a N).
        - pages_to_delete: Conjunto de números de página (1-based) a eliminar.
        """
        if not self.is_loaded():
            raise RuntimeError("No hay ningún PDF cargado.")

        total = self.get_total_pages()
        invalid_pages = [p for p in pages_to_delete if p < 1 or p > total]
        if invalid_pages:
            raise ValueError(f"Las siguientes páginas no existen en el documento (total: {total}): {invalid_pages}")

        if len(pages_to_delete) >= total:
            raise ValueError("No se pueden eliminar todas las páginas del documento.")

        new_writer = PdfWriter()
        for idx, page in enumerate(self.writer.pages):
            page_num = idx + 1
            if page_num not in pages_to_delete:
                new_writer.add_page(page)

        self.writer = new_writer
        self.has_unsaved_changes = True

    def adjust_margins(self, shift_odd_mm: float, shift_even_mm: float) -> None:
        """
        Desplaza horizontalmente el contenido de las páginas para ajustar los márgenes de lomo.
        - shift_odd_mm: Milímetros a desplazar en páginas impares (+ a la derecha, - a la izquierda).
        - shift_even_mm: Milímetros a desplazar en páginas pares (+ a la derecha, - a la izquierda).
        """
        if not self.is_loaded():
            raise RuntimeError("No hay ningún PDF cargado.")

        mm_to_pts = 2.83465
        shift_odd_pts = shift_odd_mm * mm_to_pts
        shift_even_pts = shift_even_mm * mm_to_pts

        new_writer = PdfWriter()

        for idx, page in enumerate(self.writer.pages):
            page_num = idx + 1
            # Determinar desplazamiento según paridad
            dx = shift_odd_pts if page_num % 2 != 0 else shift_even_pts

            if dx != 0:
                # Aplicar matriz de transformación de traducción horizontal
                page.add_transformation(Transformation().translate(tx=dx, ty=0))

            new_writer.add_page(page)

        self.writer = new_writer
        self.has_unsaved_changes = True

    def insert_book_front_matter(
        self,
        title: str,
        subtitle: str,
        author: str,
        isbn: str = "-",
        year_pub: str = "2026",
        year_print: str = "2026",
        printed_by: str = "ALS"
    ) -> None:
        """
        Genera e inserta 4 páginas iniciales de libro en formato A4 respetando
        márgenes de lomo y fuentes nativas Helvetica/Times-Roman.
        """
        buffer = io.BytesIO()
        ajuste_ancho = 0.726  # Factor de escala para ajustar el tamaño de la página si es necesario
        ajuste_alto = 0.77   # Factor de escala para ajustar el tamaño de la página si es necesario
        a4_width, a4_height = 595.27 * ajuste_ancho, 841.89 * ajuste_alto  # Dimensiones A4 en puntos

        # Conversión de márgenes a puntos
        top_margin = 1.0 * 28.3465    # 1.0 cm
        bottom_margin = 2.0 * 28.3465 # 2.0 cm
        inner_margin = 1.8 * 28.3465  # 1.8 cm
        outer_margin = 1.2 * 28.3465  # 1.2 cm

        c = canvas.Canvas(buffer, pagesize=(a4_width, a4_height))

        # Helper para resolver el margen izquierdo/derecho según la paridad de la página
        def get_page_margins(page_num: int):
            if page_num % 2 != 0:
                # Impar: Lomo a la izquierda
                return inner_margin, outer_margin
            else:
                # Par: Lomo a la derecha
                return outer_margin, inner_margin

        # --- PÁGINA 1: Título y Subtítulo ---
        m_left, m_right = get_page_margins(1)
        content_width = a4_width - m_left - m_right
        center_x = m_left + (content_width / 2.0)
        y = a4_height - top_margin - 80

        c.setFont("Helvetica-Bold", 21)
        c.drawCentredString(center_x, y, title)

        if subtitle:
            c.setFont("Helvetica", 14)
            c.drawCentredString(center_x, y - 35, subtitle)
        c.showPage()

        # --- PÁGINA 2: Créditos Editoriales ---
        m_left, m_right = get_page_margins(2)
        y = bottom_margin + 0

        c.setFont("Times-Roman", 8)
        c.drawString(m_left, y + 45, f"{title}{f', {subtitle}' if subtitle else ''}")
        c.drawString(m_left, y + 33, f"Autor: {author}")
        c.drawString(m_left, y + 21, f"Fecha publicación: {year_pub}")
        c.drawString(m_left, y + 9, f"ISBN: {isbn}")
        c.drawString(m_left, y - 3, f"Impreso por {printed_by} en {year_print}")
        c.showPage()

        # --- PÁGINA 3: Autor, Título y Subtítulo ---
        m_left, m_right = get_page_margins(3)
        center_x = m_left + ((a4_width - m_left - m_right) / 2.0)
        y = a4_height - top_margin - 80

        c.setFont("Helvetica", 14)
        c.drawCentredString(center_x, y, author)

        c.setFont("Helvetica-Bold", 21)
        c.drawCentredString(center_x, y - 40, title)

        if subtitle:
            c.setFont("Helvetica", 12)
            c.drawCentredString(center_x, y - 70, subtitle)
        c.showPage()

        # --- PÁGINA 4: Hoja en Blanco ---
        c.showPage()
        c.save()

        # Unir las 4 páginas generadas al inicio del documento cargado
        buffer.seek(0)
        front_reader = PdfReader(buffer)
        new_writer = PdfWriter()

        for page in front_reader.pages:
            new_writer.add_page(page)

        if self.is_loaded():
            for page in self.writer.pages:
                new_writer.add_page(page)

        self.writer = new_writer
        self.has_unsaved_changes = True

    def insert_index_from_txt(
        self,
        txt_path: Path,
        position: str = "at_end",
        margin_mode: str = "odd"
    ) -> None:
        """
        Lee un archivo .txt con la estructura del índice y genera las páginas
        maquetadas en A4 al estilo LaTeX para insertarlas en el PDF.
        - margin_mode: 'odd' (comienza en impar), 'even' (comienza en par), 'centered' (márgenes iguales).
        """
        if not txt_path.exists() or not txt_path.is_file():
            raise ValueError(f"La ruta especificada no es un archivo válido: {txt_path}")

        entries = []
        with open(txt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3:
                    entries.append({
                        "type": parts[0].upper(),
                        "title": parts[1],
                        "page": parts[2]
                    })

        if not entries:
            raise ValueError("El archivo .txt no contiene entradas válidas con formato 'TIPO | TÍTULO | PÁGINA'.")

        buffer = io.BytesIO()
        ajuste_ancho = 0.726  # Factor de escala para ajustar el tamaño de la página si es necesario
        ajuste_alto = 0.77   # Factor de escala para ajustar el tamaño de la página si es necesario
        a4_width, a4_height = 595.27 * ajuste_ancho, 841.89 * ajuste_alto  # Dimensiones A4 en puntos

        top_margin = 1.0 * 28.3465
        bottom_margin = 2.0 * 28.3465
        inner_margin = 1.8 * 28.3465
        outer_margin = 1.2 * 28.3465
        centered_margin = 1.5 * 28.3465

        c = canvas.Canvas(buffer, pagesize=(a4_width, a4_height))
        page_index = 0  # Contador relativo de páginas del índice

        def get_margins(idx: int):
            if margin_mode == "centered":
                return centered_margin, centered_margin
            elif margin_mode == "even":
                # La primera página (idx 0) es Par (lomo a la derecha)
                return (outer_margin, inner_margin) if idx % 2 == 0 else (inner_margin, outer_margin)
            else:
                # 'odd': La primera página (idx 0) es Impar (lomo a la izquierda)
                return (inner_margin, outer_margin) if idx % 2 == 0 else (outer_margin, inner_margin)

        m_left, m_right = get_margins(page_index)
        content_width = a4_width - m_left - m_right
        y = a4_height - top_margin - 60

        # Encabezado del Índice ALINEADO A LA DERECHA
        c.setFont("Helvetica-Bold", 18)
        c.drawRightString(m_left + content_width, y, "Índice General")
        y -= 35

        for entry in entries:
            if y < bottom_margin + 20:
                c.showPage()
                page_index += 1
                m_left, m_right = get_margins(page_index)
                content_width = a4_width - m_left - m_right
                y = a4_height - top_margin - 30

            etype = entry["type"]
            title = entry["title"]
            page_str = entry["page"]

            if etype == "L":    # Libro
                y -= 10
                font_name, font_size = "Times-Bold", 13
                indent = 0
                has_dots = False
            elif etype == "C":  # Capítulo
                y -= 5
                font_name, font_size = "Times-Bold", 10
                indent = 0
                has_dots = False
            elif etype == "S":  # Sección
                font_name, font_size = "Times-Roman", 9
                indent = 15
                has_dots = True
            elif etype == "SS": # Subsección
                font_name, font_size = "Times-Roman", 9
                indent = 30
                has_dots = True
            else:
                continue

            c.setFont(font_name, font_size)
            x_start = m_left + indent
            x_end = m_left + content_width

            c.drawString(x_start, y, title)
            c.drawRightString(x_end, y, page_str)

            if has_dots:
                title_width = c.stringWidth(title, font_name, font_size)
                page_width = c.stringWidth(page_str, font_name, font_size)

                dots_start_x = x_start + title_width + 8
                dots_end_x = x_end - page_width - 8

                if dots_end_x > dots_start_x:
                    c.setFont("Times-Roman", 9)
                    dot_w = c.stringWidth(". ", "Times-Roman", 9)
                    curr_x = dots_start_x
                    while curr_x + dot_w < dots_end_x:
                        c.drawString(curr_x, y, ". ")
                        curr_x += dot_w * 1.8

            y -= 12

        c.showPage()
        c.save()

        buffer.seek(0)
        index_reader = PdfReader(buffer)
        new_writer = PdfWriter()

        if self.is_loaded():
            total_orig = len(self.writer.pages)

            if position == "at_end":
                for page in self.writer.pages:
                    new_writer.add_page(page)
                for page in index_reader.pages:
                    new_writer.add_page(page)

            elif position == "after_front_matter" and total_orig >= 4:
                for i in range(4):
                    new_writer.add_page(self.writer.pages[i])
                for page in index_reader.pages:
                    new_writer.add_page(page)
                for i in range(4, total_orig):
                    new_writer.add_page(self.writer.pages[i])

            else:
                for page in index_reader.pages:
                    new_writer.add_page(page)
                for page in self.writer.pages:
                    new_writer.add_page(page)
        else:
            for page in index_reader.pages:
                new_writer.add_page(page)

        self.writer = new_writer
        self.has_unsaved_changes = True

    def insert_pdf_at(self, pdf_to_insert_path: Path, position: str = "end", page_num: int = 1) -> None:
        """
        Inserta el contenido de otro archivo PDF en una posición específica:
        - position: 'start' (al principio), 'end' (al final), 'after_page' (después de page_num).
        """
        if not pdf_to_insert_path.exists() or not pdf_to_insert_path.is_file():
            raise ValueError(f"El archivo especificado no existe o no es válido: {pdf_to_insert_path}")

        try:
            insert_reader = PdfReader(pdf_to_insert_path)
        except Exception as e:
            raise ValueError(f"No se pudo leer el PDF a insertar: {e}")

        new_writer = PdfWriter()
        total_orig = len(self.writer.pages) if self.is_loaded() else 0

        if not self.is_loaded() or total_orig == 0:
            # Si no hay un PDF base cargado, el PDF insertado pasa a ser el documento base
            for page in insert_reader.pages:
                new_writer.add_page(page)
        elif position == "start":
            # Insertar al principio
            for page in insert_reader.pages:
                new_writer.add_page(page)
            for page in self.writer.pages:
                new_writer.add_page(page)
        elif position == "end":
            # Insertar al final
            for page in self.writer.pages:
                new_writer.add_page(page)
            for page in insert_reader.pages:
                new_writer.add_page(page)
        elif position == "after_page":
            # Validar rango de la página de destino (1-based)
            target_page = max(1, min(page_num, total_orig))
            for i in range(target_page):
                new_writer.add_page(self.writer.pages[i])
            for page in insert_reader.pages:
                new_writer.add_page(page)
            for i in range(target_page, total_orig):
                new_writer.add_page(self.writer.pages[i])

        self.writer = new_writer
        self.has_unsaved_changes = True