import re

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QPushButton, QWidget, QSizePolicy,
                               QMessageBox, QLabel)


class StartClipWindow(QDialog):
    """
    QDialog window for starting to clip urls
    """
    Start_clip_finished_signal = Signal(tuple)

    def __init__(self, for_civitai=True, parent=None):
        super().__init__(parent)
        self.for_for_civitai = for_civitai
        self.initUI()
        # Dialog always stay on
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        #  In some cases, changing the window flags may not immediately update the window's visibility.
        #  Calling self.show() ensures that the window is shown again, taking into account any changes made to the flags
        self.show()

        self.clipboard_text_list = []
        self.legal_url_list = []
        self.legal_url_count = 0
        self.started_clip = False

        self.clipboard = QApplication.clipboard()
        self.timer_for_update_clipboard = QTimer()
        self.timer_for_update_clipboard.timeout.connect(self.update_clipboard)

        self.time_for_show_not_legal = QTimer()

        self.start_clip_button.clicked.connect(self.click_start_clip_button)
        self.finished_button.clicked.connect(self.click_finished_button)

    def initUI(self):
        self.setWindowTitle('Clip')
        self.setGeometry(100, 100, 200, 150)

        self.v_layout = QVBoxLayout(self)

        self.start_clip_button = QPushButton('Start')
        self.start_clip_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.v_layout.addWidget(self.start_clip_button)

        self.count_label = QLabel('Clip: 0')
        font = QFont()
        font.setPointSize(16)
        self.count_label.setFont(font)
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet("color: green;")
        self.count_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.v_layout.addWidget(self.count_label)

        # disable self.illegal (used for test)
        # self.illegal_label = QLabel()
        # self.illegal_label.setAlignment(Qt.AlignCenter)
        # self.illegal_label.setStyleSheet("color: pink;")
        # self.v_layout.addWidget(self.illegal_label)

        self.finished_button = QPushButton('Finish')
        self.finished_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.v_layout.addWidget(self.finished_button)

        self.v_layout.setStretch(0, 2)
        self.v_layout.setStretch(1, 2)
        self.v_layout.setStretch(2, 1)

        self.setLayout(self.v_layout)

        # Move the QDialog window to the center of the main window
        if self.parentWidget():
            center_point = self.parentWidget().geometry().center()
            self.move(center_point.x() - self.width() / 2, center_point.y() - self.height() / 2)

    # Overrides the reject() to allow users to cancel the dialog using the ESC key
    def reject(self, from_finished_button=False) -> None:
        """
        If self.urls_editor is not empty, ask the user before closing the window
        :return:
        """
        if self.started_clip:
            return

        if not from_finished_button and self.legal_url_list:
            QMessageBox.warning(None, 'Warning', 'list had some urls')
            return

        self.done(0)

    def click_start_clip_button(self) -> None:
        """
        :return:
        """
        if self.started_clip:
            self.started_clip = False
            self.start_clip_button.setText('Start')
            self.timer_for_update_clipboard.stop()
            self.finished_button.setEnabled(True)
        else:
            self.clipboard.clear()
            self.started_clip = True
            self.start_clip_button.setText('Stop')
            self.finished_button.setEnabled(False)
            self.timer_for_update_clipboard.start(1000)

    def click_finished_button(self):
        self.Start_clip_finished_signal.emit((self.legal_url_count, self.legal_url_list))
        self.reject(from_finished_button=True)

    def update_clipboard(self) -> None:
        mime_data = self.clipboard.mimeData()

        if mime_data.hasText():
            text = mime_data.text()
            if text not in self.clipboard_text_list:
                self.clipboard_text_list.append(text)
                if url := self.initial_parse(text):
                    self.legal_url_list.append(url)
                    self.legal_url_count += 1
                    self.count_label.setText(f'Clip: {self.legal_url_count}')

    def initial_parse(self, text: str) -> tuple|None:
        """
        if text is legal, return (model_id, model_version_id, post_id, image_id)
        :param text:
        :return:
        """
        if not self.for_for_civitai:
            return text, None
        # r'/(\d+)\?(?:(?=[^?]*modelVersionId=(\d+)))?(?:(?=[^?]*modelId=(\d+)))?(?:(?=[^?]*postId=(\d+)))?')
        pattern = r"https://civitai.com/images/(\d+)\?.*&modelVersionId=(\d+)&modelId=(\d+)&postId=(\d+)"

        if match := re.match(pattern, text):
            return text, (match[3], match[2], match[4], match[1])

        # disable self.illegal (used for test)
        # self.illegal_label.setText('illegal url')
        # self.time_for_show_not_legal.singleShot(1000, lambda: self.illegal_label.setText(''))
        print('\033[33m' + f'Cannot parse: {text}' + '\033[0m')
        return


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

            self.button = QPushButton('Open Window', self)
            self.button.clicked.connect(self.show_window)
            self.v_layout.addWidget(self.button)

        def show_window(self):
            start_clip_window = StartClipWindow(parent=self)
            start_clip_window.Start_clip_finished_signal.connect(self.handle_start_clip_finished_signal)
            start_clip_window.setWindowModality(Qt.ApplicationModal)
            start_clip_window.show()

        def handle_start_clip_finished_signal(self, info: list):
            for info in info:
                print(info)


    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
