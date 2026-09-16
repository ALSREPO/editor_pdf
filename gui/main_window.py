"""
gui/main_window.py - Ventana principal en PySide6.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QFileDialog, QTabWidget, QMessageBox, QStatusBar
)
from PySide6.QtCore import Qt
from pdf_ops import PDFEditorSession

from gui.views.booklet_view import BookletView
from gui.views.index_view import IndexView
from gui.views.pages_view import PagesView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.session = PDFEditorSession()
        self.setWindowTitle("Editor Modular de PDF (Edición e Imposición)")
        self.resize(900, 650)

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 1. Barra de Control de Archivo Base
        top_bar = QHBoxLayout()

        self.btn_load = QPushButton("📂 Cargar PDF")
        self.btn_load.setFixedHeight(35)
        self.btn_load.clicked.connect(self.load_pdf_file)
        top_bar.addWidget(self.btn_load)

        self.btn_merge = QPushButton("🧩 Unir Varios PDFs...")
        self.btn_merge.setFixedHeight(35)
        self.btn_merge.clicked.connect(self.merge_pdf_files)
        top_bar.addWidget(self.btn_merge)

        self.btn_save = QPushButton("💾 Guardar PDF")
        self.btn_save.setFixedHeight(35)
        self.btn_save.clicked.connect(self.save_pdf_file)
        top_bar.addWidget(self.btn_save)

        main_layout.addLayout(top_bar)

        # 2. Banner de Estado del PDF Activo
        self.lbl_status = QLabel("Documento Activo: Ninguno seleccionado")
        self.lbl_status.setStyleSheet("font-weight: bold; font-size: 13px; padding: 6px; background-color: #e9ecef; border-radius: 4px;")
        main_layout.addWidget(self.lbl_status)

        # 3. Contenedor de Pestañas
        self.tabs = QTabWidget()

        # Instanciar Vistas
        self.view_booklet = BookletView(self.session, on_session_updated=self.refresh_ui)
        self.view_index = IndexView(self.session, on_session_updated=self.refresh_ui)
        self.view_pages = PagesView(self.session, on_session_updated=self.refresh_ui)

        self.tabs.addTab(self.view_booklet, "📖 Imposición de Cuadernillos")
        self.tabs.addTab(self.view_index, "📑 Generar e Insertar Índice")
        self.tabs.addTab(self.view_pages, "🛠 Edición de Páginas y Márgenes")

        main_layout.addWidget(self.tabs)

        # Barra de Estado
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Listo.")

    def refresh_ui(self):
        if self.session.is_loaded():
            name = self.session.original_name
            total = self.session.get_total_pages()
            unsaved = " *" if self.session.has_unsaved_changes else ""
            self.lbl_status.setText(f"Documento Activo: {name}.pdf | {total} página(s){unsaved}")
        else:
            self.lbl_status.setText("Documento Activo: Ninguno seleccionado")

        # Notificar a las sub-vistas para refrescar rangos
        self.view_booklet.update_summary()
        self.view_pages.update_spin_bounds()

    def load_pdf_file(self):
        if self.session.has_unsaved_changes:
            ans = QMessageBox.question(
                self, "Cambios sin guardar",
                "Tienes cambios sin guardar en la sesión actual. ¿Deseas descartarlos?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ans != QMessageBox.Yes:
                return

        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo PDF", "", "Archivos PDF (*.pdf)")
        if path:
            if self.session.load_pdf(Path(path)):
                self.statusBar.showMessage(f"Cargado: {Path(path).name}", 5000)
                self.refresh_ui()
            else:
                QMessageBox.critical(self, "Error", "El archivo seleccionado no es un PDF válido.")

    def merge_pdf_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Seleccionar PDFs a unir", "", "Archivos PDF (*.pdf)")
        if paths:
            pdf_list = [Path(p) for p in paths]
            try:
                self.session.merge_pdfs(pdf_list)
                self.refresh_ui()
                QMessageBox.information(self, "Éxito", f"Se han unido {len(pdf_list)} archivos correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error de Unión", f"Ocurrió un error al unir los archivos:\n{e}")

    def save_pdf_file(self):
        if not self.session.is_loaded():
            QMessageBox.warning(self, "Atención", "No hay ningún PDF cargado en memoria para guardar.")
            return

        default_path = str(self.session.original_path) if self.session.original_path else "documento_editado.pdf"
        out_path_str, _ = QFileDialog.getSaveFileName(self, "Guardar PDF final", default_default_path if 'default_default_path' in locals() else default_path, "PDF Files (*.pdf)")

        if out_path_str:
            out_path = Path(out_path_str)
            try:
                overwrite = (self.session.original_path and out_path.resolve() == self.session.original_path.resolve())
                self.session.save_to_disk(out_path, overwrite=overwrite)
                self.refresh_ui()
                QMessageBox.information(self, "Éxito", f"✓ Archivo guardado correctamente en:\n{out_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error al guardar", f"No se pudo guardar el archivo:\n{e}")

    def closeEvent(self, event):
        if self.session.has_unsaved_changes:
            ans = QMessageBox.question(
                self, "Salir",
                "Tienes cambios sin guardar. ¿Seguro que deseas salir?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ans == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()