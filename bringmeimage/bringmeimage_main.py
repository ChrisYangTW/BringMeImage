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
        MainWindow.resize(800, 400)
        self.actionLoadClipboardFile = QAction(MainWindow)
        self.actionLoadClipboardFile.setObjectName(u"actionLoadClipboardFile")
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
        self.folder_line_edit.setEnabled(True)
        self.folder_line_edit.setReadOnly(True)

        self.horizontalLayout_1.addWidget(self.folder_line_edit)

        self.horizontalLayout_1.setStretch(0, 1)
        self.horizontalLayout_1.setStretch(1, 10)

        self.verticalLayout.addLayout(self.horizontalLayout_1)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.clip_push_button = QPushButton(self.centralwidget)
        self.clip_push_button.setObjectName(u"clip_push_button")

        self.horizontalLayout_2.addWidget(self.clip_push_button)

        self.go_push_button = QPushButton(self.centralwidget)
        self.go_push_button.setObjectName(u"go_push_button")

        self.horizontalLayout_2.addWidget(self.go_push_button)

        self.civitai_check_box = QCheckBox(self.centralwidget)
        self.civitai_check_box.setObjectName(u"civitai_check_box")
        self.civitai_check_box.setChecked(True)

        self.horizontalLayout_2.addWidget(self.civitai_check_box)

        self.categorize_check_box = QCheckBox(self.centralwidget)
        self.categorize_check_box.setObjectName(u"categorize_check_box")
        self.categorize_check_box.setChecked(True)

        self.horizontalLayout_2.addWidget(self.categorize_check_box)

        self.clear_push_button = QPushButton(self.centralwidget)
        self.clear_push_button.setObjectName(u"clear_push_button")

        self.horizontalLayout_2.addWidget(self.clear_push_button)

        self.horizontalLayout_2.setStretch(0, 4)
        self.horizontalLayout_2.setStretch(1, 4)
        self.horizontalLayout_2.setStretch(2, 1)
        self.horizontalLayout_2.setStretch(3, 1)
        self.horizontalLayout_2.setStretch(4, 1)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.operation_text_browser = QTextBrowser(self.centralwidget)
        self.operation_text_browser.setObjectName(u"operation_text_browser")
        font = QFont()
        font.setPointSize(16)
        self.operation_text_browser.setFont(font)

        self.verticalLayout.addWidget(self.operation_text_browser)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 1)
        self.verticalLayout.setStretch(2, 4)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 37))
        self.menuOption = QMenu(self.menubar)
        self.menuOption.setObjectName(u"menuOption")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuOption.menuAction())
        self.menuOption.addAction(self.actionLoadClipboardFile)
        self.menuOption.addAction(self.actionShowFailUrl)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Bring Me Image", None))
        self.actionLoadClipboardFile.setText(QCoreApplication.translate("MainWindow", u"Load Clipboard File", None))
        self.actionShowFailUrl.setText(QCoreApplication.translate("MainWindow", u"Show Failed URLs", None))
        self.actionDownloadMode.setText(QCoreApplication.translate("MainWindow", u"Download Mode", None))
        self.folder_label.setText(QCoreApplication.translate("MainWindow", u"Folder", None))
#if QT_CONFIG(tooltip)
        self.folder_line_edit.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.folder_line_edit.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Click to select the path for saving", None))
#if QT_CONFIG(tooltip)
        self.clip_push_button.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.clip_push_button.setText(QCoreApplication.translate("MainWindow", u"Clip", None))
#if QT_CONFIG(tooltip)
        self.go_push_button.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.go_push_button.setText(QCoreApplication.translate("MainWindow", u"Go", None))
#if QT_CONFIG(tooltip)
        self.civitai_check_box.setToolTip(QCoreApplication.translate("MainWindow", u"Analyzing the image links for civitai", None))
#endif // QT_CONFIG(tooltip)
        self.civitai_check_box.setText(QCoreApplication.translate("MainWindow", u"CivitAI", None))
#if QT_CONFIG(tooltip)
        self.categorize_check_box.setToolTip(QCoreApplication.translate("MainWindow", u"Automatically categorizing the path for storing images (with \"CivitAI\" checkbox selected)", None))
#endif // QT_CONFIG(tooltip)
        self.categorize_check_box.setText(QCoreApplication.translate("MainWindow", u"Categorize", None))
#if QT_CONFIG(tooltip)
        self.clear_push_button.setToolTip(QCoreApplication.translate("MainWindow", u"Clear all record list", None))
#endif // QT_CONFIG(tooltip)
        self.clear_push_button.setText(QCoreApplication.translate("MainWindow", u"Clear", None))
        self.menuOption.setTitle(QCoreApplication.translate("MainWindow", u"Option", None))
#if QT_CONFIG(statustip)
        self.statusbar.setStatusTip("")
#endif // QT_CONFIG(statustip)
    # retranslateUi

