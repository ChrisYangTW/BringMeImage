from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QWidget, QTextBrowser


class FailedUrlsWindow(QDialog):
    """
    QDialog window for displaying the failed download image links
    """
    def __init__(self, failed_urls: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Failed url')
        self.setGeometry(100, 100, 600, 400)

        v_layout = QVBoxLayout(self)
        self.display_text_browser = QTextBrowser(self)
        self.display_text_browser.setOpenExternalLinks(True)
        v_layout.addWidget(self.display_text_browser)

        # Move the QDialog window to the center of the main window
        if self.parentWidget():
            center_point = self.parentWidget().geometry().center()
            self.move(center_point.x() - self.width() / 2, center_point.y() - self.height() / 2)

        self.failed_urls = failed_urls
        if self.failed_urls:
            self.show_failed_urls_to_text_browser()

    def show_failed_urls_to_text_browser(self):
        if self.failed_urls[0][1]:
            failed_url_dict = self.sort_failed_urls()
            for name, failed_urls in failed_url_dict.items():
                self.display_text_browser.append(name)
                self.display_text_browser.append('')
                for failed_url in failed_urls:
                    self.display_text_browser.insertHtml(f'<a href="{failed_url}">{failed_url}</a><br>')
            return

        self.display_text_browser.append('Failed urls:')
        self.display_text_browser.append('')
        for failed_url, _, _ in self.failed_urls:
            self.display_text_browser.insertHtml(f'<a href="{failed_url}">{failed_url}</a><br>')

    def sort_failed_urls(self):
        failed_url_dict = {}
        for failed_url, model_name, version_name in self.failed_urls:
            if f'{model_name}:{version_name}' not in failed_url_dict:
                failed_url_dict[f'{model_name}:{version_name}'] = []
            failed_url_dict[f'{model_name}:{version_name}'].append(failed_url)
        return failed_url_dict

    # Overrides the reject() to allow users to cancel the dialog using the ESC key
    def reject(self):
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

        def show_editable_window(self):
            history_window = FailedUrlsWindow(
                failed_urls=[('abc.com', 'M1', 'V1'), ('def.com', 'M1', 'V1'),
                             ('ghi.com', 'M1', 'V2'), ('jkl.com', 'M1', 'V2'),
                             ('mno.com', 'M2', 'V1')],
                parent=self)
            history_window.setWindowModality(Qt.ApplicationModal)
            history_window.show()


    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
