# QDialog window for copying URLs that match the parsing rules.
# Supported formats:
#     for civitai.com:
#         "https://civitai.com/images/(\d+)"
#     for general picture file:
#         ".+\.(png|jpeg|jpg)$"
import re

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QPushButton, QWidget, QSizePolicy,
                               QMessageBox, QLabel)

from bringmeimage.BringMeImageData import ImageData
from bringmeimage.LoggerConf import get_logger
logger = get_logger(__name__)


class StartClipWindow(QDialog):
    """
    QDialog window for starting to clip and parsing URLs
    """
    Start_Clip_Close_Window_Signal = Signal(dict)

    def __init__(self, for_civitai: bool, urls: dict, parent=None):
        super().__init__(parent)
        self.for_civitai = for_civitai
        self.urls = urls
        self.initUI()

        # Dialog always stay on
        # In some cases, changing the window flags may not immediately update the window's visibility.
        # Calling self.show() ensures that the window is shown again, taking into account any changes made to the flags
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.show()

        self.clipboard_text_list = []
        self.isStarted = False

        self.for_civitai_pattern = re.compile(r"https://civitai.com/images/(?P<imageId>\d+)")
        self.normal_pattern = re.compile(r"http.+\.(png|jpeg|jpg)$")

        self.clipboard = QApplication.clipboard()
        self.timer_for_update_clipboard = QTimer()
        self.timer_for_update_clipboard.timeout.connect(self.update_clipboard)
        self.start_clip_button.clicked.connect(self.start_or_stop_clip)
        self.finish_clip_button.clicked.connect(self.finish_clip)

    def initUI(self):
        if self.for_civitai:
            self.setWindowTitle('Clip for Civital')
        else:
            self.setWindowTitle('Clip')
        self.setGeometry(100, 100, 200, 150)

        self.v_layout = QVBoxLayout(self)

        self.start_clip_button = QPushButton('Start')
        self.start_clip_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.v_layout.addWidget(self.start_clip_button)

        self.count_label = QLabel(f'Clip: {len(self.urls)}')
        font = QFont()
        font.setPointSize(18)
        self.count_label.setFont(font)
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet("color: green;")
        self.count_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.v_layout.addWidget(self.count_label)

        self.finish_clip_button = QPushButton('Finish')
        self.finish_clip_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.v_layout.addWidget(self.finish_clip_button)

        self.v_layout.setStretch(0, 2)
        self.v_layout.setStretch(1, 2)
        self.v_layout.setStretch(2, 1)

        self.setLayout(self.v_layout)

        # Move the QDialog window to the center of the main window
        if self.parentWidget():
            center_point = self.parentWidget().geometry().center()
            self.move(center_point.x() - self.width() / 2, center_point.y() - self.height() / 2)

    # Overrides the reject() to allow users to cancel the dialog using the ESC key
    def reject(self, called_by_finished_button=False) -> None:
        """
        If self.urls is not empty, ask the user before closing the window
        :param called_by_finished_button: set True for emitting a signal (self.urls)
        :return:
        """
        if self.isStarted:
            return

        if not called_by_finished_button and self.urls:
            reply = QMessageBox.question(self, 'Warning',
                                         'There are existing records. Are you sure you want to close the window?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            self.done(0)
            return

        self.Start_Clip_Close_Window_Signal.emit(self.urls)
        self.done(0)

    def start_or_stop_clip(self) -> None:
        """
        Set up the clip button. Once activated, read the contents of the clipboard at intervals of 1000ms.
        :return: None
        """
        if self.isStarted:
            self.isStarted = False
            self.start_clip_button.setText('Start')
            self.timer_for_update_clipboard.stop()
            self.finish_clip_button.setEnabled(True)
        else:
            self.clipboard.clear()
            self.isStarted = True
            self.start_clip_button.setText('Stop')
            self.finish_clip_button.setEnabled(False)
            self.timer_for_update_clipboard.start(1000)

    def finish_clip(self) -> None:
        """
        Set up the finish button.
        :return:
        """
        self.reject(called_by_finished_button=True)

    def update_clipboard(self) -> None:
        """
        Read the contents of the clipboard and parse them.
        The content will be recorded in self.clipboard_text_list to avoid duplicate processing.
        :return:
        """
        mime_data = self.clipboard.mimeData()
        if mime_data.hasText():
            url = mime_data.text()
            if url in self.clipboard_text_list:
                logger.info(f'URL already processed: {url}')
            else:
                self.clipboard_text_list.append(url)
                if url_data := self.initial_parse(url):
                    self.urls.update({url: url_data})
                    self.count_label.setText(f'Clip: {len(self.urls)}')

            self.clipboard.clear()

    def initial_parse(self, url: str) -> ImageData | None:
        """
        If url_text is legal, return a ImageData object
        :param url: the URL obtained from the clipboard
        :return:
        """
        img_data = None
        if self.for_civitai:
            if match := self.for_civitai_pattern.match(url):
                img_data = ImageData(url=url, imageId=match.group('imageId'))
            elif self.normal_pattern.match(url):
                img_data = ImageData(url=url, src=url, is_parsed=True)
        else:
            if self.normal_pattern.match(url):
                img_data = ImageData(url=url, src=url, is_parsed=True)

        if img_data:
            if url not in self.urls:
                return img_data
            logger.info(f'URL already exists in the legal list: {url}')
            return

        logger.info(f'URL cannot parse: {url}')


if __name__ == '__main__':
    from PySide6.QtWidgets import QMainWindow

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.initUI()

        def initUI(self):
            self.setWindowTitle('Button Window')
            self.resize(800, 600)
            widget = QWidget()
            self.v_layout = QVBoxLayout()
            widget.setLayout(self.v_layout)
            self.setCentralWidget(widget)

            self.button_1 = QPushButton('For civitai.com', self)
            self.button_1.clicked.connect(lambda: self.show_window(1))
            self.v_layout.addWidget(self.button_1)

            self.button_2 = QPushButton('For general image', self)
            self.button_2.clicked.connect(lambda: self.show_window(2))
            self.v_layout.addWidget(self.button_2)

        def show_window(self, window_type: int):
            if window_type == 1:
                start_clip_window = StartClipWindow(for_civitai=True, urls={}, parent=self)
            else:
                start_clip_window = StartClipWindow(for_civitai=False, urls={}, parent=self)

            start_clip_window.Start_Clip_Close_Window_Signal.connect(self.handle_clip_closed_window_signal)
            start_clip_window.setWindowModality(Qt.ApplicationModal)
            start_clip_window.show()

        @staticmethod
        def handle_clip_closed_window_signal(image_info_dict: dict):
            for image_url, image_data in image_info_dict.items():
                print(image_url, image_data)


    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
