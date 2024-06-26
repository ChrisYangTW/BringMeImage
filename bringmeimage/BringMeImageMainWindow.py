import contextlib
import pickle
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import sys
import subprocess

import httpx
from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from PySide6.QtCore import Qt, QThreadPool, QEvent, Signal, Slot
from PySide6.QtGui import QTextCharFormat, QMouseEvent
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QHBoxLayout, QLabel, QProgressBar, QApplication

from bringmeimage.BringMeImage_UI import Ui_MainWindow
from bringmeimage.StartClipWindow import StartClipWindow
from bringmeimage.LoginWindow import LoginWindow
from bringmeimage.ActionWindow import FailedUrlsWindow
from bringmeimage.ParserAndDownloader import ImageUrlParserRunner, VersionIdParserRunner, DownloadRunner
from bringmeimage.BringMeImageData import ImageData

Main_Path: Path = Path(__file__).parent
Cookie_File = Main_Path / 'cookie' / 'cookies.pickle'
Check_Url = r'https://civitai.com/models/10364/innies-better-vulva'
Check_Title = r'Innies: Better vulva - v1.1 | Stable Diffusion LoRA | Civitai'


@dataclass(slots=True)
class ProgressBarData:
    progress_layout: QHBoxLayout
    progress_bar_widget: QProgressBar
    completed: int
    executed: int
    quantity: int


class MainWindow(QMainWindow):
    Manual_Login_OK_Signal = Signal()

    def __init__(self) -> None:
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.pool = QThreadPool.globalInstance()
        self.httpx_client = httpx.Client()
        self.driver_temp: WebDriver | None = None
        self.driver_for_civitai: WebDriver | None = None
        self.origin_google_chrome_pid: set = set()
        self.google_chrome_pid: set = set()
        self.origin_chromedriver_pid: set = set()
        self.chromedriver_pid: set = set()

        self.save_dir: Path = Main_Path.parent / 'DownloadTemp'
        if not self.save_dir.exists():
            self.save_dir.mkdir(parents=True)
        self.ui.folder_line_edit.setText(str(self.save_dir))
        self.legal_urls: dict = {}
        self.process_failed_urls: dict = {}
        self.version_id_info: dict = {}

        self.progress_bar_task_name_list = []
        self.progress_bar_data_dict = {}

        self.ui.actionLoadClipboardFile.triggered.connect(self.load_clipboard_file)
        self.ui.actionShowFailUrl.triggered.connect(self.show_failed_url)
        self.ui.actionSaveTheRecord.triggered.connect(self.save_the_record)
        self.ui.folder_line_edit.mousePressEvent = self.select_storage_folder
        self.ui.civitai_check_box.clicked.connect(self.click_civitai_check_box)
        self.ui.categorize_check_box.clicked.connect(self.click_categorize_check_box)
        self.ui.login_label.setStyleSheet('color: red;')
        self.ui.login_label.mousePressEvent = self.click_login_label
        self.ui.clear_push_button.clicked.connect(self.click_clear_push_button)
        self.ui.clip_push_button.clicked.connect(self.start_clip_process)
        self.ui.go_push_button.clicked.connect(self.click_go_push_button)

    def load_clipboard_file(self) -> None:
        """
        Read the *.bringmeimage file (pickle) and load the corresponding configuration
        :return:
        """
        if self.legal_urls or self.process_failed_urls:
            reply = QMessageBox.question(self, 'Warning',
                                         'Loading the file will clear any record, execute it?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        filter_str = 'Bring Me Image Files (*.bringmeimage)'
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select File', '', filter_str, options=QFileDialog.ReadOnly)
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    record = pickle.load(f)
            except pickle.UnpicklingError:
                self.operation_browser_insert_html(
                    color='pink',
                    string='The file appears to have been modified and is no longer readable',
                    prefix=True
                )
            else:
                self.legal_urls.clear()
                self.process_failed_urls.clear()
                self.clear_progress_bar()
                filename = file_path.rsplit('/', maxsplit=1)[-1]
                self.process_the_record(filename, record)

    def process_the_record(self, filename: str, record: tuple[Path, bool, bool, dict]) -> None:
        self.operation_browser_insert_html(
            color='cyan',
            string=f'Loading clipboard from "{filename}"',
            prefix=True
        )

        save_dir, civitai_is_checked, categorize_is_checked, legal_urls = record
        self.save_dir = save_dir
        self.ui.folder_line_edit.setText(str(save_dir))
        self.ui.civitai_check_box.setChecked(civitai_is_checked)
        self.ui.civitai_check_box.setEnabled(False)
        self.ui.categorize_check_box.setChecked(categorize_is_checked)
        self.ui.categorize_check_box.setEnabled(False)
        self.legal_urls = legal_urls

        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_urls)} URLs ] | Click "GO" to start downloading'
            f' or "Clip" to continue adding.'
        )

    def show_failed_url(self) -> None:
        """
        Pop up a QDialog window displaying the failed download image links
        :return:
        """
        failed_url_window = FailedUrlsWindow(process_failed_url_dict=self.process_failed_urls,
                                             version_id_info_dict=self.version_id_info,
                                             parent=self)
        failed_url_window.setWindowModality(Qt.ApplicationModal)
        failed_url_window.show()

    def save_the_record(self) -> None:
        """
        Save the record without exiting the program
        :return:
        """
        if not self.legal_urls:
            return

        reply = QMessageBox.question(self, 'Warning',
                                     'Do you want to save the URL of the clipboard？'
                                     '(The current records will be cleared after saving)',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        record = (self.save_dir,
                  self.ui.civitai_check_box.isChecked(),
                  self.ui.categorize_check_box.isChecked(),
                  self.legal_urls,
                  )
        with open(f'{datetime.now().strftime("%m-%d-%H:%M:%S")}.bringmeimage', 'wb') as f:
            pickle.dump(record, f)

        self.legal_urls.clear()
        self.freeze_main_window(unfreeze=True)
        self.clear_progress_bar()

        self.operation_browser_insert_html(
            color='cyan',
            string='Save record completed',
            prefix=True
        )

    def select_storage_folder(self, event: QMouseEvent) -> None:
        """
        Set the path of a folder for saving images
        :return:
        """
        if event.button() == Qt.LeftButton:
            if folder := QFileDialog.getExistingDirectory(self, "Select Folder", options=QFileDialog.ShowDirsOnly):
                self.ui.folder_line_edit.setText(folder)
                self.save_dir = Path(folder)

    def click_civitai_check_box(self, checked: bool) -> None:
        """
        When the "CivitAi" checkbox is checked, the "Categorize" checkbox is automatically checked by default
        :return:
        """
        if checked:
            self.ui.categorize_check_box.setChecked(True)
        else:
            self.ui.categorize_check_box.setChecked(False)

    def click_categorize_check_box(self, checked: bool) -> None:
        """
        The "Categorize" checkbox can only be checked when the "CivitAi" checkbox is selected
        :return:
        """
        if checked and not self.ui.civitai_check_box.isChecked():
            self.ui.categorize_check_box.setChecked(False)

    def click_login_label(self, event) -> None:
        if event.button() == Qt.LeftButton and event.type() == QEvent.MouseButtonDblClick:
            if not self.driver_for_civitai:
                if sys.platform == 'darwin':
                    self.origin_chromedriver_pid.update(self.get_pid(process_name='chromedriver'))
                    self.origin_google_chrome_pid.update(self.get_pid(process_name='GoogleChrome'))

                self.operation_browser_insert_html(
                    color='cyan',
                    string='Wait for set up the browser. (The program may experience a brief freezing)'
                )
                self.freeze_main_window()
                QApplication.processEvents()
                self.driver_for_civitai = self.get_browser_for_civitai()
            else:
                self.operation_browser_insert_html(
                    color='cyan',
                    string='Already logged in.'
                )

    def get_browser_for_civitai(self) -> WebDriver | None:
        """
        Retrieve the browser with successful automatic login, otherwise prompt the user to log in manually
        :return:
        """
        QApplication.processEvents()

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-blink-features=AutomationControlled')
        driver = webdriver.Chrome(options=options)
        driver = self.set_browser_for_civitai(driver)

        if not driver:
            self.manual_login()
            return

        if sys.platform == 'darwin':
            self.chromedriver_pid.update(self.get_pid(process_name='chromedriver'))
            self.google_chrome_pid.update(self.get_pid(process_name='GoogleChrome'))

        self.freeze_main_window(unfreeze=True)
        return driver

    def set_browser_for_civitai(self, driver: WebDriver) -> WebDriver | None:
        """
        Load cookies, update cookies if login authentication is successful
        :param driver:
        :return:
        """
        driver.get('https://civitai.com/')

        with contextlib.suppress(Exception):
            with Cookie_File.open('rb') as f:
                cookies = pickle.load(f)
            for cookie in cookies:
                if cookie['name'] == '__Host-next-auth.csrf-token':
                    continue
                driver.add_cookie(cookie)

            driver.get('https://civitai.com/models')
            driver.get(Check_Url)
            if driver.title == Check_Title:
                cookies: list[dict] = driver.get_cookies()
                with Cookie_File.open('wb') as f:
                    pickle.dump(cookies, f)
                self.ui.login_label.setStyleSheet('color: green;')
                self.operation_browser_insert_html(
                    color='cyan',
                    string='Browser for civitai is already loaded.'
                )
                return driver

    def manual_login(self) -> None:
        """
        Pop up the window for manual login
        :return:
        """
        login_window = LoginWindow(parent=self)
        login_window.Login_Window_Start_Signal.connect(self.handle_login_window_start_signal)
        login_window.Login_Window_Finish_Signal.connect(self.handle_login_window_finish_signal)
        login_window.Login_Window_ReLogin_Signal.connect(self.handle_login_window_relogin_signal)
        login_window.Login_Window_Reject_Signal.connect(self.handle_login_window_reject_signal)
        self.Manual_Login_OK_Signal.connect(login_window.handle_login_ok)
        login_window.setWindowModality(Qt.ApplicationModal)
        login_window.show()

    @Slot()
    def handle_login_window_start_signal(self) -> None:
        """
        Open the browser for the user to log in manually
        :return:
        """
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        self.driver_temp = webdriver.Chrome(options=options)
        self.driver_temp.get('https://civitai.com')

    @Slot()
    def handle_login_window_finish_signal(self) -> None:
        """
        Save cookies and send a notification to the LoginWindow upon task completion
        :return:
        """
        cookies: list[dict] = self.driver_temp.get_cookies()

        with Cookie_File.open('wb') as f:
            pickle.dump(cookies, f)

        self.driver_temp.quit()
        self.Manual_Login_OK_Signal.emit()

    @Slot()
    def handle_login_window_relogin_signal(self) -> None:
        """
        Re-login for authentication using the newly obtained cookies
        :return:
        """
        self.freeze_main_window()
        QApplication.processEvents()
        self.driver_for_civitai = self.get_browser_for_civitai()
        if not self.driver_for_civitai:
            self.operation_browser_insert_html(
                color='red',
                string='Attempted to re-login but failed authentication.'
            )

    @Slot()
    def handle_login_window_reject_signal(self) -> None:
        """
        If the LoadWindow is closed abnormally, delete the currently created browser instance (if any)
        :return:
        """
        if self.driver_temp:
            self.driver_temp.quit()
        self.freeze_main_window(unfreeze=True)

    def click_clear_push_button(self) -> None:
        """
        After executing "Clip", the checkboxes for "CivitAi" and "Categorize" will be locked.
        Only after executing "Clear" will all records be cleared and the checkboxes unlocked.
        :return:
        """
        reply = QMessageBox.question(self, 'Warning',
                                     'Are you sure you want to initialize? (This will clear the records)',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.legal_urls.clear()
            self.freeze_main_window(unfreeze=True)
            self.clear_progress_bar()
            self.operation_browser_insert_html(
                color='cyan',
                string='Initialize.',
                prefix=True
            )

    def start_clip_process(self) -> None:
        """
        Pop up the "Clip" window and start the clip process
        :return:
        """
        if self.process_failed_urls:
            reply = QMessageBox.question(self, 'Warning',
                                         'Starting "Clip" will clear the failed download record, execute it?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

            self.process_failed_urls.clear()
            self.operation_browser_insert_html(
                color='cyan',
                string='Clear the failed download record',
                prefix=True
            )

        if not self.save_dir:
            QMessageBox.warning(self, 'Warning', 'Set the storage folder first')
            return

        start_clip_window = StartClipWindow(for_civitai=self.ui.civitai_check_box.isChecked(),
                                            legal_url_dict=self.legal_urls,
                                            parent=self)
        start_clip_window.Start_Clip_Close_Window_Signal.connect(self.handle_clip_close_window_signal)
        # Only after this QDialog is closed, the main window can be used again
        start_clip_window.setWindowModality(Qt.ApplicationModal)
        start_clip_window.show()

        # If start_clip_window is set to Qt.WindowStaysOnTopHint, then setWindowModality(Qt.ApplicationModal) will be
        # ineffective, and need to manually freeze the main window.
        self.freeze_main_window()

    def handle_clip_close_window_signal(self, legal_url_dict: dict) -> None:
        """
        Based on the content of legal_url_dict, determine the component corresponding to enable.
        :param legal_url_dict:
        :return:
        """
        if legal_url_dict:
            self.legal_urls = legal_url_dict
            self.freeze_main_window(unfreeze=True)
            self.ui.civitai_check_box.setEnabled(False)
            self.ui.categorize_check_box.setEnabled(False)
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_urls)} URLs ] | Click "GO" to start downloading'
                f' or "Clip" to continue adding.'
            )
        else:
            self.freeze_main_window(unfreeze=True)

    def click_go_push_button(self) -> None:
        """
        If support for civitai.com is not needed, download directly;
        otherwise, execute the analysis of image links first.
        :return:
        """
        if not self.legal_urls:
            self.operation_browser_insert_html(
                color='pink',
                string='There are no URLs in the list',
                prefix=True
            )
            return

        if self.ui.civitai_check_box.isChecked() and not self.driver_for_civitai:
            self.operation_browser_insert_html(
                color='pink',
                string='Login first',
                prefix=True
            )
            return

        self.clear_progress_bar()
        self.freeze_main_window()

        if self.ui.civitai_check_box.isChecked():
            self.get_image_detail_info()
        else:
            self.start_download_image()

    def get_image_detail_info(self) -> None:
        """
        Retrieves the detailed information (real_url and modelVersionId) of the images
        :return:
        """
        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_urls)} URLs ] | '
            f'(Browsing) Waiting to retrieve relevant information for each image.'
        )
        self.add_progress_bar(task_name='Browsing', count=len(self.legal_urls))

        parser = ImageUrlParserRunner(legal_url_dict=self.legal_urls, driver=self.driver_for_civitai)
        parser.signals.ImageUrlParser_Processed_Signal.connect(self.handle_ImageUrlParser_process_signal)
        parser.signals.ImageUrlParser_Completed_Signal.connect(self.handle_ImageUrlParser_completed_signal)
        self.pool.start(parser)

    @Slot()
    def handle_ImageUrlParser_process_signal(self) -> None:
        """
        Update the progress bar regardless of successful parsing
        :return:
        """
        self.update_process_bar(task_name='Browsing', is_completed=True)

    @Slot(tuple)
    def handle_ImageUrlParser_completed_signal(self, result: tuple[dict, dict]) -> None:
        legal_urls, failed_urls = result
        if not legal_urls:
            self.operation_browser_insert_html(
                color='pink',
                string='Unable to resolve any image download links from the provided image URLs.<br>'
                       'Click "Go" to retry or close the main program and save the list. '
                       'You can execute it again once the server responds properly.',
                prefix=True
            )
            return

        if failed_urls:
            self.operation_browser_insert_html(
                color='pink',
                string=f'"There are {len(failed_urls)} links with inaccessible image paths; '
                       f'you can check them later in "Failed URLs"',
                prefix=True
            )
            self.process_failed_urls = failed_urls

        if self.ui.categorize_check_box.isChecked():
            self.get_version_id_info(legal_urls)
        else:
            self.legal_urls = legal_urls
            self.start_download_image()

    def get_version_id_info(self, legal_url_dict: dict) -> None:
        """
        Retrieve the mapping information between version name and model name.
        :return:
        """
        # hint: legal_url_parse_completed_dict = {image_url1: ImageData1(dataclass), image_url2: ImageData2(dataclass),}
        version_id_set = {image_data.modelVersionId for image_data in legal_url_dict.values()}

        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_urls)} URLs ] | '
            f'(Parsing) Waiting to obtain the names of the version and model.'
        )

        self.add_progress_bar(task_name='Parsing', count=len(version_id_set))
        for version_id in version_id_set:
            # avoid repeated parsing of version_id
            if version_id in self.version_id_info:
                self.handle_parsing_task(is_completed=True)
                continue

            parser = VersionIdParserRunner(httpx_client=self.httpx_client, version_id=version_id)
            self.set_signal_and_add_to_pool(parser)

        # updating self.legal_urls for consistent content display
        self.legal_urls = legal_url_dict

    def set_signal_and_add_to_pool(self, parser) -> None:
        parser.signals.VersionIdParser_Failed_Signal.connect(self.handle_VersionIdParser_failed_signal)
        parser.signals.VersionIdParser_Completed_Signal.connect(self.handle_VersionIdParser_completed_signal)
        self.pool.start(parser)

    def handle_VersionIdParser_failed_signal(self) -> None:
        self.handle_parsing_task(is_completed=False)

    def handle_VersionIdParser_completed_signal(self, version_id_info: dict) -> None:
        # hint: version_id_info = {self.version_id: dataclass(version_name, model_id, model_name, creator)}
        self.version_id_info.update(version_id_info)
        self.handle_parsing_task(is_completed=True)

    def handle_parsing_task(self, is_completed: bool):
        progress_bar_data = self.update_process_bar(task_name='Parsing', is_completed=is_completed)
        quantity = progress_bar_data.quantity
        if progress_bar_data.executed == quantity:
            if progress_bar_data.completed != quantity or self.process_failed_urls:
                reply = QMessageBox.question(self, 'Warning',
                                             'Not all images have been fully parsed, but you can still continue '
                                             'downloading the ones that have been parsed. Do you want to proceed?',
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    self.legal_urls.update(self.process_failed_urls)
                    self.process_failed_urls.clear()
                    self.ui.folder_line_edit.setEnabled(True)
                    self.ui.clip_push_button.setEnabled(True)
                    self.ui.go_push_button.setEnabled(True)
                    self.ui.clear_push_button.setEnabled(True)
                    self.ui.operation_text_browser.append(
                        f'{datetime.now().strftime("%H:%M:%S")} '
                        f'[ {len(self.legal_urls)} URLs ] | Click "GO" to start downloading'
                        f' or "Clip" to continue adding.'
                    )
                    return

            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_urls)} URLs ] | '
                f'(Downloading) Start downloading images'
            )
            self.start_download_image()

    def start_download_image(self) -> None:
        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.legal_urls)} URLs ] | '
            f'(Downloading) Start downloading images'
        )
        self.add_progress_bar(task_name='Downloading', count=len(self.legal_urls))

        for image_data in self.legal_urls.values():
            downloader = DownloadRunner(httpx_client=self.httpx_client, image_data=image_data, save_dir=self.save_dir,
                                        categorize=self.ui.categorize_check_box.isChecked(),
                                        version_id_info_dict=self.version_id_info)
            downloader.signals.download_failed_signal.connect(self.handle_download_failed_signal)
            downloader.signals.download_completed_signal.connect(self.handle_download_completed_signal)
            self.pool.start(downloader)

    def handle_download_failed_signal(self, image_data: ImageData) -> None:
        self.process_failed_urls.update({image_data.url: image_data})
        self.handle_download_task(is_completed=False)

    def handle_download_completed_signal(self) -> None:
        self.handle_download_task(is_completed=True)

    def handle_download_task(self, is_completed: bool) -> None:
        progress_bar_info = self.update_process_bar(task_name='Downloading', is_completed=is_completed)
        if progress_bar_info.executed == progress_bar_info.quantity:
            progress_bar_info.progress_bar_widget.setStyleSheet("""
                QProgressBar {
                    text-align: center;
                }
                QProgressBar::chunk {
                   background-color: green; 
                }
            """)
            self.operation_browser_insert_html(
                color='green',
                string='All download tasks is finished.',
                prefix=True
            )

            if progress_bar_info.completed != progress_bar_info.quantity:
                progress_bar_info.progress_bar_widget.setStyleSheet("""
                    QProgressBar {
                        text-align: center;
                        color: red;
                    }
                    QProgressBar::chunk {
                       background-color: pink; 
                    }
                """)
                if progress_bar_info.completed == 0:
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
                    color='red',
                    string=f'But, {progress_bar_info.executed - progress_bar_info.completed} '
                           'failed downloads for URLs. Check them at Option > Show Failed URLs',
                    prefix=True
                )

            self.legal_urls.clear()
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.legal_urls)} URLs ] | Clear the record list'
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

        self.progress_bar_data_dict[task_name] = ProgressBarData(progress_layout=progress_layout,
                                                                 progress_bar_widget=progress_bar,
                                                                 completed=0,
                                                                 executed=0,
                                                                 quantity=count)
        self.ui.verticalLayout.addLayout(progress_layout)

    def update_process_bar(self, task_name: str, is_completed: bool) -> ProgressBarData:
        """
        Updating progress bar information.
        :param task_name: progress bar task name
        :param is_completed: set to True, it will synchronously update the 'completed' attribute of the ProgressBarData.
        :return: ProgressBarData
        """
        progress_bar_data: ProgressBarData = self.progress_bar_data_dict[task_name]
        progress_bar_data.executed += 1
        if is_completed:
            completed_count = progress_bar_data.completed + 1
            progress_bar_data.completed = completed_count
            progress_bar_data.progress_bar_widget.setValue(completed_count)

        return progress_bar_data

    def freeze_main_window(self, unfreeze=False) -> None:
        """
        Freeze all buttons and options in the main window
        :param unfreeze: set True to unfreeze all
        :return:
        """
        self.ui.folder_line_edit.setEnabled(unfreeze)
        self.ui.login_label.setEnabled(unfreeze)
        self.ui.clip_push_button.setEnabled(unfreeze)
        self.ui.go_push_button.setEnabled(unfreeze)
        self.ui.civitai_check_box.setEnabled(unfreeze)
        self.ui.categorize_check_box.setEnabled(unfreeze)
        self.ui.clear_push_button.setEnabled(unfreeze)
        self.able_option_action(unfreeze)

    def able_option_action(self, enable=True) -> None:
        """
        Enable/Disable LoadClipboardFile, ShowFailUrl and  SaveTheRecord actions
        :param enable: set False to disable them
        :return:
        """
        self.ui.actionLoadClipboardFile.setEnabled(enable)
        self.ui.actionShowFailUrl.setEnabled(enable)
        self.ui.actionSaveTheRecord.setEnabled(enable)

    def operation_browser_insert_html(self, color: str, string: str, prefix: bool = False) -> None:
        """
        Using HTML syntax in self.ui.operation_text_browser
        :param string:
        :param color:
        :param prefix:
        :return:
        """
        prefix_string = f'{datetime.now().strftime("%H:%M:%S")} [ {len(self.legal_urls)} URLs ] | ' if prefix else ''
        full_string = f'<span style="color: {color};">{prefix_string}{string}</span>'
        self.ui.operation_text_browser.append('')
        self.ui.operation_text_browser.insertHtml(full_string)
        self.ui.operation_text_browser.setCurrentCharFormat(QTextCharFormat())

    def clear_progress_bar(self) -> None:
        """
        Clear all progress bar layout
        """
        for progress_name in self.progress_bar_task_name_list:
            each_progres_bar_info: ProgressBarData = self.progress_bar_data_dict[progress_name]
            layout = each_progres_bar_info.progress_layout
            self.clear_layout_widgets(layout)

        self.progress_bar_task_name_list.clear()
        self.progress_bar_data_dict.clear()

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

    def get_pid(self, process_name: str) -> list:
        pid: list = []
        paser = re.compile(r'^\S*\s+(\d+)\s+')

        if process_name == 'GoogleChrome':
            command = "ps aux | grep '[M]acOS/Google Chrome [^H]'"
        elif process_name == 'chromedriver':
            command = "ps aux | grep '[c]hromedriver.*chromedriver'"
        else:
            raise AssertionError('process_name must be either GoogleChrome or chromedriver')

        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stdout:
            for result in result.stdout.splitlines():
                match = paser.match(result)
                if match:
                    pid.append(match.group(1))

        return pid

    def clear_chromedriver_process(self) -> None:
        for chromedriver_pid in self.chromedriver_pid:
            subprocess.run(f'kill -TERM {chromedriver_pid}', shell=True)
        for google_chrome_pid in self.google_chrome_pid:
            subprocess.run(f'kill -TERM {google_chrome_pid}', shell=True)

    def closeEvent(self, event) -> None:
        """
        If self.legal_url_info_list is not empty, before closing the window, ask if you want to save it
        :param event:
        :return:
        """
        if self.legal_urls:
            reply = QMessageBox.question(self, 'Warning',
                                         'Do you want to save the URL of the clipboard before exiting？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                record = (self.save_dir,
                          self.ui.civitai_check_box.isChecked(),
                          self.ui.categorize_check_box.isChecked(),
                          self.legal_urls,
                          )
                with open(f'{datetime.now().strftime("%m-%d-%H:%M:%S")}.bringmeimage', 'wb') as f:
                    pickle.dump(record, f)

        if sys.platform == 'darwin':
            self.clear_chromedriver_process()
        event.accept()
