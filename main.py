import sys
import re
from pathlib import Path

import httpx

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QStyleFactory, QFileDialog

from bringmeimage.bringmeimage_main import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.httpx_client = httpx.Client()
        self.clipboard = QApplication.clipboard()

        self.started_clip = False
        self.save_dir = None
        self.clipboard_text_list = []
        self.legal_url_list = []

        self.timer_for_update_clipboard = QTimer()
        self.timer_for_update_clipboard.timeout.connect(self.update_clipboard)
        self.ui.choose_folder_button.clicked.connect(self.click_choose_folder_button)
        self.ui.civitai_check_box.clicked.connect(self.click_civitai_check_box)
        self.ui.categorize_check_box.clicked.connect(self.click_categorize_check_box)
        self.ui.stayon_check_box.clicked.connect(self.click_stayon_check_box)
        self.ui.start_clip_push_button.clicked.connect(self.click_start_clip_push_button)

    def click_choose_folder_button(self) -> None:
        """
        Set the path for saving the image
        """
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        if folder := QFileDialog.getExistingDirectory(self, "Select Folder", options=options):
            self.ui.folder_line_edit.setText(folder)
            self.save_dir = Path(folder)

    def click_civitai_check_box(self, checked: bool) -> None:
        if checked:
            self.ui.categorize_check_box.setChecked(True)
            print('true')
        else:
            self.ui.categorize_check_box.setChecked(False)
            print('false')

    def click_categorize_check_box(self, checked: bool) -> None:
        if checked:
            if not self.ui.civitai_check_box.isChecked():
                self.ui.categorize_check_box.setChecked(False)
            else:
                print('true')
        else:
            print('false')

    def click_stayon_check_box(self, checked: bool) -> None:
        if checked:
            self.setWindowFlag(Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint, False)

        #  In some cases, changing the window flags may not immediately update the window's visibility.
        #  Calling self.show() ensures that the window is shown again, taking into account any changes made to the flags
        self.show()

    def click_start_clip_push_button(self) -> None:
        if self.started_clip:
            self.started_clip = False
            self.ui.start_clip_push_button.setText('Start Clip')
            self.ui.statusbar.showMessage('')
            self.timer_for_update_clipboard.stop()
        else:
            self.clipboard.clear()
            self.started_clip = True
            self.ui.start_clip_push_button.setText('Stop Clip')
            self.ui.statusbar.showMessage('Updating clipboard ...')
            self.timer_for_update_clipboard.start(1000)


    def update_clipboard(self) -> None:
        mime_data = self.clipboard.mimeData()

        if mime_data.hasText():
            text = mime_data.text()
            if text not in self.clipboard_text_list:
                self.clipboard_text_list.append(text)
                if url := self.initial_parse(text):
                    self.legal_url_list.append(url)
                    self.ui.operation_text_browser.append(text)

    def initial_parse(self, url):
        # r'/(\d+)\?(?:(?=[^?]*modelVersionId=(\d+)))?(?:(?=[^?]*modelId=(\d+)))?(?:(?=[^?]*postId=(\d+)))?')
        pattern = r"https://civitai.com/images/(\d+)\?.*&modelVersionId=(\d+)&modelId=(\d+)&postId=(\d+)"

        if match := re.match(pattern, url):
            return match[3], match[2], match[4], match[1]

        self.ui.result_text_browser.append(f'Not match {url}')
        return


    def get_real_image_url(self, image_id, model_version_id, model_id, post_id):
        image_url = f'https://civitai.com/api/v1/images?' \
                    f'modelId={model_id}&modelVersionId={model_version_id}&postId={post_id}'
        try:
            r = self.httpx_client.get(image_url)
            image_info_dict = r.json()
            image_info = image_info_dict['items']
            for image in image_info:
                if image['id'] == int(image_id):
                    print(image['url'])
        except Exception as e:
            print(e)



if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    if sys.platform == 'darwin' and 'Fusion' in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create('Fusion'))
    window.show()
    sys.exit(app.exec())