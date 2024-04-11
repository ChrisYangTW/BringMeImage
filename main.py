import sys
from PySide6.QtWidgets import QApplication, QStyleFactory
# If crash after update PySide6 >= 6.6.2
# Jusit remove and reinstall it.
# (Have to remove all packages) pip uninstall -qy shiboken6 PySide6 PySide6_Addons PySide6_Essentials

from bringmeimage.BringMeImageMainWindow import MainWindow


if __name__ == '__main__':
    app = QApplication([])
    if sys.platform == 'darwin' and 'Fusion' in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create('Fusion'))

    window = MainWindow()
    window.show()
    # app.aboutToQuit.connect(window.clear_threadpool_and_close_browser)
    app.aboutToQuit.connect(app.quit)
    sys.exit(app.exec())
