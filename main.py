import sys
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import httpx

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QTextCharFormat, QMouseEvent
from PySide6.QtWidgets import (QApplication, QMainWindow, QStyleFactory, QFileDialog, QMessageBox, QHBoxLayout,
                               QLabel, QProgressBar)

from bringmeimage.bringmeimage_main import Ui_MainWindow
from bringmeimage.StartClipWindow import StartClipWindow
from bringmeimage.ActionWindow import FailedUrlsWindow
from bringmeimage.ParserAndDownloader import ParserRunner, DownloadRunner


@dataclass
class ProgressBarInfo:
    progress_layout: QHBoxLayout
    progress_bar_widget: QProgressBar
    downloaded: int
    executed: int
    quantity_of_all_task: int


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.pool = QThreadPool.globalInstance()
        self.httpx_client = httpx.Client()

        self.save_dir = None
        self.legal_url_info_list = []
        self.temp_url_info_list = []
        self.download_failed_url_info_list = []
        self.version_count = 0
        self.version_id_info_dict = {}

        self.progress_bar_task_name_list = []
        self.progress_bar_info_dict = {}

        self.ui.actionLoadClipboardFile.triggered.connect(self.load_clipboard_file)
        self.ui.actionShowFailUrl.triggered.connect(self.show_failed_url)
        self.ui.actionSaveTheRecord.triggered.connect(self.save_the_record)
        self.ui.folder_line_edit.mousePressEvent = self.select_storage_folder
        self.ui.civitai_check_box.clicked.connect(self.click_civitai_check_box)
        self.ui.categorize_check_box.clicked.connect(self.click_categorize_check_box)
        self.ui.clear_push_button.clicked.connect(self.click_clear_push_button)
        self.ui.clip_push_button.clicked.connect(self.start_clip_process)
        self.ui.go_push_button.clicked.connect(self.click_go_push_button)

    def load_clipboard_file(self) -> None:
        """
        Read the *.bringmeimage file (pickle) and load the corresponding configuration
        """
        if self.download_failed_url_info_list:
            reply = QMessageBox.question(self, 'Warning',
                                         'Loading the file will clear the failed download record, execute it?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            else:
                self.download_failed_url_info_list.clear()

        filter_str = 'Bring Me Image Files (*.bringmeimage)'
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select File', '', filter_str, options=QFileDialog.ReadOnly)
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    record = pickle.load(f)
            except pickle.UnpicklingError:
                self.operation_browser_insert_html(
                    '<span style="color: pink;">'
                    f'{datetime.now().strftime("%H:%M:%S")} '
                    f'[ {len(self.legal_url_info_list)} URLs ] | '
                    f'The file appears to have been modified and is no longer readable'
                    '</span>'
                )
            else:
                filename = file_path.rsplit('/', maxsplit=1)[-1]
                self.process_the_record(filename, record)

    def process_the_record(self, filename: str, record: tuple) -> None:
        self.operation_browser_insert_html(
            '<span style="color: cyan;">'
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_url_info_list)} URLs ] | Loading clipboard from "{filename}"'
            '</span>'
        )

        save_dir_path, civitai_check_box, categorize_check_box, legal_url_info_list = record
        self.save_dir = save_dir_path
        self.ui.folder_line_edit.setText(str(save_dir_path))
        self.ui.civitai_check_box.setChecked(civitai_check_box)
        self.ui.civitai_check_box.setEnabled(False)
        self.ui.categorize_check_box.setChecked(categorize_check_box)
        self.ui.categorize_check_box.setEnabled(False)
        self.legal_url_info_list = legal_url_info_list

        self.ui.actionLoadClipboardFile.setEnabled(False)
        self.ui.actionShowFailUrl.setEnabled(False)
        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_url_info_list)} URLs ] | Click "GO" to start downloading'
            f' or "Clip" to continue adding.'
        )

    def show_failed_url(self) -> None:
        """
        Pop up a QDialog window displaying the failed download image links
        """
        self.download_failed_url_info_list = list(set(self.download_failed_url_info_list))
        failed_url_window = FailedUrlsWindow(failed_urls=self.download_failed_url_info_list, parent=self)
        failed_url_window.setWindowModality(Qt.ApplicationModal)
        failed_url_window.show()

    def save_the_record(self) -> None:
        """
        Save the record without exiting the program
        """
        if self.legal_url_info_list:
            reply = QMessageBox.question(self, 'Warning',
                                         'Do you want to save the URL of the clipboard？'
                                         '(The current records will be cleared after saving)',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                record = (self.save_dir,
                          self.ui.civitai_check_box.isChecked(),
                          self.ui.categorize_check_box.isChecked(),
                          self.legal_url_info_list,
                          )

                with open(f'{datetime.now().strftime("%m-%d-%H:%M:%S")}.bringmeimage', 'wb') as f:
                    pickle.dump(record, f)

                self.legal_url_info_list.clear()
                self.freeze_main_window(unfreeze=True)
                self.clear_progress_bar()

                self.operation_browser_insert_html(
                    '<span style="color: cyan;">'
                    f'{datetime.now().strftime("%H:%M:%S")} '
                    f'[ {len(self.legal_url_info_list)} URLs ] | Save record completed'
                    '</span>'
                )

    def select_storage_folder(self, event: QMouseEvent) -> None:
        """
        Set the path of a folder for saving images
        """
        if event.button() == Qt.LeftButton:
            if folder_path := QFileDialog.getExistingDirectory(self, "Select Folder", options=QFileDialog.ShowDirsOnly):
                self.ui.folder_line_edit.setText(folder_path)
                self.save_dir = Path(folder_path)

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

    def click_clear_push_button(self) -> None:
        """
        Initialize the program. After executing "Clip", the checkboxes for "CivitAi" and "Categorize" will be locked.
        Only after executing "Clear" will all records be cleared and the checkboxes unlocked.
        """
        reply = QMessageBox.question(self, 'Warning',
                                     'Are you sure you want to initialize? (This will clear the records)',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.legal_url_info_list.clear()
            self.freeze_main_window(unfreeze=True)
            self.clear_progress_bar()
            self.operation_browser_insert_html(
                '<span style="color: cyan;">'
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | Initialize'
                '</span>'
            )

    def start_clip_process(self) -> None:
        """
        Pop up the "Clip" window and start the clip process
        """
        if self.download_failed_url_info_list:
            reply = QMessageBox.question(self, 'Warning',
                                         'Starting "Clip" will clear the failed download record, execute it?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

            self.download_failed_url_info_list.clear()
            self.operation_browser_insert_html(
                '<span style="color: cyan;">'
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | Clear the failed download record'
                '</span>'
            )

        if not self.save_dir:
            QMessageBox.warning(self, 'Warning', 'Set the storage folder first')
            return

        start_clip_window = StartClipWindow(for_civitai=self.ui.civitai_check_box.isChecked(),
                                            legal_url_info_list=self.legal_url_info_list,
                                            parent=self)
        start_clip_window.Start_Clip_Closed_Window_Signal.connect(self.handle_clip_closed_window_signal)
        # Only after this QDialog is closed, the main window can be used again
        start_clip_window.setWindowModality(Qt.ApplicationModal)
        start_clip_window.show()

        # If start_clip_window is set to Qt.WindowStaysOnTopHint, then setWindowModality(Qt.ApplicationModal) will be
        # ineffective, and need to manually freeze the main window.
        self.freeze_main_window()

    def handle_clip_closed_window_signal(self, legal_url_info_list: list) -> None:
        if legal_url_info_list:
            self.legal_url_info_list = legal_url_info_list
            self.ui.folder_line_edit.setEnabled(True)
            self.ui.clip_push_button.setEnabled(True)
            self.ui.go_push_button.setEnabled(True)
            self.ui.clear_push_button.setEnabled(True)
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | Click "GO" to start downloading'
                f' or "Clip" to continue adding.'
            )
        else:
            self.freeze_main_window(unfreeze=True)

    def click_go_push_button(self) -> None:
        """
        If support for civitai.com is not needed, download directly;
        otherwise, execute the analysis of model name and version name first.
        """
        if not self.legal_url_info_list:
            self.operation_browser_insert_html(
                '<span style="color: pink;">'
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | There are no URLs in the list'
                '</span>'
            )
            return

        self.clear_progress_bar()
        self.ui.go_push_button.setEnabled(False)

        if self.ui.civitai_check_box.isChecked():
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | '
                f'Preprocessing, waiting to retrieve model and version names'
            )
            self.get_version_id_info()
        else:
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | '
                f'Start downloading images'
            )
            self.start_download_image()

    def get_version_id_info(self) -> None:
        """
        Retrieve the mapping information between version name and model name.
        :return:
        """
        # hint: self.legal_url_info_list = [(url_text, (modelVersionId, postId, imageId, params)), ...]
        version_id_set = {image_info[1][0] for image_info in self.legal_url_info_list}
        version_id_set.discard(None)
        self.version_count = len(version_id_set)

        if self.version_count:
            self.add_progress_bar(task_name='Preprocessing', count=self.version_count)
            for version_id in version_id_set:
                parser = ParserRunner(httpx_client=self.httpx_client, version_id=version_id)
                self.set_signal_and_add_to_pool(parser)
        else:
            # links of the form 'https://civitai.com/images/(\d+)\?postId=(\d+)' only"
            self.start_download_image()

    def set_signal_and_add_to_pool(self, parser) -> None:
        parser.signals.Parser_Connect_To_API_Failed_Signal.connect(self.handle_parser_connect_to_api_failed_signal)
        parser.signals.Parser_Completed_Signal.connect(self.handle_parser_completed_signal)
        self.pool.start(parser)

    def handle_parser_connect_to_api_failed_signal(self, failed_message: tuple) -> None:
        message, task_name = failed_message
        self.pool.clear()
        self.ui.operation_text_browser.append(message)
        self.operation_browser_insert_html(
            '<span style="color: pink;">'
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_url_info_list)} URLs ] | '
            f'{message} '
            f'Unable to retrieve the full name. It may be due to a connection issue.<br>'
            f'Click "Go" to retry or close the main program and save the list. '
            f'You can execute it again once the server responds properly.'
            '</span>'
        )
        self.ui.go_push_button.setEnabled(True)

    def handle_parser_completed_signal(self, completed_message: tuple) -> None:
        version_id_info, task_name = completed_message
        # hint: version_id_info = {self.version_id: nametuple(version_name, model_id, model_name, creator)}
        self.version_id_info_dict.update(version_id_info)

        progress_bar_info: ProgressBarInfo = self.progress_bar_info_dict[task_name]
        progress_bar_info.executed += 1
        downloaded_count = progress_bar_info.downloaded + 1
        progress_bar_info.downloaded = downloaded_count
        progress_bar_info.progress_bar_widget.setValue(downloaded_count)

        if progress_bar_info.downloaded == progress_bar_info.quantity_of_all_task:
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | '
                f'Start downloading images'
            )
            self.start_download_image(version_id_info_dict=self.version_id_info_dict)

    def start_download_image(self, version_id_info_dict: dict | None = None) -> None:
        self.add_progress_bar(task_name='Downloading', count=len(self.legal_url_info_list))

        for image_info in self.legal_url_info_list:
            downloader = DownloadRunner(httpx_client=self.httpx_client, image_info=image_info, save_dir=self.save_dir,
                                        categorize=self.ui.categorize_check_box.isChecked(),
                                        version_id_info_dict=version_id_info_dict)
            downloader.signals.download_failed_signal.connect(
                self.handle_download_failed_signal)
            downloader.signals.download_completed_signal.connect(self.handle_download_completed_signal)
            self.pool.start(downloader)

    def handle_download_failed_signal(self, failed_message: tuple) -> None:
        original_url, model_name, version_name, message, task_name, image_params = failed_message

        self.download_failed_url_info_list.append((original_url, model_name, version_name))
        self.temp_url_info_list.append((original_url, image_params))

        progress_bar_info: ProgressBarInfo = self.progress_bar_info_dict[task_name]
        progress_bar_info.executed += 1

        self.handle_download_task(task_name)

    def handle_download_completed_signal(self, completed_message: tuple) -> None:
        original_url, message, task_name = completed_message

        progress_bar_info: ProgressBarInfo = self.progress_bar_info_dict[task_name]
        progress_bar_info.executed += 1
        downloaded_count = progress_bar_info.downloaded + 1
        progress_bar_info.downloaded = downloaded_count
        progress_bar_info.progress_bar_widget.setValue(downloaded_count)

        self.handle_download_task(task_name)

    def handle_download_task(self, task_name) -> None:
        progress_bar_info: ProgressBarInfo = self.progress_bar_info_dict[task_name]
        if progress_bar_info.executed == progress_bar_info.quantity_of_all_task:
            progress_bar_info.progress_bar_widget.setStyleSheet("""
                QProgressBar {
                    text-align: center;
                }
                QProgressBar::chunk {
                   background-color: green; 
                }
            """)
            self.operation_browser_insert_html(
                '<span style="color: green;">'
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | '
                f'All download tasks is finished.'
                '</span>'
            )

            if progress_bar_info.downloaded != progress_bar_info.quantity_of_all_task:
                progress_bar_info.progress_bar_widget.setStyleSheet("""
                    QProgressBar {
                        text-align: center;
                        color: red;
                    }
                    QProgressBar::chunk {
                       background-color: pink; 
                    }
                """)
                if progress_bar_info.downloaded == 0:
                    # If the progress is 0, there won't be a visible progress bar.
                    # Therefore, the progress bar object's background needs to be set directly.
                    progress_bar_info.progress_bar_widget.setStyleSheet("""
                        QProgressBar {
                            text-align: center;
                            color: red;
                            background-color: pink;
                        }
                    """)
                self.operation_browser_insert_html(
                    '<span style="color: red;">'
                    f'{datetime.now().strftime("%H:%M:%S")} '
                    f'[ {len(self.legal_url_info_list)} URLs ] | '
                    f'But, {progress_bar_info.executed - progress_bar_info.downloaded} '
                    f'failed downloads for URLs. Check them at Option > Show Failed URLs'
                    f'Or click "go" to try again'
                    '</span>'
                )
                self.legal_url_info_list = self.temp_url_info_list[:]
                self.temp_url_info_list.clear()
                self.ui.actionShowFailUrl.setEnabled(True)
                self.ui.clip_push_button.setEnabled(True)
                self.ui.go_push_button.setEnabled(True)
                self.ui.operation_text_browser.append(
                    f'{datetime.now().strftime("%H:%M:%S")} '
                    f'[ {len(self.legal_url_info_list)} URLs ] | Click "GO" to start downloading'
                    f' or "Clip" to continue adding.'
                )
                return

            self.legal_url_info_list.clear()
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_url_info_list)} URLs ] | Clear the record list'
            )
            self.freeze_main_window(unfreeze=True)

    def add_progress_bar(self, task_name: str, count: int) -> None:
        """
        Create a QLabel and QProgressBar (both within a QHBoxLayout)
        """
        # hint:
        # progressBar.setStyleSheet("""
        #     QProgressBar::chunk {
        #         background-color: green; /* set bar color */
        #     }
        #     QProgressBar {
        #         color: green; /* set bar text color */
        #         background-color: pink;  /* set bar background color */
        #         text-align: center;
        #         /* During testing, adding the QProgressBar::chunk style caused the text to no longer be centered,
        #         so I set the text-align property.*/
        #     }
        # """)

        self.progress_bar_task_name_list.append(task_name)

        progress_layout = QHBoxLayout()
        progress_label = QLabel(task_name)
        progress_bar = QProgressBar(maximum=count)
        progress_bar.setFormat("%v / %m (%p%)")
        progress_bar.setValue(0)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(progress_bar)
        progress_layout.setStretch(0, 1)
        progress_layout.setStretch(1, 5)

        self.progress_bar_info_dict[task_name] = ProgressBarInfo(progress_layout=progress_layout,
                                                                 progress_bar_widget=progress_bar,
                                                                 downloaded=0,
                                                                 executed=0,
                                                                 quantity_of_all_task=count)
        self.ui.verticalLayout.addLayout(progress_layout)

    def freeze_main_window(self, unfreeze=False) -> None:
        """
        Freeze all buttons and options in the main window
        :param unfreeze: set True to unfreeze all
        :return:
        """
        self.ui.folder_line_edit.setEnabled(unfreeze)
        self.ui.clip_push_button.setEnabled(unfreeze)
        self.ui.go_push_button.setEnabled(unfreeze)
        self.ui.civitai_check_box.setEnabled(unfreeze)
        self.ui.categorize_check_box.setEnabled(unfreeze)
        self.ui.clear_push_button.setEnabled(unfreeze)
        self.able_option_action(unfreeze)

    def able_option_action(self, enable=True) -> None:
        """
        Enable/Disable LoadClipboardFile and ShowFailUrl actions
        :param enable: set False to disable them
        :return:
        """
        self.ui.actionLoadClipboardFile.setEnabled(enable)
        self.ui.actionShowFailUrl.setEnabled(enable)

    def operation_browser_insert_html(self, html_string: str, newline_first=True) -> None:
        """
        Using HTML syntax in self.ui.operation_text_browser
        :param html_string:
        :param newline_first:
        :return:
        """
        if newline_first:
            self.ui.operation_text_browser.append('')
        self.ui.operation_text_browser.insertHtml(html_string)
        self.ui.operation_text_browser.setCurrentCharFormat(QTextCharFormat())

    def clear_progress_bar(self) -> None:
        """
        Clear all progress bar layout
        """
        for progress_name in self.progress_bar_task_name_list:
            each_progres_bar_info: ProgressBarInfo = self.progress_bar_info_dict[progress_name]
            layout = each_progres_bar_info.progress_layout
            self.clear_layout_widgets(layout)

        self.progress_bar_task_name_list.clear()
        self.progress_bar_info_dict.clear()

    def clear_layout_widgets(self, layout) -> None:
        """
        Clears all widgets within a layout, including sub-layouts
        """
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout_widgets(item.layout())

    def closeEvent(self, event) -> None:
        """
        If self.legal_url_info_list is not empty, before closing the window, ask if you want to save it
        :param event:
        :return:
        """
        if self.legal_url_info_list:
            reply = QMessageBox.question(self, 'Warning',
                                         'Do you want to save the URL of the clipboard before exiting？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                record = (self.save_dir,
                          self.ui.civitai_check_box.isChecked(),
                          self.ui.categorize_check_box.isChecked(),
                          self.legal_url_info_list,
                          )
                with open(f'{datetime.now().strftime("%m-%d-%H:%M:%S")}.bringmeimage', 'wb') as f:
                    pickle.dump(record, f)

        event.accept()

    def clear_threadpool(self) -> None:
        """
        Clear the global thread pool to ensure all tasks are cancelled before the application exits
        """
        self.pool.clear()


if __name__ == '__main__':
    app = QApplication([])
    if sys.platform == 'darwin' and 'Fusion' in QStyleFactory.keys():
        app.setStyle(QStyleFactory.create('Fusion'))

    window = MainWindow()
    window.show()
    app.aboutToQuit.connect(window.clear_threadpool)
    sys.exit(app.exec())
