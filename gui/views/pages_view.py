"""
gui/views/pages_view.py - Vista para operaciones diversas sobre páginas del PDF.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, QFileDialog,
    QMessageBox, QComboBox, QCheckBox, QTabWidget, QFormLayout
)
from pdf_ops import PDFEditorSession
from cli_menu import parse_page_selection


class PagesView(QWidget):
    def __init__(self, session: PDFEditorSession, on_session_updated=None):
        super().__init__()
        self.session = session
        self.on_session_updated = on_session_updated
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        sub_tabs = QTabWidget()

        # ---------------------------------------------------------
        # Sub-pestaña 1: Estructura (Recortar, Borrar, Insertar)
        # ---------------------------------------------------------
        tab_struct = QWidget()
        struct_layout = QVBoxLayout(tab_struct)

        # 1.1 Extraer / Eliminar
        box_edit = QGroupBox("Recortar / Eliminar Páginas")
        h_edit = QHBoxLayout()

        layout_ext = QVBoxLayout()
        layout_ext.addWidget(QLabel("<b>Extraer Rango:</b>"))
        h_range = QHBoxLayout()
        h_range.addWidget(QLabel("De:"))
        self.spin_ext_start = QSpinBox()
        h_range.addWidget(self.spin_ext_start)
        h_range.addWidget(QLabel("A:"))
        self.spin_ext_end = QSpinBox()
        h_range.addWidget(self.spin_ext_end)
        layout_ext.addLayout(h_range)
        btn_ext = QPushButton("Extraer Rango")
        btn_ext.clicked.connect(self.run_extract)
        layout_ext.addWidget(btn_ext)
        h_edit.addLayout(layout_ext)

        h_edit.addSpacing(20)

        layout_del = QVBoxLayout()
        layout_del.addWidget(QLabel("<b>Eliminar Páginas Específicas:</b>"))
        self.txt_del_pages = QLineEdit()
        self.txt_del_pages.setPlaceholderText("Ej: 3, 8, 10-12")
        layout_del.addWidget(self.txt_del_pages)
        btn_del = QPushButton("Borrar Páginas")
        btn_del.clicked.connect(self.run_delete)
        layout_del.addWidget(btn_del)
        h_edit.addLayout(layout_del)

        box_edit.setLayout(h_edit)
        struct_layout.addWidget(box_edit)

        # 1.2 Insertar PDF o Páginas Blancas
        box_ins = QGroupBox("Insertar Contenido")
        v_ins = QVBoxLayout()

        # PDF
        h_pdf = QHBoxLayout()
        self.txt_ins_pdf = QLineEdit()
        self.txt_ins_pdf.setPlaceholderText("Ruta de PDF a insertar...")
        btn_browse_pdf = QPushButton("Examinar...")
        btn_browse_pdf.clicked.connect(self.browse_insert_pdf)
        self.combo_ins_pdf_pos = QComboBox()
        self.combo_ins_pdf_pos.addItems(["Al final", "Al principio", "Después de página..."])
        self.spin_ins_pdf_page = QSpinBox()
        h_pdf.addWidget(self.txt_ins_pdf)
        h_pdf.addWidget(btn_browse_pdf)
        h_pdf.addWidget(self.combo_ins_pdf_pos)
        h_pdf.addWidget(self.spin_ins_pdf_page)
        btn_run_pdf = QPushButton("Insertar PDF")
        btn_run_pdf.clicked.connect(self.run_insert_pdf)
        h_pdf.addWidget(btn_run_pdf)
        v_ins.addLayout(h_pdf)

        # Hojas Blancas
        h_blank = QHBoxLayout()
        h_blank.addWidget(QLabel("<b>Insertar Páginas Blancas:</b>"))
        self.spin_blank_count = QSpinBox()
        self.spin_blank_count.setRange(1, 100)
        self.spin_blank_count.setValue(1)
        h_blank.addWidget(self.spin_blank_count)
        h_blank.addWidget(QLabel("páginas"))
        self.combo_blank_pos = QComboBox()
        self.combo_blank_pos.addItems(["Al final", "Al principio", "Después de página..."])
        self.spin_blank_page = QSpinBox()
        h_blank.addWidget(self.combo_blank_pos)
        h_blank.addWidget(self.spin_blank_page)
        btn_run_blank = QPushButton("Insertar Blancas")
        btn_run_blank.clicked.connect(self.run_insert_blanks)
        h_blank.addWidget(btn_run_blank)
        v_ins.addLayout(h_blank)

        box_ins.setLayout(v_ins)
        struct_layout.addWidget(box_ins)

        # 1.3 Generar e Insertar Páginas de Portada (Front Matter - A4)
        box_front = QGroupBox("Generar e Insertar Portada Inicial (4 páginas A4)")
        form_front = QFormLayout()

        self.txt_front_title = QLineEdit()
        self.txt_front_title.setPlaceholderText("Título obligatorio del libro")

        self.txt_front_subtitle = QLineEdit()
        self.txt_front_subtitle.setPlaceholderText("Subtítulo (opcional)")

        self.txt_front_author = QLineEdit()
        self.txt_front_author.setPlaceholderText("Nombre del autor")

        self.txt_front_isbn = QLineEdit()
        self.txt_front_isbn.setText("-")

        self.txt_front_pub_year = QLineEdit()
        self.txt_front_pub_year.setText("2026")

        self.txt_front_print_year = QLineEdit()
        self.txt_front_print_year.setText("2026")

        self.txt_front_printed_by = QLineEdit()
        self.txt_front_printed_by.setText("ALS")

        form_front.addRow("Título *:", self.txt_front_title)
        form_front.addRow("Subtítulo:", self.txt_front_subtitle)
        form_front.addRow("Autor:", self.txt_front_author)

        h_front_meta = QHBoxLayout()
        h_front_meta.addWidget(QLabel("ISBN:"))
        h_front_meta.addWidget(self.txt_front_isbn)
        h_front_meta.addWidget(QLabel("Año Pub.:"))
        h_front_meta.addWidget(self.txt_front_pub_year)
        h_front_meta.addWidget(QLabel("Año Imp.:"))
        h_front_meta.addWidget(self.txt_front_print_year)
        h_front_meta.addWidget(QLabel("Impreso por:"))
        h_front_meta.addWidget(self.txt_front_printed_by)

        form_front.addRow(h_front_meta)

        btn_run_front = QPushButton("Generar e Insertar Portada (4 Págs)")
        btn_run_front.clicked.connect(self.run_insert_front_matter)
        form_front.addRow(btn_run_front)

        box_front.setLayout(form_front)
        struct_layout.addWidget(box_front)

        struct_layout.addStretch()
        sub_tabs.addTab(tab_struct, "Estructura e Inserción")

        # ---------------------------------------------------------
        # Sub-pestaña 2: Márgenes y Encabezados/Pies
        # ---------------------------------------------------------
        tab_format = QWidget()
        format_layout = QVBoxLayout(tab_format)

        # Márgenes
        box_margins = QGroupBox("Ajuste de Márgenes de Encuadernación")
        h_m = QHBoxLayout()
        h_m.addWidget(QLabel("Impares (mm):"))
        self.spin_m_odd = QDoubleSpinBox()
        self.spin_m_odd.setRange(-50.0, 50.0)
        h_m.addWidget(self.spin_m_odd)
        h_m.addWidget(QLabel("Pares (mm):"))
        self.spin_m_even = QDoubleSpinBox()
        self.spin_m_even.setRange(-50.0, 50.0)
        h_m.addWidget(self.spin_m_even)
        btn_margins = QPushButton("Aplicar Márgenes")
        btn_margins.clicked.connect(self.run_margins)
        h_m.addWidget(btn_margins)
        box_margins.setLayout(h_m)
        format_layout.addWidget(box_margins)

        # Cabecera
        box_hdr = QGroupBox("Modificar / Ocultar Cabecera")
        form_hdr = QFormLayout()
        self.txt_hdr_text = QLineEdit()
        self.txt_hdr_text.setPlaceholderText("Dejar vacío para ocultar/parchear en blanco")
        self.txt_hdr_pages = QLineEdit()
        self.txt_hdr_pages.setPlaceholderText("Ej: 1-4 o dejar vacío para aplicar a todo")
        form_hdr.addRow("Texto Cabecera:", self.txt_hdr_text)
        form_hdr.addRow("Páginas Objetivo:", self.txt_hdr_pages)
        btn_apply_hdr = QPushButton("Aplicar Cambios en Cabecera")
        btn_apply_hdr.clicked.connect(self.run_header)
        form_hdr.addRow(btn_apply_hdr)
        box_hdr.setLayout(form_hdr)
        format_layout.addWidget(box_hdr)

        # Pie de página
        box_ftr = QGroupBox("Modificar / Renumerar Pie de Página")
        form_ftr = QFormLayout()
        self.chk_ftr_renumber = QCheckBox("Renumerar páginas automáticamente")
        self.chk_ftr_renumber.setChecked(True)
        self.spin_ftr_offset = QSpinBox()
        self.spin_ftr_offset.setRange(0, 100)
        self.spin_ftr_offset.setValue(0)

        self.txt_ftr_pages = QLineEdit()
        self.txt_ftr_pages.setPlaceholderText("Ej: 1-4 para ocultar pie en portada")

        form_ftr.addRow(self.chk_ftr_renumber)
        form_ftr.addRow("Desfase de numeración (Offset):", self.spin_ftr_offset)
        form_ftr.addRow("Ocultar pie en páginas:", self.txt_ftr_pages)
        btn_apply_ftr = QPushButton("Aplicar Cambios en Pie de Página")
        btn_apply_ftr.clicked.connect(self.run_footer)
        form_ftr.addRow(btn_apply_ftr)
        box_ftr.setLayout(form_ftr)
        format_layout.addWidget(box_ftr)

        format_layout.addStretch()
        sub_tabs.addTab(tab_format, "Márgenes, Cabeceras y Pies")

        layout.addWidget(sub_tabs)

    def update_spin_bounds(self):
        total = self.session.get_total_pages() if self.session.is_loaded() else 1
        total = max(1, total)
        self.spin_ext_start.setRange(1, total)
        self.spin_ext_end.setRange(1, total)
        self.spin_ext_end.setValue(total)
        self.spin_ins_pdf_page.setRange(1, total)
        self.spin_blank_page.setRange(1, total)

    def browse_insert_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF a insertar", "", "PDF (*.pdf)")
        if path:
            self.txt_ins_pdf.setText(path)

    def run_extract(self):
        if not self.session.is_loaded(): return
        try:
            self.session.extract_page_range(self.spin_ext_start.value(), self.spin_ext_end.value())
            QMessageBox.information(self, "Éxito", f"Páginas restantes: {self.session.get_total_pages()}")
            if self.on_session_updated: self.on_session_updated()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def run_delete(self):
        if not self.session.is_loaded(): return
        raw = self.txt_del_pages.text().strip()
        if not raw: return
        try:
            pages = parse_page_selection(raw, self.session.get_total_pages())
            self.session.delete_pages(pages)
            self.txt_del_pages.clear()
            QMessageBox.information(self, "Éxito", f"Páginas restantes: {self.session.get_total_pages()}")
            if self.on_session_updated: self.on_session_updated()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def run_insert_pdf(self):
        if not self.session.is_loaded(): return
        p = Path(self.txt_ins_pdf.text().strip())
        if not p.exists(): return
        idx = self.combo_ins_pdf_pos.currentIndex()
        pos = "end" if idx == 0 else ("start" if idx == 1 else "after_page")
        try:
            self.session.insert_pdf_at(p, position=pos, page_num=self.spin_ins_pdf_page.value())
            QMessageBox.information(self, "Éxito", f"PDF Insertado. Total páginas: {self.session.get_total_pages()}")
            if self.on_session_updated: self.on_session_updated()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def run_insert_blanks(self):
        if not self.session.is_loaded(): return
        count = self.spin_blank_count.value()
        idx = self.combo_blank_pos.currentIndex()
        pos = "end" if idx == 0 else ("start" if idx == 1 else "after_page")
        try:
            self.session.insert_blank_pages(count=count, position=pos, page_num=self.spin_blank_page.value())
            QMessageBox.information(self, "Éxito", f"Insertadas {count} página(s) en blanco. Total: {self.session.get_total_pages()}")
            if self.on_session_updated: self.on_session_updated()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def run_insert_front_matter(self):
        if not self.session.is_loaded():
            QMessageBox.warning(self, "Atención", "Primero debes cargar un documento PDF.")
            return

        title = self.txt_front_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Campo Obligatorio", "El título del libro es obligatorio.")
            return

        subtitle = self.txt_front_subtitle.text().strip()
        author = self.txt_front_author.text().strip()
        isbn = self.txt_front_isbn.text().strip() or "-"
        year_pub = self.txt_front_pub_year.text().strip() or "2026"
        year_print = self.txt_front_print_year.text().strip() or "2026"
        printed_by = self.txt_front_printed_by.text().strip() or "ALS"

        try:
            self.session.insert_book_front_matter(
                title=title,
                subtitle=subtitle,
                author=author,
                isbn=isbn,
                year_pub=year_pub,
                year_print=year_print,
                printed_by=printed_by
            )
            QMessageBox.information(
                self, "Éxito",
                f"Se han generado e insertado las 4 páginas de portada al inicio en formato A4.\n"
                f"Total páginas en la sesión: {self.session.get_total_pages()}"
            )
            if self.on_session_updated:
                self.on_session_updated()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar la portada: {e}")

    def run_margins(self):
        if not self.session.is_loaded(): return
        try:
            self.session.adjust_margins(self.spin_m_odd.value(), self.spin_m_even.value())
            QMessageBox.information(self, "Éxito", "Márgenes ajustados.")
            if self.on_session_updated: self.on_session_updated()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def run_header(self):
        if not self.session.is_loaded(): return
        text = self.txt_hdr_text.text().strip()
        raw_p = self.txt_hdr_pages.text().strip()
        target_pages = parse_page_selection(raw_p, self.session.get_total_pages()) if raw_p else None
        try:
            self.session.modify_header(text=text, target_pages=target_pages)
            QMessageBox.information(self, "Éxito", "Cabecera actualizada.")
            if self.on_session_updated: self.on_session_updated()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))

    def run_footer(self):
        if not self.session.is_loaded(): return
        raw_p = self.txt_ftr_pages.text().strip()
        hide_pages = parse_page_selection(raw_p, self.session.get_total_pages()) if raw_p else []
        try:
            self.session.modify_footer(
                renumber=self.chk_ftr_renumber.isChecked(),
                offset=self.spin_ftr_offset.value(),
                hide_pages=hide_pages
            )
            QMessageBox.information(self, "Éxito", "Pie de página actualizado.")
            if self.on_session_updated: self.on_session_updated()
        except Exception as e: QMessageBox.critical(self, "Error", str(e))