import sys
from PySide6.QtWidgets import QApplication, QStyleFactory
from bringmeimage.BringMeImageMainWindow import MainWindow


if __name__ == '__main__':
    app = QApplication([])
    if sys.platform == 'darwin' and 'Fusion' in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create('Fusion'))

    window = MainWindow()
    window.show()
    app.aboutToQuit.connect(window.clear_threadpool_and_close_browser)
    sys.exit(app.exec())
