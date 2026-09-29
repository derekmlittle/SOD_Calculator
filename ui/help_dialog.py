"""
Help dialog.

Keep user instructions short and clear.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton


HELP_TEXT = """
How to Use This App

1. Enter the Project Number and Project Name.
2. Click Add CSV and select one or more files.
3. In the import window, adjust Rows to skip, confirm the preview, choose the chamber type, and map the columns.
4. After files are added, review the Current Site Batch table.
5. Click Compute Results.
6. For each file, select the regression window by clicking Pick Start / Pick End and then clicking on the plot, or type the timestamps directly.
7. Review the results in the output box.
8. Click Export Results to save the CSV, plot, and Word report.

Tips:
- Make sure ODO MG/L is mapped correctly.
- If the preview looks wrong, change the Rows to skip value.
- Chamber type and chamber ID can be edited in the file list.
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Use This App")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText(HELP_TEXT.strip())
        layout.addWidget(help_text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)