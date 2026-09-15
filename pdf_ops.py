"""
pdf_ops.py - Módulo para la manipulación en memoria de archivos PDF.
"""

import io
from pathlib import Path
from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import white
from reportlab.pdfgen import canvas


class PDFEditorSession:
    """Clase que mantiene el documento PDF actual en memoria y permite aplicar cambios acumulativos."""

    def __init__(self):
        self.writer: PdfWriter | None = None
        self.original_name: str = ""
        self.has_unsaved_changes: bool = False
        self._original_bytes: bytes | None = None  # Resguardo del PDF original intacto

    def load_pdf(self, pdf_path: str | Path) -> bool:
        """Carga un archivo PDF del disco a la sesión en memoria."""
        path = Path(pdf_path).resolve()
        if not path.exists() or path.suffix.lower() != ".pdf":
            return False

        with open(path, "rb") as f:
            self._original_bytes = f.read()

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

    def save_to_disk(self, output_path: str | Path, keep_original: bool = True) -> None:
        """Guarda la versión modificada en disco y, opcionalmente, restaura el original en memoria."""
        if not self.is_loaded():
            raise RuntimeError("No hay nada que guardar.")

        out = Path(output_path)
        with open(out, "wb") as f_out:
            self.writer.write(f_out)

        # Al terminar de guardar, volvemos a dejar cargado el documento original si se requiere
        if keep_original:
            self.reset_to_original()
        else:
            self.has_unsaved_changes = False

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

        valid_paths = [Path(p) for p in pdf_paths if Path(p).is_file() and Path(p).suffix.lower() == ".pdf"]
        
        if not valid_paths:
            raise FileNotFoundError("No se encontraron archivos PDF válidos en la lista proporcionada.")

        new_writer = PdfWriter()

        for path in valid_paths:
            reader = PdfReader(path)
            for page in reader.pages:
                new_writer.add_page(page)

        self.writer = new_writer
        self.original_name = f"merged_{valid_paths[0].stem}"
        self.has_unsaved_changes = True