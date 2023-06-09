from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QWidget, QTextBrowser, QRadioButton, QButtonGroup, \
    QHBoxLayout, QLabel, QSizePolicy, QGroupBox


class FailedUrlsWindow(QDialog):
    """
    QDialog window for show history
    """
    def __init__(self, failed_urls: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Failed url')
        self.setGeometry(100, 100, 600, 400)

        v_layout = QVBoxLayout(self)
        self.display_text_browser = QTextBrowser(self)
        v_layout.addWidget(self.display_text_browser)

        # Move the QDialog window to the center of the main window
        if self.parentWidget():
            center_point = self.parentWidget().geometry().center()
            self.move(center_point.x() - self.width() / 2, center_point.y() - self.height() / 2)

        self.failed_urls = failed_urls
        self.show_failed_urls_to_text_browser()

    def show_failed_urls_to_text_browser(self):
        """
        :return:
        """
        self.display_text_browser.setOpenExternalLinks(True)
        for failed_url in self.failed_urls:
            self.display_text_browser.insertHtml(f'<a href="{failed_url}">{failed_url}</a><br>')

    # Overrides the reject() to allow users to cancel the dialog using the ESC key
    def reject(self):
        self.done(0)


class ClipboardWindow(QDialog):
    """
    QDialog window for ...
    """
    Clipboard_load_signal = Signal(int)

    def __init__(self, download_mode: tuple, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Load clipboard')
        self.resize(100, 200)

        v_box = QVBoxLayout()

        self.load_button = QPushButton('Load file')
        self.load_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        v_box.addWidget(self.load_button)
        self.setLayout(v_box)


        # Move the QDialog window to the center of the main window
        if self.parentWidget():
            center_point = self.parentWidget().geometry().center()
            self.move(center_point.x() - self.width() / 2, center_point.y() - self.height() / 2)

    def set_radio_button_checked(self, download_mode):
        match download_mode:
            case (True, False):
                self.one.setChecked(True)
            case (False, True):
                self.two.setChecked(True)
            case (True, True):
                self.three.setChecked(True)

    def radio_button_clicked(self, item):
        select_number = item.group().checkedId()
        self.DevConfig_setup_signal.emit(select_number)

    def reject(self) -> None:
        self.done(0)


if __name__ == '__main__':
    from PySide6.QtWidgets import QMainWindow, QApplication
    from PySide6.QtGui import Qt, QFont


    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.initUI()

        def initUI(self):
            self.setWindowTitle('Button Window')
            self.resize(800, 600)
            widget = QWidget()
            v_layout = QVBoxLayout()
            widget.setLayout(v_layout)
            self.setCentralWidget(widget)

            self.button1 = QPushButton('Open History Window', self)
            self.button1.clicked.connect(self.show_editable_window)
            v_layout.addWidget(self.button1)

            self.button2 = QPushButton('Open Config Window', self)
            self.button2.clicked.connect(self.show_config_window)
            v_layout.addWidget(self.button2)

        def show_editable_window(self):
            history_window = FailedUrlsWindow(failed_urls=['abc', 'def'], parent=self)
            history_window.setWindowModality(Qt.ApplicationModal)
            history_window.show()

        def show_config_window(self):
            config_window = ClipboardWindow(download_mode=(True, True), parent=self)
            config_window.setWindowModality(Qt.ApplicationModal)
            config_window.show()


    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
