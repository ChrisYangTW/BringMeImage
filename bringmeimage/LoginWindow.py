from PySide6.QtCore import Signal, Qt, Slot
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QPushButton, QWidget, QSizePolicy, QLabel,
                               QSpacerItem)

from bringmeimage.LoggerConf import get_logger
logger = get_logger(__name__)


class LoginWindow(QDialog):
    """
    QDialog window for setting the browser
    """
    Login_Window_Start_Signal = Signal()
    Login_Window_Finish_Signal = Signal()
    Login_Window_ReLogin_Signal = Signal()
    Login_Window_Reject_Signal = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.initUI()

        # Dialog always stay on
        # In some cases, changing the window flags may not immediately update the window's visibility.
        # Calling self.show() ensures that the window is shown again, taking into account any changes made to the flags
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.show()

    def initUI(self) -> None:
        self.setWindowTitle('Manual login')
        self.setGeometry(100, 100, 300, 200)

        self.v_layout = QVBoxLayout(self)

        self.status_label = self.create_label('1. Click "Open" will open a browser for manual login')
        self.v_layout.addWidget(self.status_label)

        self.open_button = QPushButton('Open')
        self.open_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.open_button.clicked.connect(self.open_browser)
        self.v_layout.addWidget(self.open_button)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.v_layout.addSpacerItem(self.spacer)

        self.finish_label_1 = self.create_label('2. After confirming login, click on "Finish"')
        self.v_layout.addWidget(self.finish_label_1)

        self.finish_label_2 = self.create_label('   (No need to close the browser)')
        self.v_layout.addWidget(self.finish_label_2)

        self.finish_button = QPushButton('Finish')
        self.finish_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.finish_button.clicked.connect(self.finish)
        self.finish_button.setEnabled(False)
        self.v_layout.addWidget(self.finish_button)

        self.note_label_1 = self.create_label('3. The program will attempt to re-login.(check)')
        self.v_layout.addWidget(self.note_label_1)

        self.note_label_2 = self.create_label('   (May be a brief freezing during the process)')
        self.v_layout.addWidget(self.note_label_2)

        self.v_layout.setStretch(0, 1)
        self.v_layout.setStretch(1, 2)
        self.v_layout.setStretch(2, 1)
        self.v_layout.setStretch(3, 1)
        self.v_layout.setStretch(4, 1)
        self.v_layout.setStretch(5, 2)
        self.v_layout.setStretch(6, 1)
        self.v_layout.setStretch(7, 1)

        self.setLayout(self.v_layout)

        # Move the QDialog window to the center of the main window
        if self.parentWidget():
            center_point = self.parentWidget().geometry().center()
            self.move(center_point.x() - self.width() / 2, center_point.y() - self.height() / 2)

    @staticmethod
    def create_label(label_string: str) -> QLabel:
        label = QLabel(label_string)
        label.setAlignment(Qt.AlignLeft)
        label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        return label

    def open_browser(self) -> None:
        """
        Notify the main thread to open a browser for manual login by the user
        :return:
        """
        self.Login_Window_Start_Signal.emit()
        self.open_button.setEnabled(False)
        self.finish_button.setEnabled(True)

    def finish(self) -> None:
        """
        Notify the main thread to save cookies
        :return:
        """
        self.Login_Window_Finish_Signal.emit()

    @Slot()
    def handle_login_ok(self) -> None:
        """
        Notify the main thread to test re-login and close the LoginWindow window
        :return:
        """
        self.Login_Window_ReLogin_Signal.emit()
        self.done(0)

    # Overrides the reject() to allow users to cancel the dialog using the ESC key
    def reject(self) -> None:
        """
        Notify the main thread to close the temporary browser and close the LoginWindow window
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
