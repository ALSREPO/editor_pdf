"""
gui/views/index_view.py - Vista para insertar índices desde archivo TXT.
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QPushButton, QFileDialog, QRadioButton, QLabel, QMessageBox
)
from pdf_ops import PDFEditorSession


class IndexView(QWidget):
    def __init__(self, session: PDFEditorSession, on_session_updated=None):
        super().__init__()
        self.session = session
        self.on_session_updated = on_session_updated
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Selección de Archivo TXT
        box_file = QGroupBox("Archivo de Índice (.txt)")
        file_layout = QHBoxLayout()

        self.txt_path = QLineEdit()
        self.txt_path.setPlaceholderText("Selecciona el archivo .txt con el índice...")
        file_layout.addWidget(self.txt_path)

        btn_browse = QPushButton("Examinar...")
        btn_browse.clicked.connect(self.browse_txt)
        file_layout.addWidget(btn_browse)

        box_file.setLayout(file_layout)
        layout.addWidget(box_file)

        # 2. Posición de Inserción
        box_pos = QGroupBox("Posición de inserción del índice")
        pos_layout = QVBoxLayout()
        self.radio_pos_end = QRadioButton("Al final del documento")
        self.radio_pos_end.setChecked(True)
        self.radio_pos_front = QRadioButton("Tras las páginas de portada (después de la página 4)")
        self.radio_pos_start = QRadioButton("Al principio del documento (Página 1)")

        pos_layout.addWidget(self.radio_pos_end)
        pos_layout.addWidget(self.radio_pos_front)
        pos_layout.addWidget(self.radio_pos_start)
        box_pos.setLayout(pos_layout)
        layout.addWidget(box_pos)

        # 3. Márgenes de la primera página
        box_margin = QGroupBox("Disposición de márgenes de la 1ª página del índice")
        margin_layout = QVBoxLayout()
        self.radio_m_odd = QRadioButton("Página Impar (Lomo a la izquierda: 1.8cm izq / 1.2cm der)")
        self.radio_m_odd.setChecked(True)
        self.radio_m_even = QRadioButton("Página Par (Lomo a la derecha: 1.2cm izq / 1.8cm der)")
        self.radio_m_center = QRadioButton("Centrado (Márgenes iguales: 1.5cm izq / 1.5cm der)")

        margin_layout.addWidget(self.radio_m_odd)
        margin_layout.addWidget(self.radio_m_even)
        margin_layout.addWidget(self.radio_m_center)
        box_margin.setLayout(margin_layout)
        layout.addWidget(box_margin)

        # 4. Botón de Inserción
        btn_insert = QPushButton("Generar e Insertar Índice")
        btn_insert.setFixedHeight(40)
        btn_insert.clicked.connect(self.run_insert_index)
        layout.addWidget(btn_insert)

        layout.addStretch()

    def browse_txt(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo de índice", "", "Archivos de texto (*.txt)")
        if path:
            self.txt_path.setText(path)

    def run_insert_index(self):
        if not self.session.is_loaded():
            QMessageBox.warning(self, "Atención", "Primero debes cargar un PDF base.")
            return

        txt_str = self.txt_path.text().strip()
        if not txt_str:
            QMessageBox.warning(self, "Atención", "Debes seleccionar un archivo .txt de índice.")
            return

        txt_path = Path(txt_str)
        if not txt_path.exists() or not txt_path.is_file():
            QMessageBox.critical(self, "Error", f"No existe el archivo especificado:\n{txt_path}")
            return

        # Determinar posición
        if self.radio_pos_front.isChecked():
            pos = "after_front_matter"
        elif self.radio_pos_start.isChecked():
            pos = "at_start"
        else:
            pos = "at_end"

        # Determinar modo de margen
        if self.radio_m_even.isChecked():
            margin_mode = "even"
        elif self.radio_m_center.isChecked():
            margin_mode = "centered"
        else:
            margin_mode = "odd"

        try:
            self.session.insert_index_from_txt(txt_path, position=pos, margin_mode=margin_mode)
            QMessageBox.information(self, "Éxito", "✓ Índice maquetado e insertado correctamente.")
            if self.on_session_updated:
                self.on_session_updated()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar e insertar el índice:\n{e}")