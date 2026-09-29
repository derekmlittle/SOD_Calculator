"""
Import dialog.

Handles:
- rows to skip
- preview
- column mapping
- chamber type
- site name
"""

import os

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QHeaderView,
)

from config import TARGET_FIELDS, CHAMBER_TYPES
from services.csv_importer import read_csv_with_fallback


class ImportDialog(QDialog):
    def __init__(self, path, mapper, profile_helper, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import CSV")
        self.resize(1200, 800)

        self.path = path
        self.mapper = mapper
        self.profile_helper = profile_helper

        self.df = None
        self.encoding = None
        self.sep = ","
        self.skiprows = 8
        self.column_mapping = {}
        self.columns = []
        self.mapping_widgets = {}

        self.file_edit = QLineEdit(os.path.basename(path))
        self.skip_spin = QSpinBox()
        self.chamber_combo = QComboBox()
        self.site_edit = QLineEdit()
        self.profile_edit = QLineEdit()

        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)

        self.skip_spin.setRange(0, 500)
        self.skip_spin.setValue(8)

        self.chamber_combo.addItems(CHAMBER_TYPES)

        self.setup_ui()
        self.load_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.file_edit.setReadOnly(True)

        form = QFormLayout()
        form.addRow("File:", self.file_edit)
        form.addRow("Rows to skip:", self.skip_spin)
        form.addRow("Chamber Type:", self.chamber_combo)
        form.addRow("Site Name:", self.site_edit)
        layout.addLayout(form)

        layout.addWidget(QLabel("Preview"))
        layout.addWidget(self.preview_table)

        mapping_box = QGroupBox("Column Mapping")
        self.mapping_layout = QGridLayout(mapping_box)
        self.mapping_layout.addWidget(QLabel("Target Field"), 0, 0)
        self.mapping_layout.addWidget(QLabel("CSV Column"), 0, 1)
        layout.addWidget(mapping_box)

        btn_row = QHBoxLayout()
        self.btn_accept = QPushButton("Accept")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_accept.clicked.connect(self.accept_dialog)
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_accept)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        self.skip_spin.valueChanged.connect(self.load_preview)

    def load_preview(self):
        try:
            self.skiprows = self.skip_spin.value()
            self.df, self.encoding, self.sep = read_csv_with_fallback(
                self.path,
                skiprows=self.skiprows,
            )
            self.columns = list(self.df.columns)
            self.populate_preview()
            self.populate_mapping()
            self.autofill_site_name()
        except Exception as exc:
            QMessageBox.critical(self, "Import Error", str(exc))

    def populate_preview(self):
        preview_df = self.df.head(10)

        self.preview_table.setRowCount(preview_df.shape[0])
        self.preview_table.setColumnCount(preview_df.shape[1])
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in preview_df.columns])

        for i in range(preview_df.shape[0]):
            for j in range(preview_df.shape[1]):
                self.preview_table.setItem(i, j, QTableWidgetItem(str(preview_df.iat[i, j])))

        self.preview_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            child = item.layout()
            if child is not None:
                self.clear_layout(child)

    def populate_mapping(self):
        self.clear_layout(self.mapping_layout)

        self.mapping_layout.addWidget(QLabel("Target Field"), 0, 0)
        self.mapping_layout.addWidget(QLabel("CSV Column"), 0, 1)

        self.mapping_widgets = {}
        self.column_mapping = self.mapper.get_best_mapping(
            self.columns,
            self.profile_edit.text().strip(),
        )

        for row, target in enumerate(TARGET_FIELDS, start=1):
            self.mapping_layout.addWidget(QLabel(target), row, 0)

            combo = QComboBox()
            combo.addItem("")
            combo.addItems(self.columns)

            mapped_col = self.column_mapping.get(target)
            if mapped_col in self.columns:
                combo.setCurrentText(mapped_col)

            combo.currentTextChanged.connect(
                lambda text, t=target: self.column_mapping.__setitem__(t, text or None)
            )

            self.mapping_layout.addWidget(combo, row, 1)
            self.mapping_widgets[target] = combo

    def autofill_site_name(self):
        if self.site_edit.text().strip():
            return

        site_col = self.column_mapping.get("SITE NAME")
        if not site_col or site_col not in self.df.columns:
            return

        nonempty = self.df[site_col].dropna().astype(str)
        if not nonempty.empty:
            self.site_edit.setText(nonempty.iloc[0].strip())

    def accept_dialog(self):
        self.skiprows = self.skip_spin.value()

        for target, combo in self.mapping_widgets.items():
            self.column_mapping[target] = combo.currentText().strip() or None

        self.accept()