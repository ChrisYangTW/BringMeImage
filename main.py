import pickle
import sys
from datetime import datetime
from pathlib import Path

import httpx

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QTextCharFormat
from PySide6.QtWidgets import (QApplication, QMainWindow, QStyleFactory, QFileDialog, QMessageBox, QHBoxLayout,
                               QLabel, QProgressBar)

from bringmeimage.bringmeimage_main import Ui_MainWindow
from bringmeimage.StartClipWindow import StartClipWindow
from bringmeimage.ActionWindow import FailedUrlsWindow
from bringmeimage.ParserAndDownloader import ParserRunner, DownloadRunner


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.pool = QThreadPool.globalInstance()
        self.httpx_client = httpx.Client()

        self.started_clip = False
        self.save_dir = None
        self.legal_url_info_list = []
        self.download_failed_original_url_list = []
        self.model_count = 0
        self.version_count = 0
        self.model_name_dict = {}
        self.version_name_dict = {}

        self.progress_bar_list = []
        self.progress_bar_info = {}

        self.ui.actionLoadClipboardFile.triggered.connect(self.trigger_load_clipboard_file)
        self.ui.actionShowFailUrl.triggered.connect(self.trigger_action_show_fail_url)
        self.ui.folder_line_edit.mousePressEvent = self.click_folder_line_edit_mouse_press
        self.ui.civitai_check_box.clicked.connect(self.click_civitai_check_box)
        self.ui.categorize_check_box.clicked.connect(self.click_categorize_check_box)
        self.ui.clear_push_button.clicked.connect(self.click_clear_push_button)
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
                    record = pickle.load(f)
            except pickle.UnpicklingError:
                self.ui.operation_text_browser.append(
                    f'{datetime.now().strftime("%H:%M:%S")} '
                    f'The file appears to have been modified and is no longer readable'
                )
            self.load_record(record)

    def load_record(self, record: tuple):
        self.ui.civitai_check_box.setChecked(record[0])
        self.ui.categorize_check_box.setChecked(record[1])
        self.legal_url_info_list = record[2]
        self.ui.civitai_check_box.setEnabled(False)
        self.ui.categorize_check_box.setEnabled(False)
        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_url_info_list)} URLs ] | Click "GO" to start downloading'
            f' or "Clip" to continue adding (clear checkbox cannot be selected)'
        )

    def trigger_action_show_fail_url(self):
        failed_url_window = FailedUrlsWindow(failed_urls=self.download_failed_original_url_list, parent=self)
        failed_url_window.setWindowModality(Qt.ApplicationModal)
        failed_url_window.show()

    def click_folder_line_edit_mouse_press(self, event):
        """
        Set the path for saving the image
        """
        if event.button() == Qt.LeftButton:
            options = QFileDialog.Options()
            options |= QFileDialog.ShowDirsOnly
            if folder := QFileDialog.getExistingDirectory(self, "Select Folder", options=options):
                self.ui.folder_line_edit.setText(folder)
                self.save_dir = Path(folder)

    def click_civitai_check_box(self, checked: bool) -> None:
        """
        When the "CivitAi" checkbox is checked, the "Categorize" checkbox is automatically checked by default
        """
        if checked:
            self.ui.categorize_check_box.setChecked(True)
        else:
            self.ui.categorize_check_box.setChecked(False)

    def click_categorize_check_box(self, checked: bool) -> None:
        """
        The "Categorize" checkbox can only be checked when the "CivitAi" checkbox is selected
        """
        if checked and not self.ui.civitai_check_box.isChecked():
            self.ui.categorize_check_box.setChecked(False)

    def click_clear_push_button(self):
        reply = QMessageBox.question(self, 'Warning',
                                     'Are you sure you want to clear all records?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.legal_url_info_list.clear()
            self.ui.civitai_check_box.setEnabled(True)
            self.ui.categorize_check_box.setEnabled(True)

    def click_clip_push_button(self) -> None:
        legal_url_count = len(self.legal_url_info_list)
        start_clip_window = StartClipWindow(for_civitai=self.ui.civitai_check_box.isChecked(),
                                            legal_url_count=legal_url_count, parent=self)
        start_clip_window.Start_clip_finished_signal.connect(self.handle_start_clip_finished_signal)
        start_clip_window.Start_clip_close_window_signal.connect(self.handle_start_clip_close_window_signal)
        start_clip_window.setWindowModality(Qt.ApplicationModal)
        start_clip_window.show()

        self.able_option_action(enable=False)

    def handle_start_clip_finished_signal(self, finished_message: tuple):
        self.ui.civitai_check_box.setEnabled(False)
        self.ui.categorize_check_box.setEnabled(False)

        legal_url_count, legal_url_list = finished_message
        assert legal_url_count == len(legal_url_list)
        self.legal_url_info_list.extend(legal_url_list)
        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_url_info_list)} URLs ] | Click "GO" to start downloading'
            f' or "Clip" to continue adding (clear checkbox cannot be selected)'
        )

    def handle_start_clip_close_window_signal(self, close_window_signal: bool):
        if close_window_signal:
            self.able_option_action()

    def click_go_push_button(self):
        if not self.save_dir:
            QMessageBox.warning(self, 'Warning', 'Set the storage folder first')
            return

        if not self.legal_url_info_list:
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'There are no URLs in the list'
            )
            return

        self.ui.clip_push_button.setEnabled(False)
        self.ui.go_push_button.setEnabled(False)
        self.ui.actionLoadClipboardFile.setEnabled(False)
        self.clear_progress_bar()

        if self.ui.civitai_check_box.isChecked():
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | '
                f'Preprocessing, waiting to retrieve model and version names'
            )
            self.get_model_and_version_name()
        else:
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | '
                f'Start downloading images'
            )
            self.start_download_image(model_and_version_name=())

    def get_model_and_version_name(self) -> None:
        model_id_set = set()
        version_id_set = set()

        for image_info in self.legal_url_info_list:
            model_id_set.add(image_info[1][0])
            version_id_set.add(image_info[1][1])

        self.model_count = len(model_id_set)
        self.version_count = len(version_id_set)
        self.add_progress_bar(task_name='Preprocessing', count=self.model_count + self.version_count)

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

    def handle_parser_connect_to_api_failed_signal(self, failed_message: tuple):
        message, task_name = failed_message
        self.pool.clear()
        self.ui.operation_text_browser.append(message)
        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_url_info_list)} URLs ] | '
            f'Unable to retrieve the full name. It may be due to a connection issue. Click "Go" again.'
        )
        self.ui.go_push_button.setEnabled(True)
        self.ui.clip_push_button.setEnabled(True)
        self.ui.actionLoadClipboardFile.setEnabled(True)

    def handle_parser_completed_signal(self, completed_message: tuple):
        is_model, name_info, task_name = completed_message
        self.progress_bar_info[task_name][2] += 1

        if is_model:
            self.model_name_dict.update(name_info)
        else:
            self.version_name_dict.update(name_info)

        downloaded_count = self.progress_bar_info[task_name][1] + 1
        self.progress_bar_info[task_name][1] = downloaded_count
        self.progress_bar_info[task_name][0].setValue(downloaded_count)

        if self.progress_bar_info[task_name][1] == self.progress_bar_info[task_name][3]:
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | '
                f'Start downloading images'
            )
            self.start_download_image(model_and_version_name=(self.model_name_dict, self.version_name_dict))

    def start_download_image(self, model_and_version_name: tuple):
        self.add_progress_bar(task_name='Downloading', count=len(self.legal_url_info_list))

        for image_info in self.legal_url_info_list:
            downloader = DownloadRunner(httpx_client=self.httpx_client, image_info=image_info, save_dir=self.save_dir,
                                        categorize=self.ui.categorize_check_box.isChecked(),
                                        model_and_version_name=model_and_version_name)
            downloader.signals.download_connect_to_api_failed_signal.connect(
                self.handle_download_connect_to_api_failed_signal)
            downloader.signals.download_completed_signal.connect(self.handle_download_completed_signal)
            self.pool.start(downloader)

    def handle_download_connect_to_api_failed_signal(self, failed_message: tuple):
        original_url, message, task_name = failed_message
        self.download_failed_original_url_list.append(original_url)
        self.progress_bar_info[task_name][2] += 1
        self.operation_browser_insert_html(
            '<span style="color: pink;">'
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_url_info_list)} URLs ] | '
            f'{message}'
            '</span>'
        )
        self.handle_download_task(task_name)

    def handle_download_completed_signal(self, completed_message: tuple):
        original_url, message, task_name = completed_message
        self.progress_bar_info[task_name][2] += 1
        downloaded_count = self.progress_bar_info[task_name][1] + 1
        self.progress_bar_info[task_name][1] = downloaded_count
        self.progress_bar_info[task_name][0].setValue(downloaded_count)

        self.handle_download_task(task_name)

    def handle_download_task(self, task_name):
        if self.progress_bar_info[task_name][2] == self.progress_bar_info[task_name][3]:
            self.operation_browser_insert_html(
                '<span style="color: green;">'
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | '
                f'All download tasks is finished. Clear the record list.'
                '</span>'
            )
            if self.progress_bar_info[task_name][1] != self.progress_bar_info[task_name][3]:
                self.operation_browser_insert_html(
                    '<span style="color: pink;">'
                    f'{datetime.now().strftime("%H:%M:%S")} '
                    f'[ {len(self.legal_url_info_list)} URLs ] | '
                    f'But, {self.progress_bar_info[task_name][2] - self.progress_bar_info[task_name][1]} '
                    f'failed downloads for URLs. Check them at Option > Show Failed URLs'
                    '</span>'
                )
            self.legal_url_info_list.clear()
            self.able_buttons_and_checkbox()

    def add_progress_bar(self, task_name: str, count: int) -> None:
        """
        Create a QLabel and QProgressBar (both within a QHBoxLayout)
        """
        self.progress_bar_list.append(task_name)

        progress_layout = QHBoxLayout()
        progress_label = QLabel(task_name)
        progress_bar = QProgressBar(maximum=count)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(progress_bar)
        progress_layout.setStretch(0, 1)
        progress_layout.setStretch(1, 5)

        # about progress_bar_info:
        # {'Preprocessing': [ProgressBar widget, Downloaded, Executed, Quantity of all task, ProgressBar Layout], ... }
        self.progress_bar_info[task_name] = [progress_bar, 0, 0, count, progress_layout]
        self.ui.verticalLayout.addLayout(progress_layout)

    def able_buttons_and_checkbox(self, enable=True) -> None:
        """
        Enable/Disable clip, go buttons and civitai, categorize checkboxs and loadClipboardFile action
        :param enable: set False to disable them
        :return:
        """
        self.ui.clip_push_button.setEnabled(enable)
        self.ui.go_push_button.setEnabled(enable)
        self.ui.civitai_check_box.setEnabled(enable)
        self.ui.categorize_check_box.setEnabled(enable)

    def able_option_action(self, enable=True) -> None:
        """
        Enable/Disable LoadClipboardFile and ShowFailUrl actions
        :param enable: set False to disable them
        :return:
        """
        self.ui.actionLoadClipboardFile.setEnabled(enable)
        self.ui.actionShowFailUrl.setEnabled(enable)

    def operation_browser_insert_html(self, html_string: str, newline_first=True):
        if newline_first:
            self.ui.operation_text_browser.append('')
        self.ui.operation_text_browser.insertHtml(html_string)
        self.ui.operation_text_browser.setCurrentCharFormat(QTextCharFormat())

    def clear_progress_bar(self) -> None:
        """
        Clear all progress bar layout
        """
        for progress_name in self.progress_bar_list:
            each_progres_bar_info = self.progress_bar_info[progress_name]
            layout = each_progres_bar_info[4]
            self.clear_layout_widgets(layout)

        self.progress_bar_list.clear()
        self.progress_bar_info.clear()

    def clear_layout_widgets(self, layout) -> None:
        """
        Clears all widgets within a layout, including sub-layouts.
        """
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout_widgets(item.layout())

    def closeEvent(self, event) -> None:
        if self.legal_url_info_list:
            reply = QMessageBox.question(self, 'Warning',
                                         'Do you want to save the URL of the clipboard before exiting？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                record = (self.ui.civitai_check_box.isChecked(),
                          self.ui.categorize_check_box.isChecked(),
                          self.legal_url_info_list,
                          )
                with open(f'{datetime.now().strftime("%m-%d-%H:%M:%S")}.bringmeimage', 'wb') as f:
                    pickle.dump(record, f)

            event.accept()
        event.accept()

    def clear_threadpool(self):
        self.pool.clear()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    if sys.platform == 'darwin' and 'Fusion' in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create('Fusion'))
    window.show()
    app.aboutToQuit.connect(window.clear_threadpool)
    sys.exit(app.exec())