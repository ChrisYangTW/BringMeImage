import pickle
import sys
from datetime import datetime
from pathlib import Path

import httpx

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QApplication, QMainWindow, QStyleFactory, QFileDialog, QMessageBox

from bringmeimage.bringmeimage_main import Ui_MainWindow
from bringmeimage.StartClipWindow import StartClipWindow
from bringmeimage.ParserAndDownloader import ParserRunner, DownloadRunner


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.pool = QThreadPool.globalInstance()
        self.clipboard = QApplication.clipboard()
        self.httpx_client = httpx.Client()

        self.started_clip = False
        self.save_dir = None
        self.url_info_list = []
        self.url_count = 0
        self.model_count = 0
        self.version_count = 0
        self.model_name_dict = {}
        self.version_name_dict = {}

        self.ui.actionLoadClipboardFile.triggered.connect(self.trigger_load_clipboard_file)
        self.ui.actionShowFailUrl.triggered.connect(self.trigger_action_show_fail_url)
        self.ui.choose_folder_button.clicked.connect(self.click_choose_folder_button)
        self.ui.civitai_check_box.clicked.connect(self.click_civitai_check_box)
        self.ui.categorize_check_box.clicked.connect(self.click_categorize_check_box)
        self.ui.clip_push_button.clicked.connect(self.click_clip_push_button)
        self.ui.go_push_button.clicked.connect(self.click_go_push_button)

    def trigger_load_clipboard_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        filters = "Bring Me Image Files (*.bringmeimage)"
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", filters, options=options)
        if file:
            try:
                with open(file, 'rb') as f:
                    loaded_list = pickle.load(f)
                self.url_info_list = loaded_list
                self.url_count = len(self.url_info_list)
                self.ui.operation_text_browser.append(
                    f'[ {len(self.url_info_list)} URLs ]. Click "GO" to start downloading'
                    f' or "Clip" to continue adding (clear checkbox cannot be selected)'
                )
            except pickle.UnpicklingError:
                self.ui.operation_text_browser.append('File exception, failed to read.')


    def trigger_action_show_fail_url(self):
        pass

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

    def click_clip_push_button(self) -> None:
        if self.ui.clear_check_box.isChecked():
            self.url_info_list.clear()

        start_clip_window = StartClipWindow(for_civitai=self.ui.civitai_check_box.isChecked(), parent=self)
        start_clip_window.Start_clip_finished_signal.connect(self.handle_start_clip_finished_signal)
        start_clip_window.setWindowModality(Qt.ApplicationModal)
        start_clip_window.show()

    def handle_start_clip_finished_signal(self, finished_message: tuple):
        legal_url_count, legal_url_list = finished_message
        assert legal_url_count == len(legal_url_list)
        self.url_info_list.extend(legal_url_list)
        self.url_count = len(self.url_info_list)
        self.ui.operation_text_browser.append(
            f'[ {len(self.url_info_list)} URLs ]. Click "GO" to start downloading'
            f' or "Clip" to continue adding (clear checkbox cannot be selected)'
        )
        # todo: test
        print(self.url_info_list)

    def click_go_push_button(self):
        if not self.save_dir:
            QMessageBox.warning(self, 'Warning', 'Set the storage folder first')
            return

        if not self.url_info_list:
            self.ui.operation_text_browser.append('No any url list')

        self.ui.go_push_button.setEnabled(False)
        self.ui.clip_push_button.setEnabled(False)
        if self.ui.civitai_check_box.isChecked():
            self.ui.operation_text_browser.append('Preprocessing, waiting to retrieve model and version names')
            self.get_model_and_version_name()
        else:
            print('start download: normal image url')
            self.start_download_image(model_and_version_name=())

    def get_model_and_version_name(self) -> None:
        model_id_set = set()
        version_id_set = set()

        for image_info in self.url_info_list:
            model_id_set.add(image_info[1][0])
            version_id_set.add(image_info[1][1])

        self.model_count = len(model_id_set)
        self.version_count = len(version_id_set)

        for model_id in model_id_set:
            parser = ParserRunner(httpx_client=self.httpx_client, model_id=model_id)
            self.set_signal_and_add_to_pool(parser)
        for version_id in version_id_set:
            parser = ParserRunner(httpx_client=self.httpx_client, version_id=version_id)
            self.set_signal_and_add_to_pool(parser)

    def set_signal_and_add_to_pool(self, parser):
        parser.signals.Parser_connect_to_api_failed_signal.connect(self.handle_parser_connect_to_api_failed_signal)
        parser.signals.Parser_completed_signal.connect(self.handle_parser_completed_signal)
        self.pool.start(parser)

    def handle_parser_connect_to_api_failed_signal(self, failed_message: str):
        self.pool.clear()
        self.ui.operation_text_browser.append(failed_message)
        self.ui.operation_text_browser.append(
            'Unable to retrieve the full name. It may be due to a connection issue. Click "Go" again.'
        )
        self.ui.go_push_button.setEnabled(True)
        self.ui.clip_push_button.setEnabled(True)

    def handle_parser_completed_signal(self, completed_message: tuple):
        is_model, name_info = completed_message
        if is_model:
            self.model_name_dict.update(name_info)
        else:
            self.version_name_dict.update(name_info)

        if len(self.model_name_dict) == self.model_count and len(self.version_name_dict) == self.version_count:
            print('start download image')
            self.start_download_image(model_and_version_name=(self.model_name_dict, self.version_name_dict))

    def start_download_image(self, model_and_version_name: tuple):
        self.ui.clip_push_button.setEnabled(False)
        for image_info in self.url_info_list:
            downloader = DownloadRunner(httpx_client=self.httpx_client, image_info=image_info, save_dir=self.save_dir,
                                        model_and_version_name=model_and_version_name)
            downloader.signals.download_started_signal.connect(self.handle_download_started_signal)
            downloader.signals.download_connect_to_api_failed_signal.connect(
                self.handle_download_connect_to_api_failed_signal)
            downloader.signals.download_completed_signal.connect(self.handle_download_completed_signal)
            self.pool.start(downloader)

    def handle_download_started_signal(self, started_message: str):
        self.ui.result_text_browser.append(started_message)

    def handle_download_connect_to_api_failed_signal(self, failed_message: str):
        self.ui.result_text_browser.append(failed_message)
        self.url_count -= 1
        if not self.url_count:
            self.ui.go_push_button.setEnabled(True)
            self.ui.clip_push_button.setEnabled(True)

    def handle_download_completed_signal(self, completed_message: str):
        self.ui.result_text_browser.append(completed_message)
        self.url_count -= 1
        if not self.url_count:
            self.ui.go_push_button.setEnabled(True)
            self.ui.clip_push_button.setEnabled(True)

    def closeEvent(self, event) -> None:
        if self.url_info_list:
            reply = QMessageBox.question(self, 'Warning',
                                         'Do you want to save the URL of the clipboard before exiting？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                with open(f'{datetime.now().strftime("%m-%d %H:%M:%S")}.bringmeimage', 'wb') as f:
                    pickle.dump(self.url_info_list, f)

            event.accept()
        event.accept()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    if sys.platform == 'darwin' and 'Fusion' in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create('Fusion'))
    window.show()
    sys.exit(app.exec())