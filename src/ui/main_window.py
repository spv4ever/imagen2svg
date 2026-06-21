"""PySide6 drag-and-drop interface for PNG/JPEG to plain SVG export."""

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
from src.processing.inkscape import InkscapeNotFoundError, find_inkscape


class MainWindow(QMainWindow):
    """Small desktop window that accepts image drops and exports them with Inkscape."""

    def __init__(self) -> None:
        super().__init__()
        self.files: list[Path] = []
        self.setWindowTitle("Imagen a SVG compatible con Fusion 360")
        self.setAcceptDrops(True)
        self.resize(820, 560)

        self.queue = QListWidget()
        self.queue.currentRowChanged.connect(self._update_preview)

        self.preview = QLabel("Arrastra imágenes PNG o JPEG aquí")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(420, 300)
        self.preview.setStyleSheet("border: 1px dashed #888; padding: 12px;")

        inkscape_status = (
            "Inkscape detectado" if find_inkscape() else "Inkscape no detectado"
        )
        self.status_label = QLabel(
            f"{inkscape_status} · SVG plain + segunda pasada compatible con Fusion 360"
        )
        self.progress = QProgressBar()

        add_button = QPushButton("Añadir imágenes")
        add_button.clicked.connect(self._choose_files)
        process_button = QPushButton("Convertir a SVG Fusion 360")
        process_button.clicked.connect(self._process_batch)

        controls = QHBoxLayout()
        controls.addWidget(self.status_label)
        controls.addWidget(add_button)
        controls.addWidget(process_button)

        layout = QVBoxLayout()
        layout.addLayout(controls)
        layout.addWidget(self.queue)
        layout.addWidget(self.preview)
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
            self,
            "Seleccionar imágenes",
            "input",
            "Imágenes (*.png *.jpg *.jpeg)",
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
        self.preview.setPixmap(
            QPixmap(str(source)).scaled(
                self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )

    def _process_batch(self) -> None:
        if not self.files:
            QMessageBox.information(
                self, "Sin imágenes", "Añade al menos una imagen PNG o JPEG."
            )
            return
        output_dir = (
            QFileDialog.getExistingDirectory(self, "Elegir carpeta de salida", "output")
            or "output"
        )
        self.progress.setMaximum(len(self.files))
        self.progress.setValue(0)
        try:
            results = export_batch(self.files, output_dir)
            self.progress.setValue(len(self.files))
        except InkscapeNotFoundError as error:
            QMessageBox.critical(self, "Inkscape no disponible", str(error))
            return
        except (OSError, RuntimeError, ValueError) as error:
            QMessageBox.critical(self, "Error de exportación", str(error))
            return
        QMessageBox.information(
            self,
            "Listo",
            f"Exportados {len(results)} SVG compatibles con Fusion 360 en {output_dir}.",
        )
