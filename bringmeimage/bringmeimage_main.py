# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'bringmeimage_main.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSizePolicy, QStatusBar, QTextBrowser,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.actionShowHistory = QAction(MainWindow)
        self.actionShowHistory.setObjectName(u"actionShowHistory")
        self.actionShowFailUrl = QAction(MainWindow)
        self.actionShowFailUrl.setObjectName(u"actionShowFailUrl")
        self.actionDownloadMode = QAction(MainWindow)
        self.actionDownloadMode.setObjectName(u"actionDownloadMode")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_1 = QHBoxLayout()
        self.horizontalLayout_1.setObjectName(u"horizontalLayout_1")
        self.folder_label = QLabel(self.centralwidget)
        self.folder_label.setObjectName(u"folder_label")
        self.folder_label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_1.addWidget(self.folder_label)

        self.folder_line_edit = QLineEdit(self.centralwidget)
        self.folder_line_edit.setObjectName(u"folder_line_edit")
        self.folder_line_edit.setEnabled(False)

        self.horizontalLayout_1.addWidget(self.folder_line_edit)

        self.choose_folder_button = QPushButton(self.centralwidget)
        self.choose_folder_button.setObjectName(u"choose_folder_button")

        self.horizontalLayout_1.addWidget(self.choose_folder_button)

        self.horizontalLayout_1.setStretch(0, 2)
        self.horizontalLayout_1.setStretch(1, 14)
        self.horizontalLayout_1.setStretch(2, 2)

        self.verticalLayout.addLayout(self.horizontalLayout_1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.start_clip_push_button = QPushButton(self.centralwidget)
        self.start_clip_push_button.setObjectName(u"start_clip_push_button")

        self.horizontalLayout_2.addWidget(self.start_clip_push_button)

        self.civitai_check_box = QCheckBox(self.centralwidget)
        self.civitai_check_box.setObjectName(u"civitai_check_box")
        self.civitai_check_box.setChecked(True)

        self.horizontalLayout_2.addWidget(self.civitai_check_box)

        self.categorize_check_box = QCheckBox(self.centralwidget)
        self.categorize_check_box.setObjectName(u"categorize_check_box")
        self.categorize_check_box.setChecked(True)

        self.horizontalLayout_2.addWidget(self.categorize_check_box)

        self.stayon_check_box = QCheckBox(self.centralwidget)
        self.stayon_check_box.setObjectName(u"stayon_check_box")

        self.horizontalLayout_2.addWidget(self.stayon_check_box)

        self.horizontalLayout_2.setStretch(0, 2)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.operation_text_browser = QTextBrowser(self.centralwidget)
        self.operation_text_browser.setObjectName(u"operation_text_browser")

        self.verticalLayout.addWidget(self.operation_text_browser)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.result_text_browser = QTextBrowser(self.centralwidget)
        self.result_text_browser.setObjectName(u"result_text_browser")

        self.verticalLayout.addWidget(self.result_text_browser)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 2)
        self.verticalLayout.setStretch(4, 2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 37))
        self.menuShow = QMenu(self.menubar)
        self.menuShow.setObjectName(u"menuShow")
        self.menuDev = QMenu(self.menubar)
        self.menuDev.setObjectName(u"menuDev")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuShow.menuAction())
        self.menubar.addAction(self.menuDev.menuAction())
        self.menuShow.addAction(self.actionShowHistory)
        self.menuShow.addAction(self.actionShowFailUrl)
        self.menuDev.addAction(self.actionDownloadMode)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Help Me Download (just for Civit)", None))
        self.actionShowHistory.setText(QCoreApplication.translate("MainWindow", u"Show History", None))
        self.actionShowFailUrl.setText(QCoreApplication.translate("MainWindow", u"Show Failed URLs", None))
        self.actionDownloadMode.setText(QCoreApplication.translate("MainWindow", u"Download Mode", None))
        self.folder_label.setText(QCoreApplication.translate("MainWindow", u"Folder", None))
        self.choose_folder_button.setText(QCoreApplication.translate("MainWindow", u"Folder", None))
        self.start_clip_push_button.setText(QCoreApplication.translate("MainWindow", u"Start Clip", None))
#if QT_CONFIG(tooltip)
        self.civitai_check_box.setToolTip(QCoreApplication.translate("MainWindow", u"Analyzing the image links for civitai", None))
#endif // QT_CONFIG(tooltip)
        self.civitai_check_box.setText(QCoreApplication.translate("MainWindow", u"CivitAI", None))
#if QT_CONFIG(tooltip)
        self.categorize_check_box.setToolTip(QCoreApplication.translate("MainWindow", u"Automatically categorizing the path for storing images (with \"CivitAI\" checkbox selected)", None))
#endif // QT_CONFIG(tooltip)
        self.categorize_check_box.setText(QCoreApplication.translate("MainWindow", u"Categorize", None))
#if QT_CONFIG(tooltip)
        self.stayon_check_box.setToolTip(QCoreApplication.translate("MainWindow", u"Keep the window always on top", None))
#endif // QT_CONFIG(tooltip)
        self.stayon_check_box.setText(QCoreApplication.translate("MainWindow", u"StayOn", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Download task message", None))
        self.menuShow.setTitle(QCoreApplication.translate("MainWindow", u"Show", None))
        self.menuDev.setTitle(QCoreApplication.translate("MainWindow", u"Dev", None))
    # retranslateUi

