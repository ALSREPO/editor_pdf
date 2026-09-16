"""
gui/views/booklet_view.py - Vista para imposición de cuadernillos en PySide6.
"""

import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
    QSpinBox, QLineEdit, QPushButton, QLabel, QMessageBox, QTextEdit
)
from pdf_ops import PDFEditorSession


class BookletView(QWidget):
    def __init__(self, session: PDFEditorSession, on_session_updated=None):
        super().__init__()
        self.session = session
        self.on_session_updated = on_session_updated
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 1. Configuración de Imposición
        box_config = QGroupBox("Configuración de Cuadernillos (Booklet Imposition)")
        config_layout = QVBoxLayout()

        self.radio_fixed = QRadioButton("Tamaño fijo por cuadernillo")
        self.radio_fixed.setChecked(True)
        self.radio_fixed.toggled.connect(self.toggle_mode)
        config_layout.addWidget(self.radio_fixed)

        # Opción Fija: SpinBox para hojas
        fixed_layout = QHBoxLayout()
        fixed_layout.setContentsMargins(20, 0, 0, 0)
        fixed_layout.addWidget(QLabel("Hojas por cuadernillo:"))
        self.spin_sheets = QSpinBox()
        self.spin_sheets.setRange(1, 100)
        self.spin_sheets.setValue(7)
        self.spin_sheets.valueChanged.connect(self.update_summary)
        fixed_layout.addWidget(self.spin_sheets)
        fixed_layout.addStretch()
        config_layout.addLayout(fixed_layout)

        self.radio_custom = QRadioButton("Lista personalizada por cuadernillo (ej. Excel)")
        config_layout.addWidget(self.radio_custom)

        # Opción Personalizada: LineEdit
        custom_layout = QHBoxLayout()
        custom_layout.setContentsMargins(20, 0, 0, 0)
        custom_layout.addWidget(QLabel("Secuencia de hojas (ej. 7,7,7,7,7,6,7,7,7,7,7):"))
        self.txt_custom = QLineEdit()
        self.txt_custom.setPlaceholderText("7, 7, 7, 7, 7, 6, 7, 7, 7, 7, 7")
        self.txt_custom.setEnabled(False)
        self.txt_custom.textChanged.connect(self.update_summary)
        custom_layout.addWidget(self.txt_custom)
        config_layout.addLayout(custom_layout)

        box_config.setLayout(config_layout)
        layout.addWidget(box_config)

        # 2. Resumen informativo
        box_summary = QGroupBox("Resumen de Imposición")
        summary_layout = QVBoxLayout()
        self.lbl_summary = QLabel("Cargue un archivo PDF para ver el resumen de imposición.")
        self.lbl_summary.setWordWrap(True)
        summary_layout.addWidget(self.lbl_summary)
        box_summary.setLayout(summary_layout)
        layout.addWidget(box_summary)

        # 3. Botón de Acción
        self.btn_impose = QPushButton("Ejecutar Imposición de Cuadernillos")
        self.btn_impose.setFixedHeight(40)
        self.btn_impose.clicked.connect(self.run_imposition)
        layout.addWidget(self.btn_impose)

        layout.addStretch()

    def toggle_mode(self):
        is_fixed = self.radio_fixed.isChecked()
        self.spin_sheets.setEnabled(is_fixed)
        self.txt_custom.setEnabled(not is_fixed)
        self.update_summary()

    def get_sheets_list(self) -> list[int]:
        if not self.session.is_loaded():
            return []

        total_pages = self.session.get_total_pages()
        if total_pages == 0:
            return []

        if self.radio_fixed.isChecked():
            h = self.spin_sheets.value()
            total_needed = math.ceil(total_pages / (h * 4))
            return [h] * total_needed
        else:
            raw = self.txt_custom.text().strip()
            if not raw:
                return []
            try:
                return [int(x.strip()) for x in raw.split(",") if x.strip()]
            except ValueError:
                return []

    def update_summary(self):
        if not self.session.is_loaded():
            self.lbl_summary.setText("⚠ No hay ningún PDF cargado en la sesión.")
            self.btn_impose.setEnabled(False)
            return

        total_p = self.session.get_total_pages()
        sheets_list = self.get_sheets_list()

        if not sheets_list:
            self.lbl_summary.setText("⚠ Especifica una secuencia de hojas válida.")
            self.btn_impose.setEnabled(False)
            return

        total_covered = sum(s * 4 for s in sheets_list)
        blank_added = max(0, total_covered - total_p)

        text = (
            f"• Páginas actuales del documento: <b>{total_p}</b><br/>"
            f"• Cuadernillos a generar: <b>{len(sheets_list)}</b><br/>"
            f"• Páginas totales de folleto que cubrirá: <b>{total_covered}</b><br/>"
        )
        if blank_added > 0:
            text += f"• <font color='orange'>Se añadirán <b>{blank_added}</b> página(s) en blanco al final para completar el último cuadernillo.</font><br/>"
        text += "<br/><b>Instrucciones de impresión:</b> Imprimir a doble cara por el <b>borde corto</b> (*Flip on short edge*)."

        self.lbl_summary.setText(text)
        self.btn_impose.setEnabled(True)

    def run_imposition(self):
        sheets_list = self.get_sheets_list()
        if not sheets_list:
            QMessageBox.warning(self, "Error", "La lista de cuadernillos introducida no es válida.")
            return

        try:
            self.session.impose_booklet(sheets_list)
            QMessageBox.information(
                self, "Éxito",
                "✓ Imposición realizada con éxito.\n"
                "El documento resultante está preparado para imprimirse directamente a doble cara por el borde corto."
            )
            if self.on_session_updated:
                self.on_session_updated()
        except Exception as e:
            QMessageBox.critical(self, "Error de Imposición", f"No se pudo completar la imposición:\n{e}")