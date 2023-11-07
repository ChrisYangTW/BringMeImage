from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QWidget, QTextBrowser

from bringmeimage.BringMeImageData import ImageData


class FailedUrlsWindow(QDialog):
    """
    QDialog window for displaying the failed download image links
    """
    def __init__(self, process_failed_url_dict: dict, version_id_info_dict: dict, parent=None):
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

        self.process_failed_url_dict = process_failed_url_dict
        self.version_id_info_dict = version_id_info_dict
        self.classified_process_failed_url_dict = {}

        if self.process_failed_url_dict:
            self.show_failed_urls_to_text_browser()

    def show_failed_urls_to_text_browser(self):
        # hint: process_failed_url_dict = {image_url1: ImageData1(dataclass), image_url2: ImageData2(dataclass),}
        # hint: version_id_info = {self.version_id: dataclass(version_name, model_id, model_name, creator)}
        for image_url, image_data in self.process_failed_url_dict.items():
            model_version_name = self.get_model_version_name(image_data.modelVersionId)
            if model_version_name in self.classified_process_failed_url_dict:
                self.classified_process_failed_url_dict[model_version_name].append(image_url)
            else:
                self.classified_process_failed_url_dict[model_version_name] = [image_url]

        for name, url_list in self.classified_process_failed_url_dict.items():
            self.display_text_browser.append(name)
            self.display_text_browser.append('')
            for url in url_list:
                self.display_text_browser.insertHtml(f'<a href="{url}">{url}</a><br>')

    def get_model_version_name(self, modelVersionId: str) -> str:
        return (
            f'{version_id_data.model_name} {version_id_data.version_name}'
            if (version_id_data := self.version_id_info_dict.get(modelVersionId))
            else 'unfounded'
        )

    # Overrides the reject() to allow users to cancel the dialog using the ESC key
    def reject(self):
        self.done(0)


if __name__ == '__main__':
    from PySide6.QtWidgets import QMainWindow, QApplication
    from PySide6.QtGui import Qt


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
            data = {
                'https://civitai.com/images/2805528': ImageData(url='https://civitai.com/images/2805528',
                                                                real_url='', modelVersionId='', postId='',
                                                                imageId='2805528', is_parsed=False),
                'https://civitai.com/images/2805533': ImageData(url='https://civitai.com/images/2805533',
                                                                real_url='', modelVersionId='', postId='',
                                                                imageId='2805533', is_parsed=False),
            }
            history_window = FailedUrlsWindow(
                process_failed_url_dict=data,
                version_id_info_dict={},
                parent=self)
            history_window.setWindowModality(Qt.ApplicationModal)
            history_window.show()


    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec()
