"""
Main window.

This is the UI controller for the app.
It handles file import, result calculation, and exporting.
"""

import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import TARGET_FIELDS, CHAMBER_TYPES, CHAMBER_IDS
from models.file_record import FileRecord
from services.calculation_service import (
    apply_blank_adjustment_and_convert,
    compute_chamber_result,
    results_to_dataframe,
    summarize_site,
)
from services.plot_service import plot_site_results
from services.report_service import build_word_report
from storage.column_mapper import ColumnMapper
from storage.import_profile import ImportProfileStore
from ui.help_dialog import HelpDialog
from ui.import_dialog import ImportDialog
from ui.time_window_dialog import TimeWindowDialog
from utils.filename import infer_chamber_id_from_filename, make_safe_filename


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SOD Calculator")
        self.resize(1500, 950)

        self.mapper = ColumnMapper(TARGET_FIELDS)
        self.import_profile_helper = ImportProfileStore()

        self.records = []
        self.current_results = []
        self.current_blank_mean = float("nan")
        self.current_site_summary = {}

        self.project_number = QLineEdit()
        self.project_name = QLineEdit()
        self.theta = QLineEdit("1.065")
        self.v_over_a = QLineEdit("240")

        self.file_list = QTableWidget(0, 6)
        self.file_list.setHorizontalHeaderLabels(
            ["File", "Site", "Chamber Type", "Chamber ID", "Rows Skipped", "Encoding"]
        )
        self.file_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.file_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.file_list.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.SelectedClicked
            | QTableWidget.EditTrigger.EditKeyPressed
        )
        self.file_list.itemChanged.connect(self.update_site_name)

        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)

        self.setup_ui()

    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)

        form = QFormLayout()
        form.addRow("Project Number:", self.project_number)
        form.addRow("Project Name:", self.project_name)
        form.addRow("Theta:", self.theta)
        form.addRow("V/A (L/m²):", self.v_over_a)
        layout.addLayout(form)

        btn_row = QHBoxLayout()

        add_btn = QPushButton("Add CSV")
        add_btn.clicked.connect(self.add_csv)

        remove_btn = QPushButton("Remove Selected CSV")
        remove_btn.clicked.connect(self.remove_selected_csv)

        compute_btn = QPushButton("Compute Results")
        compute_btn.clicked.connect(self.compute_results)

        export_btn = QPushButton("Export Results")
        export_btn.clicked.connect(self.export_all_results)

        help_btn = QPushButton("How to Use This App")
        help_btn.clicked.connect(self.show_help_dialog)

        for btn in (add_btn, remove_btn, compute_btn, export_btn, help_btn):
            btn_row.addWidget(btn)

        layout.addLayout(btn_row)
        layout.addWidget(QLabel("Current Site Batch"))
        layout.addWidget(self.file_list)
        layout.addWidget(self.results_text)

        self.setCentralWidget(central)

    def show_help_dialog(self):
        HelpDialog(self).exec()

    def update_site_name(self, item):
        if item.column() == 1 and 0 <= item.row() < len(self.records):
            self.records[item.row()].site_name = item.text().strip()

    def update_chamber_type(self, idx, text):
        if 0 <= idx < len(self.records):
            self.records[idx].chamber_type = text

    def update_chamber_id(self, idx, text):
        if 0 <= idx < len(self.records):
            self.records[idx].chamber_id = text

    def add_csv(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select CSV Files",
            "",
            "CSV Files (*.csv *.txt);All Files (*)",
        )
        if not paths:
            return

        for path in paths:
            try:
                dlg = ImportDialog(path, self.mapper, self.import_profile_helper, self)
                if dlg.exec() == QDialog.DialogCode.Accepted:
                    record = FileRecord(
                        path=path,
                        encoding=dlg.encoding,
                        skiprows=dlg.skiprows,
                        dataframe=dlg.df.copy(),
                        column_mapping=dlg.column_mapping,
                        chamber_type=dlg.chamber_combo.currentText(),
                        chamber_id=infer_chamber_id_from_filename(path),
                        site_name=dlg.site_edit.text().strip(),
                        file_name=os.path.basename(path),
                    )
                    self.records.append(record)
            except Exception as exc:
                QMessageBox.warning(self, "Import Error", f"{os.path.basename(path)}:\n{exc}")

        self.refresh_file_list()

    def remove_selected_csv(self):
        selected_rows = sorted(
            {idx.row() for idx in self.file_list.selectionModel().selectedRows()},
            reverse=True,
        )
        if not selected_rows:
            QMessageBox.information(self, "Remove CSV", "Please select one or more rows to remove.")
            return

        for row in selected_rows:
            if 0 <= row < len(self.records):
                del self.records[row]

        self.refresh_file_list()

    def refresh_file_list(self):
        self.file_list.blockSignals(True)
        self.file_list.setRowCount(len(self.records))

        for i, rec in enumerate(self.records):
            self.file_list.setItem(i, 0, QTableWidgetItem(rec.file_name))

            site_item = QTableWidgetItem(rec.site_name)
            site_item.setFlags(site_item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.file_list.setItem(i, 1, site_item)

            chamber_combo = QComboBox()
            chamber_combo.addItems(CHAMBER_TYPES)
            chamber_combo.setCurrentText(rec.chamber_type)
            chamber_combo.currentTextChanged.connect(
                lambda text, idx=i: self.update_chamber_type(idx, text)
            )
            self.file_list.setCellWidget(i, 2, chamber_combo)

            chamber_id_combo = QComboBox()
            chamber_id_combo.addItems(CHAMBER_IDS)
            if rec.chamber_id in CHAMBER_IDS:
                chamber_id_combo.setCurrentText(rec.chamber_id)
            else:
                chamber_id_combo.setCurrentIndex(-1)
            chamber_id_combo.currentTextChanged.connect(
                lambda text, idx=i: self.update_chamber_id(idx, text)
            )
            self.file_list.setCellWidget(i, 3, chamber_id_combo)

            self.file_list.setItem(i, 4, QTableWidgetItem(str(rec.skiprows)))
            self.file_list.setItem(i, 5, QTableWidgetItem(str(rec.encoding or "")))

        self.file_list.blockSignals(False)
        self.file_list.resizeColumnsToContents()
        self.file_list.setColumnWidth(0, max(self.file_list.columnWidth(0), 350))

    def compute_results(self):
        if not self.records:
            QMessageBox.information(self, "No Data", "Please add one or more CSV files first.")
            return

        try:
            theta = float(self.theta.text())
            v_over_a = float(self.v_over_a.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Theta and V/A must be numeric.")
            return

        self.current_results = []
        self.current_blank_mean = float("nan")
        self.current_site_summary = {}
        self.results_text.clear()

        default_start = None
        default_end = None

        for rec in self.records:
            try:
                dlg = TimeWindowDialog(
                    rec,
                    self,
                    default_start=default_start,
                    default_end=default_end,
                )
                if dlg.exec() != QDialog.DialogCode.Accepted:
                    continue

                if default_start is None and dlg.selected_start is not None:
                    default_start = dlg.selected_start
                if default_end is None and dlg.selected_end is not None:
                    default_end = dlg.selected_end

                result = compute_chamber_result(
                    rec,
                    start_dt=dlg.selected_start,
                    end_dt=dlg.selected_end,
                )
                self.current_results.append(result)

            except Exception as exc:
                QMessageBox.warning(self, "Computation Error", f"{rec.file_name}:\n{exc}")

        if not self.current_results:
            self.results_text.append("No results computed.")
            return

        self.current_blank_mean = apply_blank_adjustment_and_convert(
            self.current_results,
            theta=theta,
            v_over_a=v_over_a,
        )
        self.current_site_summary = summarize_site(self.current_results)

        self.results_text.append(f"Computed {len(self.current_results)} files")
        self.results_text.append(f"Blank mean slope: {self.current_blank_mean:.6f} mg/L/min")
        self.results_text.append("")
        self.results_text.append("Site Summary:")
        self.results_text.append(f"  Mean SOD: {self.current_site_summary['mean_sod_g_m2_day']:.6f} g/m²/day")
        self.results_text.append(f"  Mean Temp: {self.current_site_summary['average_temp_c']:.2f} °C")
        self.results_text.append(f"  Mean SOD corrected to 20°C: {self.current_site_summary['mean_sod_20c_g_m2_day']:.6f} g/m²/day")
        self.results_text.append(f"  Mean R²: {self.current_site_summary['mean_r2']:.6f}")
        self.results_text.append("")
        self.results_text.append("Per-Chamber Results:")

        for r in self.current_results:
            self.results_text.append(
                f"{r.record.file_name} | {r.record.chamber_type} | "
                f"Chamber ID={r.record.chamber_id} | "
                f"Slope={r.slope:.6f} | Adj={r.adjusted_do_rate:.6f} | "
                f"SOD={r.sod_g_m2_day:.6f} g/m²/day | R²={r.r2:.4f}"
            )

    def get_results_output_dir(self):
        if not self.records:
            return None

        first_path = self.records[0].path
        if not first_path:
            return None

        base_dir = os.path.dirname(first_path)
        if not base_dir:
            return None

        out_dir = os.path.join(base_dir, "Calculation Results")
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def export_all_results(self):
        if not self.current_results:
            QMessageBox.information(self, "No Results", "Compute results before exporting.")
            return

        try:
            theta = float(self.theta.text())
            v_over_a = float(self.v_over_a.text())
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Theta and V/A must be numeric.")
            return

        out_dir = self.get_results_output_dir()
        if not out_dir:
            QMessageBox.warning(self, "No Import Folder", "Could not determine the import folder.")
            return

        project_number = self.project_number.text().strip() or "Project"
        project_name = self.project_name.text().strip() or "SOD"

        summary_path = os.path.join(
            out_dir,
            make_safe_filename(f"{project_number}_{project_name}_SOD_summary.csv"),
        )
        plot_path = os.path.join(
            out_dir,
            make_safe_filename(f"{project_number}_{project_name}_SOD_plot.png"),
        )
        report_path = os.path.join(
            out_dir,
            make_safe_filename(f"{project_number}_{project_name}_SOD_Report.docx"),
        )

        try:
            df = results_to_dataframe(
                self.current_results,
                project_number,
                project_name,
                self.current_blank_mean,
                self.current_site_summary,
                theta,
                v_over_a,
            )
            df.to_csv(summary_path, index=False)

            fig = plot_site_results(
                self.current_results,
                project_number,
                project_name,
                site_summary=self.current_site_summary,
                blank_mean=self.current_blank_mean,
            )
            fig.savefig(plot_path, dpi=300, bbox_inches="tight")
            fig.clf()

            build_word_report(
                report_path,
                project_number,
                project_name,
                self.current_results,
                self.current_blank_mean,
                self.current_site_summary,
                theta,
                v_over_a,
            )
        except ImportError:
            QMessageBox.warning(
                self,
                "Missing Dependency",
                "python-docx is not installed.\n\nInstall it with:\n    pip install python-docx",
            )
            return
        except Exception as exc:
            QMessageBox.warning(self, "Export Error", str(exc))
            return

        QMessageBox.information(
            self,
            "Export Complete",
            "Files saved successfully:\n\n"
            f"Folder: {out_dir}\n"
            f"Summary CSV: {summary_path}\n"
            f"Word Report: {report_path}\n"
            f"Plot: {plot_path}",
        )

    def open_file_default_app(self, path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception:
            pass