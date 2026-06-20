"""PySide6 drag-and-drop interface for Inkscape PNG-to-SVG export."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from src.output.export_manager import SUPPORTED_EXTENSIONS, export_batch
from src.processing.inkscape import is_inkscape_available


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.files: list[Path] = []
        self.setWindowTitle("Imagen a SVG local")
        self.setAcceptDrops(True)
        self.resize(900, 600)

        self.queue = QListWidget()
        self.queue.currentRowChanged.connect(self._update_preview)
        self.before = QLabel("Arrastra PNG aquí")
        self.after = QLabel("Exportación directa con Inkscape")
        for label in (self.before, self.after):
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumSize(320, 260)
            label.setStyleSheet("border: 1px dashed #888; padding: 12px;")

        self.inkscape_available = is_inkscape_available()
        self.status_label = QLabel(
            "Inkscape disponible: exportación PNG → SVG plain"
            if self.inkscape_available
            else "Inkscape no está disponible: instala Inkscape o añádelo al PATH"
        )
        self.progress = QProgressBar()

        add_button = QPushButton("Añadir imágenes")
        add_button.clicked.connect(self._choose_files)
        process_button = QPushButton("Procesar lote")
        process_button.clicked.connect(self._process_batch)

        controls = QHBoxLayout()
        controls.addWidget(self.status_label)
        controls.addWidget(add_button)
        controls.addWidget(process_button)

        previews = QHBoxLayout()
        previews.addWidget(self.before)
        previews.addWidget(self.after)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self.queue)
        layout.addLayout(previews)
        layout.addWidget(self.progress)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

    def dragEnterEvent(self, event):  # noqa: N802 - Qt API name
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):  # noqa: N802 - Qt API name
        self._add_files([Path(url.toLocalFile()) for url in event.mimeData().urls()])

    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imágenes", "input", "PNG (*.png)"
        )
        self._add_files([Path(path) for path in paths])

    def _add_files(self, paths: list[Path]) -> None:
        for path in paths:
            if path.suffix.lower() in SUPPORTED_EXTENSIONS and path not in self.files:
                self.files.append(path)
                self.queue.addItem(str(path))
        if self.files and self.queue.currentRow() < 0:
            self.queue.setCurrentRow(0)

    def _update_preview(self) -> None:
        row = self.queue.currentRow()
        if row < 0 or row >= len(self.files):
            return
        source = self.files[row]
        self.before.setPixmap(
            QPixmap(str(source)).scaled(
                self.before.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.after.setPixmap(
            QPixmap(str(source)).scaled(
                self.after.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

    def _process_batch(self) -> None:
        if not self.files:
            QMessageBox.information(self, "Sin imágenes", "Añade al menos un PNG.")
            return
        if not self.inkscape_available:
            QMessageBox.critical(
                self,
                "Inkscape requerido",
                "Instala Inkscape o añade su ejecutable al PATH para exportar SVG plain.",
            )
            return

        output_dir = (
            QFileDialog.getExistingDirectory(self, "Elegir carpeta de salida", "output")
            or "output"
        )
        self.progress.setMaximum(len(self.files))
        results = []
        try:
            for index, path in enumerate(self.files, start=1):
                results.extend(export_batch([path], output_dir))
                self.progress.setValue(index)
        except RuntimeError as error:
            QMessageBox.critical(self, "Error de Inkscape", str(error))
            return
        QMessageBox.information(
            self, "Listo", f"Exportados {len(results)} SVG plain en {output_dir}."
        )
