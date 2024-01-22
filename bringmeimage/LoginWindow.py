from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QPushButton, QWidget, QSizePolicy, QLabel,
                               QSpacerItem)
from selenium.webdriver.chrome.webdriver import WebDriver

from bringmeimage.LoggerConf import get_logger
logger = get_logger(__name__)


class LoginWindow(QDialog):
    Login_Window_Start_Signal = Signal()
    Login_Window_Finish_Signal = Signal()
    Login_Window_Close_Signal = Signal()
    Login_Window_Reject_Signal = Signal()
    """
    QDialog window for setting the browser
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.browser: WebDriver | None = None

        # Dialog always stay on
        # In some cases, changing the window flags may not immediately update the window's visibility.
        # Calling self.show() ensures that the window is shown again, taking into account any changes made to the flags
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.show()

    def initUI(self):
        self.setWindowTitle('Manual login')
        self.setGeometry(100, 100, 300, 200)

        self.v_layout = QVBoxLayout(self)

        self.status_label = QLabel()
        self.status_label.setText('Click "Start" to login')
        self.status_label.setAlignment(Qt.AlignCenter)
        self.v_layout.addWidget(self.status_label)

        self.start_button = QPushButton('Start')
        self.start_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.start_button.clicked.connect(self.start_login)
        self.v_layout.addWidget(self.start_button)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.v_layout.addSpacerItem(self.spacer)

        self.finish_label = QLabel('After confirming login, click on "Finish"')
        self.finish_label.setAlignment(Qt.AlignCenter)
        self.finish_label.setStyleSheet("color: gray;")
        self.finish_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.v_layout.addWidget(self.finish_label)

        self.finish_button = QPushButton('Finish')
        self.finish_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.finish_button.clicked.connect(self.finish)
        self.finish_button.setEnabled(False)
        self.v_layout.addWidget(self.finish_button)

        self.v_layout.setStretch(0, 1)
        self.v_layout.setStretch(1, 2)
        self.v_layout.setStretch(2, 1)
        self.v_layout.setStretch(3, 1)
        self.v_layout.setStretch(4, 2)

        self.setLayout(self.v_layout)

        # Move the QDialog window to the center of the main window
        if self.parentWidget():
            center_point = self.parentWidget().geometry().center()
            self.move(center_point.x() - self.width() / 2, center_point.y() - self.height() / 2)

    def start_login(self):
        self.Login_Window_Start_Signal.emit()
        self.finish_label.setStyleSheet("color: green;")
        self.finish_button.setEnabled(True)

    def finish(self):
        self.Login_Window_Finish_Signal.emit()

    @Slot()
    def handle_login_ok(self):
        self.Login_Window_Close_Signal.emit()
        self.done(0)

    # Overrides the reject() to allow users to cancel the dialog using the ESC key
    def reject(self) -> None:
        """
        :return:
        """
        self.Login_Window_Reject_Signal.emit()
        self.done(0)


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
            self.button_1.clicked.connect(self.show_window)
            self.v_layout.addWidget(self.button_1)

        def show_window(self):
            set_browser_window = LoginWindow(parent=self)
            set_browser_window.setWindowModality(Qt.ApplicationModal)
            set_browser_window.show()


    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
