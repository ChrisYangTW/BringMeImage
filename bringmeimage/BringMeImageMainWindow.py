import contextlib
import json
import pickle
from datetime import datetime
from pathlib import Path

import httpx
from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import BrowserContext, Page
from PySide6.QtCore import Qt, QThreadPool, QEvent, Signal, Slot
from PySide6.QtGui import QTextCharFormat, QMouseEvent
from PySide6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QHBoxLayout, QLabel, QProgressBar, QApplication

from bringmeimage.BringMeImage_UI import Ui_MainWindow
from bringmeimage.StartClipWindow import StartClipWindow
from bringmeimage.LoginWindow import LoginWindow
from bringmeimage.ActionWindow import FailedUrlsWindow
from bringmeimage.Downloader import DownloadRunner
from bringmeimage.BringMeImageData import ImageData, ProgressBarData
from bringmeimage.config import Login_Check_Url, Login_Check_Title, Chrome_Path


Main_Path: Path = Path(__file__).parent
Cookie_File: Path = Main_Path / 'cookie' / 'cookies.json'


class MainWindow(QMainWindow):
    Manual_Login_OK_Signal = Signal()

    def __init__(self) -> None:
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.pool = QThreadPool.globalInstance()
        self.httpx_client = httpx.Client()
        self.playwright = None
        self.browser = None
        self.context: BrowserContext | None = None
        self.driver_page: Page | None = None
        self.browser_temp = None
        self.context_temp = None
        self.is_login_civitai: bool = False

        self.save_dir: Path = Main_Path.parent / 'DownloadTemp'
        if not self.save_dir.exists():
            self.save_dir.mkdir(parents=True)
        self.ui.folder_line_edit.setText(str(self.save_dir))
        self.urls: dict[str: ImageData] = {}
        self.urls_parsed: dict[str: ImageData] = {}
        self.urls_failed: dict[str: ImageData] = {}
        self.process_failed_urls: dict = {}

        self.progress_bar_task_name: list = []
        self.progress_bar_data: dict = {}

        self.ui.actionLoadClipboardFile.triggered.connect(self.load_clipboard_file)
        self.ui.actionShowFailUrl.triggered.connect(self.show_failed_url)
        self.ui.actionSaveTheRecord.triggered.connect(self.save_the_record)
        self.ui.folder_line_edit.mousePressEvent = self.select_storage_folder
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
        if self.urls or self.process_failed_urls:
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
                self.urls.clear()
                self.process_failed_urls.clear()
                self.clear_progress_bar()
                filename = file_path.rsplit('/', maxsplit=1)[-1]
                self.process_the_record(filename, record)

    def process_the_record(self, filename: str, record: tuple[Path, bool, dict]) -> None:
        self.operation_browser_insert_html(
            color='cyan',
            string=f'Loading clipboard from "{filename}"',
            prefix=True
        )

        save_dir, civitai_is_checked, urls = record
        self.save_dir = save_dir
        self.ui.folder_line_edit.setText(str(save_dir))
        self.ui.civitai_check_box.setChecked(civitai_is_checked)
        self.ui.civitai_check_box.setEnabled(False)
        self.urls = urls

        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.urls)} URLs ] | Click "GO" to start downloading'
            f' or "Clip" to continue adding.'
        )

    def show_failed_url(self) -> None:
        """
        Pop up a QDialog window displaying the failed download image links
        :return:
        """
        failed_url_window = FailedUrlsWindow(process_failed_url_dict=self.process_failed_urls,
                                             parent=self)
        failed_url_window.setWindowModality(Qt.ApplicationModal)
        failed_url_window.show()

    def save_the_record(self) -> None:
        """
        Save the record without exiting the program
        :return:
        """
        if not self.urls:
            return

        reply = QMessageBox.question(self, 'Warning',
                                     'Do you want to save the URL of the clipboard？'
                                     '(The current records will be cleared after saving)',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        record = (self.save_dir,
                  self.ui.civitai_check_box.isChecked(),
                  self.urls,
                  )
        with open(f'{datetime.now().strftime("%m-%d-%H:%M:%S")}.bringmeimage', 'wb') as f:
            pickle.dump(record, f)

        self.urls.clear()
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

    def click_login_label(self, event) -> None:
        if event.button() == Qt.LeftButton and event.type() == QEvent.MouseButtonDblClick:
            if not self.driver_page:
                self.operation_browser_insert_html(
                    color='cyan',
                    string='Wait for set up the browser. (The program may experience a brief freezing)'
                )
                self.freeze_main_window()
                self.driver_page = self.get_browser_page_for_civitai()
            else:
                self.operation_browser_insert_html(
                    color='cyan',
                    string='Already logged in.'
                )

    def get_browser_page_for_civitai(self) -> Page | None:
        """
        Retrieve the browser page with successful automatic login, otherwise prompt the user to log in manually
        :return:
        """
        QApplication.processEvents()
        if not self.playwright:
            self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(executable_path=Chrome_Path,
                                                       headless=True,
                                                       args=['--disable-blink-features=AutomationControlled'])
        self.context = self.browser.new_context()
        driver_page = self.set_browser_for_civitai()

        if not driver_page:
            self.context.close()
            self.browser.close()
            self.manual_login()
            return

        self.freeze_main_window(unfreeze=True)
        return driver_page

    def set_browser_for_civitai(self) -> Page | None:
        """
        Load cookies, update cookies if login authentication is successful
        :return:
        """
        with contextlib.suppress(Exception):
            with Cookie_File.open() as f:
                cookies = json.load(f)
                self.context.add_cookies(cookies)

            driver_page = self.context.new_page()
            driver_page.goto('https://civitai.com/', wait_until='domcontentloaded')
            driver_page.goto(Login_Check_Url, wait_until='domcontentloaded')
            if driver_page.title() == Login_Check_Title:
                cookies = self.context.cookies()
                with Cookie_File.open('w') as f:
                    json.dump(cookies, f)
                self.ui.login_label.setStyleSheet('color: green;')
                self.operation_browser_insert_html(
                    color='cyan',
                    string='Browser for civitai is already loaded.'
                )
                self.is_login_civitai = True
                return driver_page

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
        self.browser_temp = self.playwright.chromium.launch(executable_path=Chrome_Path,
                                                            headless=False,
                                                            args=['--disable-blink-features=AutomationControlled'])
        self.context_temp = self.browser_temp.new_context()
        page = self.context_temp.new_page()
        page.goto('https://civitai.com', wait_until="domcontentloaded")

    @Slot()
    def handle_login_window_finish_signal(self) -> None:
        """
        Save cookies and send a notification to the LoginWindow upon task completion
        :return:
        """
        cookies = self.context_temp.cookies()
        with Cookie_File.open('w') as f:
            json.dump(cookies, f)

        self.context_temp.close()
        self.browser_temp.close()

        self.Manual_Login_OK_Signal.emit()

    @Slot()
    def handle_login_window_relogin_signal(self) -> None:
        """
        Re-login for authentication using the newly obtained cookies
        :return:
        """
        self.driver_page = self.get_browser_page_for_civitai()
        if not self.driver_page:
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
        if self.context_temp:
            self.context_temp.close()

        if self.browser_temp:
            self.browser_temp.close()

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
            self.urls.clear()
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

        if self.ui.civitai_check_box.isChecked() and not self.is_login_civitai:
            self.operation_browser_insert_html(
                color='red',
                string='Login before Clip',
                prefix=True
            )
            return

        start_clip_window = StartClipWindow(for_civitai=self.ui.civitai_check_box.isChecked(),
                                            urls=self.urls,
                                            parent=self)
        start_clip_window.Start_Clip_Close_Window_Signal.connect(self.handle_clip_close_window_signal)
        # Only after this QDialog is closed, the main window can be used again
        start_clip_window.setWindowModality(Qt.ApplicationModal)
        start_clip_window.show()

        # If start_clip_window is set to Qt.WindowStaysOnTopHint, then setWindowModality(Qt.ApplicationModal) will be
        # ineffective, and need to manually freeze the main window.
        self.freeze_main_window()

    @Slot(dict)
    def handle_clip_close_window_signal(self, urls: dict) -> None:
        """
        Based on the content of legal_url_dict, determine the component corresponding to enable.
        :param urls:
        :return:
        """
        if urls:
            self.urls = urls
            self.freeze_main_window(unfreeze=True)
            self.ui.civitai_check_box.setEnabled(False)
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.urls)} URLs ] | Click "GO" to start downloading'
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
        if not self.urls:
            self.operation_browser_insert_html(
                color='pink',
                string='There are no URLs in the list',
                prefix=True
            )
            return

        if self.ui.civitai_check_box.isChecked() and not self.driver_page:
            self.operation_browser_insert_html(
                color='pink',
                string='Login first',
                prefix=True
            )
            return

        self.clear_progress_bar()
        self.freeze_main_window()

        if self.ui.civitai_check_box.isChecked():
            self.get_image_info()
        else:
            self.start_download_image()

    def get_image_info(self) -> None:
        """
        Retrieves the detailed information (src) of the images
        :return:
        """
        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.urls)} URLs ] | '
            f'(Browsing) Waiting to retrieve relevant information for each image.'
        )
        self.add_progress_bar(task_name='Browsing', count=len(self.urls))

        for img_url, img_data in self.urls.items():
            if img_data.is_parsed:
                self.urls_parsed[img_url] = img_data
                continue

            img_src = self.parse_image_scr(img_url)
            if img_src:
                img_data.src = img_src
                img_data.is_parsed = True
                self.urls_parsed[img_url] = img_data
            else:
                self.urls_failed[img_url] = img_data

            self.update_process_bar(task_name='Browsing', is_completed=True)
            QApplication.processEvents()
            # todo: process_bar is not correct

        self.image_parse_completed()

    def parse_image_scr(self, img_url: str) -> str:
        # wait DOM
        self.driver_page.goto(img_url, wait_until='domcontentloaded')
        # wait <img>
        self.driver_page.wait_for_selector(selector=".relative.flex.size-full.items-center.justify-center img",
                                           timeout=60000)
        img_src = None
        for i in range(2):
            img_src = self.driver_page.eval_on_selector(
                selector=".relative.flex.size-full.items-center.justify-center img",
                expression="img => img.src")
            if img_src or i:
                break
            self.driver_page.wait_for_timeout(500)  # wait 0.5 second

        return img_src

    def image_parse_completed(self):
        if not self.urls:
            self.operation_browser_insert_html(
                color='pink',
                string='Unable to resolve any image download links from the provided image URLs.<br>'
                       'Click "Go" to retry or close the main program and save the list. '
                       'You can execute it again once the server responds properly.',
                prefix=True
            )
            return

        if self.urls_failed:
            self.operation_browser_insert_html(
                color='pink',
                string=f'"There are {len(self.urls_failed)} links with inaccessible image paths; '
                       f'you can check them later in "Failed URLs"',
                prefix=True
            )
            self.process_failed_urls = self.urls_failed

        QApplication.processEvents()
        self.start_download_image()

    def start_download_image(self) -> None:
        self.ui.operation_text_browser.append(
            f'{datetime.now().strftime("%H:%M:%S")} '
            f'[ {len(self.urls)} URLs ] | '
            f'(Downloading) Start downloading images'
        )
        self.add_progress_bar(task_name='Downloading', count=len(self.urls))

        for img_data in self.urls.values():
            downloader = DownloadRunner(httpx_client=self.httpx_client, image_data=img_data, save_dir=self.save_dir)
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

            self.urls.clear()
            self.ui.operation_text_browser.append(
                f'{datetime.now().strftime("%H:%M:%S")} '
                f'[ {len(self.urls)} URLs ] | Clear the record list'
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

        self.progress_bar_task_name.append(task_name)

        progress_layout = QHBoxLayout()
        progress_label = QLabel(task_name)
        progress_bar = QProgressBar(maximum=count)
        progress_bar.setFormat("%v / %m (%p%)")
        progress_bar.setValue(0)
        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(progress_bar)
        progress_layout.setStretch(0, 1)
        progress_layout.setStretch(1, 5)

        self.progress_bar_data[task_name] = ProgressBarData(progress_layout=progress_layout,
                                                            progress_bar_widget=progress_bar,
                                                            completed=0,
                                                            executed=0,
                                                            quantity=count)
        self.ui.verticalLayout.addLayout(progress_layout)
        QApplication.processEvents()

    def update_process_bar(self, task_name: str, is_completed: bool) -> ProgressBarData:
        """
        Updating progress bar information.
        :param task_name: progress bar task name
        :param is_completed: set to True, it will synchronously update the 'completed' attribute of the ProgressBarData.
        :return: ProgressBarData
        """
        progress_bar_data: ProgressBarData = self.progress_bar_data[task_name]
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
        self.ui.clear_push_button.setEnabled(unfreeze)
        self.able_option_action(unfreeze)
        QApplication.processEvents()

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
        prefix_string = f'{datetime.now().strftime("%H:%M:%S")} [ {len(self.urls)} URLs ] | ' if prefix else ''
        full_string = f'<span style="color: {color};">{prefix_string}{string}</span>'
        self.ui.operation_text_browser.append('')
        self.ui.operation_text_browser.insertHtml(full_string)
        self.ui.operation_text_browser.setCurrentCharFormat(QTextCharFormat())

    def clear_progress_bar(self) -> None:
        """
        Clear all progress bar layout
        """
        for progress_name in self.progress_bar_task_name:
            each_progres_bar_info: ProgressBarData = self.progress_bar_data[progress_name]
            layout = each_progres_bar_info.progress_layout
            self.clear_layout_widgets(layout)

        self.progress_bar_task_name.clear()
        self.progress_bar_data.clear()

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
        if self.urls:
            reply = QMessageBox.question(self, 'Warning',
                                         'Do you want to save the URL of the clipboard before exiting？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                record = (self.save_dir,
                          self.ui.civitai_check_box.isChecked(),
                          self.urls,
                          )
                with open(f'{datetime.now().strftime("%m-%d-%H:%M:%S")}.bringmeimage', 'wb') as f:
                    pickle.dump(record, f)

        try:
            if self.driver_page:
                self.driver_page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
        except Exception as e:
            print(e)
        finally:
            if self.playwright:
                self.playwright.stop()

        event.accept()
