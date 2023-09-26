import re

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QPushButton, QWidget, QSizePolicy,
                               QMessageBox, QLabel)


class StartClipWindow(QDialog):
    """
    QDialog window for starting to clip and parse urls
    """
    Start_clip_closed_window_signal = Signal()
    Start_clip_finished_signal = Signal(list)

    def __init__(self, for_civitai: bool, legal_url_list: list, parent=None):
        super().__init__(parent)
        self.for_civitai = for_civitai
        self.legal_url_list = legal_url_list
        self.initUI()
        # Dialog always stay on
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        #  In some cases, changing the window flags may not immediately update the window's visibility.
        #  Calling self.show() ensures that the window is shown again, taking into account any changes made to the flags
        self.show()

        self.clipboard_text_list = []
        self.started_clip = False

        # r'/(\d+)\?(?:(?=[^?]*modelVersionId=(\d+)))?(?:(?=[^?]*modelId=(\d+)))?(?:(?=[^?]*postId=(\d+)))?')
        self.for_civitai_pattern_1 = re.compile(
            r"https://civitai.com/images/(\d+)\?.*&modelVersionId=(\d+)&modelId=(\d+)&postId=(\d+)")
        self.for_civitai_pattern_2 = re.compile(
            r"https://civitai.com/images/(\d+)\?postId=(\d+)&tags=(\d+)")
        self.normal_pattern = re.compile(r".+\.(png|jpeg|jpg)$")

        self.clipboard = QApplication.clipboard()
        self.timer_for_update_clipboard = QTimer()
        self.timer_for_update_clipboard.timeout.connect(self.update_clipboard)
        self.start_clip_button.clicked.connect(self.start_clip)
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

        self.count_label = QLabel(f'Clip: {len(self.legal_url_list)}')
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
        If self.legal_url_list is not empty, ask the user before closing the window
        :param called_by_finished_button: set True for ignoring whether self.legal_url_list is empty
        :return:
        """
        if self.started_clip:
            return

        if not called_by_finished_button and self.legal_url_list:
            reply = QMessageBox.question(self, 'Warning',
                                         'There are existing records. Are you sure you want to close the window?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        self.Start_clip_closed_window_signal.emit()
        self.done(0)

    def start_clip(self) -> None:
        if self.started_clip:
            self.started_clip = False
            self.start_clip_button.setText('Start')
            self.timer_for_update_clipboard.stop()
            self.finish_clip_button.setEnabled(True)
        else:
            self.clipboard.clear()
            self.started_clip = True
            self.start_clip_button.setText('Stop')
            self.finish_clip_button.setEnabled(False)
            self.timer_for_update_clipboard.start(1000)

    def finish_clip(self):
        if not self.legal_url_list:
            self.reject(called_by_finished_button=True)
            return

        self.Start_clip_finished_signal.emit(self.legal_url_list)
        self.reject(called_by_finished_button=True)

    def update_clipboard(self) -> None:
        mime_data = self.clipboard.mimeData()

        if mime_data.hasText():
            url_text = mime_data.text()
            if url_text not in self.clipboard_text_list:
                self.clipboard_text_list.append(url_text)
                if url_info := self.initial_parse(url_text):
                    self.legal_url_list.append(url_info)
                    self.count_label.setText(f'Clip: {len(self.legal_url_list)}')

    def initial_parse(self, url_text: str) -> tuple | None:
        """
        if url_text is legal, return (url_text, (model_id, model_version_id, post_id, image_id))
        :param url_text:
        :return:
        """
        url_info = ''
        if self.for_civitai:
            if match := self.for_civitai_pattern_1.match(url_text):
                url_info = url_text, (match[3], match[2], match[4], match[1])
            elif match := self.for_civitai_pattern_2.match(url_text):
                url_info = url_text, (None, None, match[2], match[1])
        elif match := self.normal_pattern.match(url_text):
            url_info = url_text, None

        if url_info:
            if url_info not in self.legal_url_list:
                return url_info
            print('\033[33m' + f'URL existed: {url_text}' + '\033[0m')
            return
        # disable self.illegal (used for test)
        # self.illegal_label.setText('illegal url')
        # self.time_for_show_not_legal.singleShot(1000, lambda: self.illegal_label.setText(''))
        print('\033[33m' + f'URL cannot parse: {url_text}' + '\033[0m')


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
            start_clip_window = StartClipWindow(for_civitai=True, legal_url_list=[], parent=self)
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
