from dataclasses import dataclass

from PySide6.QtWidgets import QHBoxLayout, QProgressBar


@dataclass(slots=True)
class ImageData:
    url: str
    src: str = ''
    imageId: str = ''
    is_parsed: bool = False


@dataclass(slots=True)
class ProgressBarData:
    progress_layout: QHBoxLayout
    progress_bar_widget: QProgressBar
    completed: int
    executed: int
    quantity: int
