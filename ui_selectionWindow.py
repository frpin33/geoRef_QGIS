# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui-getLayer.ui'
#
# Created by: PyQt5 UI code generator 5.12.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_getVectorLayer(object):
    def setupUi(self, getVectorLayer):
        getVectorLayer.setObjectName("getVectorLayer")
        getVectorLayer.resize(351, 358)
        self.buttonBox = QtWidgets.QDialogButtonBox(getVectorLayer)
        self.buttonBox.setGeometry(QtCore.QRect(180, 320, 156, 23))
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.listWidget = QtWidgets.QListWidget(getVectorLayer)
        self.listWidget.setGeometry(QtCore.QRect(30, 50, 291, 261))
        self.listWidget.setObjectName("listWidget")
        #item = QtWidgets.QListWidgetItem()
        #font = QtGui.QFont()
        #font.setPointSize(12)
        #item.setFont(font)
        #item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsEnabled)
        #self.listWidget.addItem(item)
        self.label = QtWidgets.QLabel(getVectorLayer)
        self.label.setGeometry(QtCore.QRect(110, 10, 141, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setObjectName("label")

        self.retranslateUi(getVectorLayer)
        QtCore.QMetaObject.connectSlotsByName(getVectorLayer)

    def retranslateUi(self, getVectorLayer):
        _translate = QtCore.QCoreApplication.translate
        getVectorLayer.setWindowTitle(_translate("getVectorLayer", "Choix des images"))
        __sortingEnabled = self.listWidget.isSortingEnabled()
        self.listWidget.setSortingEnabled(False)
        #item = self.listWidget.item(0)
        #item.setText(_translate("getVectorLayer", "New Item"))
        self.listWidget.setSortingEnabled(__sortingEnabled)
        self.label.setText(_translate("getVectorLayer", "Images Disponibles"))


class getSelectionWindow(QtWidgets.QDialog): 
    def __init__(self, listPicture, heading=False, shpName=False, setTrue=[]):
        super(getSelectionWindow, self).__init__()
        self.ui = Ui_getVectorLayer()
        self.ui.setupUi(self)
        for name in listPicture:
            item = QtWidgets.QListWidgetItem()
            font = QtGui.QFont()
            font.setPointSize(12)
            item.setFont(font)
            item.setFlags(QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
            if name in setTrue : item.setCheckState(QtCore.Qt.Checked)
            else : item.setCheckState(QtCore.Qt.Unchecked)
            item.setText(name)
            self.ui.listWidget.addItem(item)
        self.ui.listWidget.item(0).setSelected(True) 
        if heading : 
            self.ui.checkBox = QtWidgets.QCheckBox(self)
            self.ui.checkBox.setGeometry(QtCore.QRect(30, 320, 91, 16))
            self.ui.checkBox.setChecked(False)
            self.ui.checkBox.setText('Heading')
            self.ui.checkBox.setObjectName("checkBox")   
        if shpName : 
            self.ui.lineEdit = QtWidgets.QLineEdit(self)
            self.ui.lineEdit.setGeometry(QtCore.QRect(20, 320, 151, 20))
            self.ui.lineEdit.setText('Nom')