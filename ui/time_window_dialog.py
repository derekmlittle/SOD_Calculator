"""
Time window dialog.

Lets the user choose the regression window for one imported file.
"""

import matplotlib.dates as mdates
import pandas as pd

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QHBoxLayout,
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from services.dataframe_service import prepare_dataframe
from utils.date_utils import parse_time_text


class TimeWindowDialog(QDialog):
    def __init__(self, record, parent=None, default_start=None, default_end=None):
        super().__init__(parent)

        self.record = record
        self.default_start = default_start
        self.default_end = default_end

        self.setWindowTitle(f"Select Time Window - {record.file_name}")
        self.resize(1000, 700)

        self.df = prepare_dataframe(record.dataframe, record.column_mapping)
        self.odo_col = "ODO MG/L"

        self.selected_start = None
        self.selected_end = None
        self.pick_mode = None

        self.fig = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)

        self.start_edit = QLineEdit()
        self.end_edit = QLineEdit()
        self.status = QLabel(
            "Click Pick Start / Pick End, then click the plot, or type timestamps directly."
        )
        self.info = QLabel(
            "Timestamp examples: 2026-07-13 17:45:00 or 7/13/2026 5:45:00 PM"
        )

        self.btn_pick_start = QPushButton("Pick Start")
        self.btn_pick_end = QPushButton("Pick End")
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")

        self.btn_pick_start.clicked.connect(lambda: self.set_pick_mode("start"))
        self.btn_pick_end.clicked.connect(lambda: self.set_pick_mode("end"))
        self.btn_ok.clicked.connect(self.accept_window)
        self.btn_cancel.clicked.connect(self.reject)

        self.build_ui()
        self.canvas.mpl_connect("button_press_event", self.on_click)

        self.load_defaults()
        self.plot_data()

    def build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

        form = QFormLayout()
        form.addRow("Start Time:", self.start_edit)
        form.addRow("End Time:", self.end_edit)
        layout.addLayout(form)

        layout.addWidget(self.info)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_pick_start)
        btn_row.addWidget(self.btn_pick_end)
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_cancel)
        layout.addLayout(btn_row)

        layout.addWidget(self.status)

    def load_defaults(self):
        if self.default_start is not None:
            self.start_edit.setText(
                pd.to_datetime(self.default_start).strftime("%Y-%m-%d %H:%M:%S")
            )
        if self.default_end is not None:
            self.end_edit.setText(
                pd.to_datetime(self.default_end).strftime("%Y-%m-%d %H:%M:%S")
            )

    def set_pick_mode(self, mode):
        self.pick_mode = mode
        self.status.setText(f"Pick {mode} by clicking on the plot.")

    def _parse_time_text(self, text):
        return parse_time_text(text)

    def _snap_to_closest_timestamp(self, target_dt):
        if target_dt is None:
            return None

        d = self.df.dropna(subset=["_datetime"]).copy()
        if d.empty:
            return None

        idx = (d["_datetime"] - target_dt).abs().idxmin()
        return d.loc[idx, "_datetime"]

    def plot_data(self):
        self.ax.clear()

        if "_datetime" not in self.df.columns or self.odo_col not in self.df.columns:
            self.ax.text(
                0.5,
                0.5,
                "Missing time or ODO column",
                transform=self.ax.transAxes,
                ha="center",
                va="center",
            )
            self.canvas.draw()
            return

        d = self.df.dropna(subset=["_datetime", self.odo_col]).copy()
        d = d.sort_values("_datetime")

        if d.empty:
            self.ax.text(
                0.5,
                0.5,
                "No valid data to display",
                transform=self.ax.transAxes,
                ha="center",
                va="center",
            )
            self.canvas.draw()
            return

        self.ax.plot(d["_datetime"], d[self.odo_col], marker="o", linestyle="-", alpha=0.8)

        start_dt = self._parse_time_text(self.start_edit.text())
        end_dt = self._parse_time_text(self.end_edit.text())

        if start_dt is not None:
            self.ax.axvline(start_dt, color="green", linestyle="--", linewidth=2, label="Start")
        if end_dt is not None:
            self.ax.axvline(end_dt, color="red", linestyle="--", linewidth=2, label="End")
        if start_dt is not None and end_dt is not None and start_dt < end_dt:
            self.ax.axvspan(start_dt, end_dt, color="yellow", alpha=0.2)

        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("ODO MG/L")
        self.ax.set_title("Select regression window")
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d/%Y %H:%M:%S"))
        self.fig.autofmt_xdate()
        self.ax.legend(loc="best")
        self.canvas.draw()

    def on_click(self, event):
        if event.inaxes != self.ax or event.xdata is None:
            return

        clicked_dt = mdates.num2date(event.xdata).replace(tzinfo=None)

        if self.pick_mode == "start":
            self.start_edit.setText(clicked_dt.strftime("%Y-%m-%d %H:%M:%S"))
            self.pick_mode = None
            self.status.setText("Start selected.")
            self.plot_data()
        elif self.pick_mode == "end":
            self.end_edit.setText(clicked_dt.strftime("%Y-%m-%d %H:%M:%S"))
            self.pick_mode = None
            self.status.setText("End selected.")
            self.plot_data()

    def accept_window(self):
        start_dt = self._parse_time_text(self.start_edit.text())
        end_dt = self._parse_time_text(self.end_edit.text())

        if self.start_edit.text().strip() and start_dt is None:
            QMessageBox.warning(self, "Invalid Start", "Could not parse start time.")
            return
        if self.end_edit.text().strip() and end_dt is None:
            QMessageBox.warning(self, "Invalid End", "Could not parse end time.")
            return
        if start_dt is not None and end_dt is not None and start_dt >= end_dt:
            QMessageBox.warning(self, "Invalid Window", "Start time must be earlier than end time.")
            return

        self.selected_start = self._snap_to_closest_timestamp(start_dt) if start_dt is not None else None
        self.selected_end = self._snap_to_closest_timestamp(end_dt) if end_dt is not None else None
        self.accept()