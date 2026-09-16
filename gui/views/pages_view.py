"""
gui/views/pages_view.py - Vista para operaciones diversas sobre páginas del PDF.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, QFileDialog,
    QMessageBox, QComboBox, QCheckBox
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

        # Group 1: Extraer / Eliminar Páginas
        box_page_edit = QGroupBox("Recortar / Eliminar Páginas")
        layout_edit = QHBoxLayout()

        # Extraer rango
        layout_extract = QVBoxLayout()
        layout_extract.addWidget(QLabel("<b>Extraer Rango de Páginas:</b>"))
        h_ext = QHBoxLayout()
        self.spin_ext_start = QSpinBox()
        self.spin_ext_end = QSpinBox()
        h_ext.addWidget(QLabel("De:"))
        h_ext.addWidget(self.spin_ext_start)
        h_ext.addWidget(QLabel("A:"))
        h_ext.addWidget(self.spin_ext_end)
        layout_extract.addLayout(h_ext)
        btn_extract = QPushButton("Aplicar Recorte")
        btn_extract.clicked.connect(self.run_extract)
        layout_extract.addWidget(btn_extract)
        layout_edit.addLayout(layout_extract)

        layout_edit.addSpacing(20)

        # Eliminar selección
        layout_del = QVBoxLayout()
        layout_del.addWidget(QLabel("<b>Eliminar Páginas Específicas:</b>"))
        self.txt_del_pages = QLineEdit()
        self.txt_del_pages.setPlaceholderText("Ej: 3, 8, 10-12, 15")
        layout_del.addWidget(self.txt_del_pages)
        btn_del = QPushButton("Borrar Páginas")
        btn_del.clicked.connect(self.run_delete)
        layout_del.addWidget(btn_del)
        layout_edit.addLayout(layout_del)

        box_page_edit.setLayout(layout_edit)
        layout.addWidget(box_page_edit)

        # Group 2: Insertar PDF / Blancas
        box_insert = QGroupBox("Insertar Contenido")
        layout_ins = QVBoxLayout()

        # Insertar PDF en posición
        h_ins_pdf = QHBoxLayout()
        self.txt_insert_pdf = QLineEdit()
        self.txt_insert_pdf.setPlaceholderText("Ruta del PDF a insertar...")
        btn_browse_pdf = QPushButton("Examinar PDF...")
        btn_browse_pdf.clicked.connect(self.browse_insert_pdf)
        self.combo_ins_pos = QComboBox()
        self.combo_ins_pos.addItems(["Al final", "Al principio", "Después de página..."])
        self.spin_ins_page = QSpinBox()
        self.spin_ins_page.setValue(1)

        h_ins_pdf.addWidget(self.txt_insert_pdf)
        h_ins_pdf.addWidget(btn_browse_pdf)
        h_ins_pdf.addWidget(self.combo_ins_pos)
        h_ins_pdf.addWidget(self.spin_ins_page)
        btn_run_ins_pdf = QPushButton("Insertar PDF")
        btn_run_ins_pdf.clicked.connect(self.run_insert_pdf)
        h_ins_pdf.addWidget(btn_run_ins_pdf)
        layout_ins.addLayout(h_ins_pdf)

        box_insert.setLayout(layout_ins)
        layout.addWidget(box_insert)

        # Group 3: Ajuste de Márgenes
        box_margins = QGroupBox("Ajuste de Márgenes para Encuadernación")
        h_margins = QHBoxLayout()
        h_margins.addWidget(QLabel("Impares (mm):"))
        self.spin_m_odd = QDoubleSpinBox()
        self.spin_m_odd.setRange(-50.0, 50.0)
        h_margins.addWidget(self.spin_m_odd)

        h_margins.addWidget(QLabel("Pares (mm):"))
        self.spin_m_even = QDoubleSpinBox()
        self.spin_m_even.setRange(-50.0, 50.0)
        h_margins.addWidget(self.spin_m_even)

        btn_apply_margins = QPushButton("Aplicar Márgenes")
        btn_apply_margins.clicked.connect(self.run_margins)
        h_margins.addWidget(btn_apply_margins)
        box_margins.setLayout(h_margins)
        layout.addWidget(box_margins)

        layout.addStretch()

    def update_spin_bounds(self):
        total = self.session.get_total_pages() if self.session.is_loaded() else 1
        total = max(1, total)
        self.spin_ext_start.setRange(1, total)
        self.spin_ext_end.setRange(1, total)
        self.spin_ext_end.setValue(total)
        self.spin_ins_page.setRange(1, total)

    def browse_insert_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF a insertar", "", "PDF (*.pdf)")
        if path:
            self.txt_insert_pdf.setText(path)

    def run_extract(self):
        if not self.session.is_loaded():
            return
        try:
            s, e = self.spin_ext_start.value(), self.spin_ext_end.value()
            self.session.extract_page_range(s, e)
            QMessageBox.information(self, "Éxito", f"Rango extraído. Páginas actuales: {self.session.get_total_pages()}")
            if self.on_session_updated:
                self.on_session_updated()
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def run_delete(self):
        if not self.session.is_loaded():
            return
        raw = self.txt_del_pages.text().strip()
        if not raw:
            return
        try:
            pages_to_del = parse_page_selection(raw, self.session.get_total_pages())
            self.session.delete_pages(pages_to_del)
            self.txt_del_pages.clear()
            QMessageBox.information(self, "Éxito", f"Páginas eliminadas. Restantes: {self.session.get_total_pages()}")
            if self.on_session_updated:
                self.on_session_updated()
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Error al borrar páginas:\n{ex}")

    def run_insert_pdf(self):
        if not self.session.is_loaded():
            return
        p_str = self.txt_insert_pdf.text().strip()
        if not p_str:
            return
        pdf_path = Path(p_str)
        if not pdf_path.exists():
            QMessageBox.critical(self, "Error", "El archivo PDF a insertar no existe.")
            return

        idx = self.combo_ins_pos.currentIndex()
        pos = "end" if idx == 0 else ("start" if idx == 1 else "after_page")
        target_p = self.spin_ins_page.value()

        try:
            self.session.insert_pdf_at(pdf_path, position=pos, page_num=target_p)
            QMessageBox.information(self, "Éxito", f"PDF insertado. Páginas totales: {self.session.get_total_pages()}")
            if self.on_session_updated:
                self.on_session_updated()
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))

    def run_margins(self):
        if not self.session.is_loaded():
            return
        try:
            o = self.spin_m_odd.value()
            e = self.spin_m_even.value()
            self.session.adjust_margins(o, e)
            QMessageBox.information(self, "Éxito", "Márgenes ajustados correctamente.")
            if self.on_session_updated:
                self.on_session_updated()
        except Exception as ex:
            QMessageBox.critical(self, "Error", str(ex))