#from qgis.gui import *
#from qgis.core import *
#from qgis.PyQt import QtCore, QtGui, QtWidgets
from PyQt5 import QtCore, QtGui, QtWidgets
import time

listUTC = [-12, -11, -10, -9.5, -9, -8, -7, 
    -6, -5, -4, -3.5, -3, -2, -1, 0,
    1, 2, 3, 3.5, 4, 4.5, 5, 5.5, 5.75, 
    6, 6.5, 7, 8, 8.75, 9, 9.5, 10, 10.5,
    11, 12, 12.75, 13, 14]

class Ui_gpxWindow(object):
    def setupUi(self, gpxWindow):
        gpxWindow.setObjectName("gpxWindow")
        gpxWindow.resize(399, 363)
        self.buttonBox = QtWidgets.QDialogButtonBox(gpxWindow)
        self.buttonBox.setGeometry(QtCore.QRect(210, 240, 161, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.label = QtWidgets.QLabel(gpxWindow)
        self.label.setGeometry(QtCore.QRect(30, 100, 171, 16))
        self.label.setObjectName("label")
        self.groupBox = dropedit(gpxWindow)
        self.groupBox.setGeometry(QtCore.QRect(20, 10, 351, 71))
        self.groupBox.setObjectName("groupBox")
        self.toolButtonGPX = QtWidgets.QToolButton(self.groupBox)
        self.toolButtonGPX.setGeometry(QtCore.QRect(320, 30, 25, 19))
        self.toolButtonGPX.setObjectName("toolButtonGPX")
        self.lineEditPathGPX = QtWidgets.QLineEdit(self.groupBox)
        self.lineEditPathGPX.setGeometry(QtCore.QRect(20, 30, 291, 20))
        self.lineEditPathGPX.setObjectName("lineEditPathGPX")
        self.label_2 = QtWidgets.QLabel(gpxWindow)
        self.label_2.setGeometry(QtCore.QRect(30, 140, 161, 16))
        self.label_2.setObjectName("label_2")
        self.checkBoxKeep = QtWidgets.QCheckBox(gpxWindow)
        self.checkBoxKeep.setGeometry(QtCore.QRect(30, 215, 221, 17))
        self.checkBoxKeep.setObjectName("checkBoxKeep")
        self.progressBar = QtWidgets.QProgressBar(gpxWindow)
        self.progressBar.setEnabled(True)
        self.progressBar.setGeometry(QtCore.QRect(40, 310, 331, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.spinBoxInterpol = QtWidgets.QSpinBox(gpxWindow)
        self.spinBoxInterpol.setGeometry(QtCore.QRect(200, 100, 171, 22))
        self.spinBoxInterpol.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.spinBoxInterpol.setMinimum(0)
        self.spinBoxInterpol.setMaximum(3600)
        self.spinBoxInterpol.setSingleStep(5)
        self.spinBoxInterpol.setProperty("value", 120)
        self.spinBoxInterpol.setObjectName("spinBoxInterpol")
        self.toolButtonUpUTC = QtWidgets.QToolButton(gpxWindow)
        self.toolButtonUpUTC.setGeometry(QtCore.QRect(355, 139, 16, 12))
        self.toolButtonUpUTC.setArrowType(QtCore.Qt.UpArrow)
        self.toolButtonUpUTC.setObjectName("toolButtonUpUTC")
        self.toolButtonUpUTC.clicked.connect(self.upArrowPress)
        self.toolButtonDownUTC = QtWidgets.QToolButton(gpxWindow)
        self.toolButtonDownUTC.setGeometry(QtCore.QRect(355, 149, 16, 12))
        self.toolButtonDownUTC.setArrowType(QtCore.Qt.DownArrow)
        self.toolButtonDownUTC.setObjectName("toolButtonDownUTC")
        self.toolButtonDownUTC.clicked.connect(self.downArrowPress)
        self.lineEditUTC = QtWidgets.QLineEdit(gpxWindow)
        self.lineEditUTC.setGeometry(QtCore.QRect(200, 140, 156, 20))
        self.lineEditUTC.setObjectName("lineEditUTC")
        self.lineEditUTC.setReadOnly(True)
        offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        self.currentUTC = offset /60 /60 * -1
        for i in range(len(listUTC)) :
            if listUTC[i] == self.currentUTC :
                self.currentIndex = i
                break
        else : 
            self.currentIndex = 14
        self.setUTCstr(self.currentUTC)
        self.label_3 = QtWidgets.QLabel(gpxWindow)
        self.label_3.setGeometry(QtCore.QRect(30, 180, 131, 16))
        self.label_3.setObjectName("label_3")
        self.spinBoxDecalage = QtWidgets.QSpinBox(gpxWindow)
        self.spinBoxDecalage.setGeometry(QtCore.QRect(200, 180, 171, 22))
        self.spinBoxDecalage.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.spinBoxDecalage.setMinimum(0)
        self.spinBoxDecalage.setMaximum(3600)
        self.spinBoxDecalage.setSingleStep(5)
        self.spinBoxDecalage.setProperty("value", 0)
        self.spinBoxDecalage.setObjectName("spinBoxDecalage")
        self.labelNbSelect = QtWidgets.QLabel(gpxWindow)
        self.labelNbSelect.setGeometry(QtCore.QRect(40, 280, 331, 20))
        self.labelNbSelect.setObjectName("labelNbSelect")

        self.retranslateUi(gpxWindow)
        QtCore.QMetaObject.connectSlotsByName(gpxWindow)

    def retranslateUi(self, gpxWindow):
        _translate = QtCore.QCoreApplication.translate
        gpxWindow.setWindowTitle(_translate("gpxWindow", "Ajout par GPX"))
        self.label.setText(_translate("gpxWindow", "Temps d\'interpolation maximal (s)"))
        self.groupBox.setTitle(_translate("gpxWindow", "Chemin GPX"))
        self.toolButtonGPX.setText(_translate("gpxWindow", "..."))
        self.label_2.setText(_translate("gpxWindow", "Décalage Horaire ±HH:MM (UTC)"))
        self.checkBoxKeep.setText(_translate("gpxWindow", "Conserver les coordonnées existantes"))
        self.toolButtonUpUTC.setText(_translate("gpxWindow", "..."))
        self.toolButtonDownUTC.setText(_translate("gpxWindow", "..."))
        self.label_3.setText(_translate("gpxWindow", "Décalage temporel additionnel (s)"))
        self.labelNbSelect.setText(_translate("gpxWindow", " Le traitement s\'appliquera sur les 0 photos sélectionnées."))

    def upArrowPress(self) :
        if self.currentIndex < 37 :
            self.currentIndex += 1
            self.currentUTC = listUTC[self.currentIndex]
            self.setUTCstr(self.currentUTC)
        else :
            pass


    def downArrowPress(self) :
        if self.currentIndex > 0 :
            self.currentIndex -= 1
            self.currentUTC = listUTC[self.currentIndex]
            self.setUTCstr(self.currentUTC)
        else :
            pass

    def setUTCstr(self, utc) :
        strSign = '+' if utc >= 0 else '-'
        strHour = str(int(abs(utc))) if int(abs(utc)) > 9 else  '0' + str(int(abs(utc)))
        
        if abs(utc - int(utc)) == 0.25 :
            strMin = '15'
        elif abs(utc - int(utc))  == 0.5 :
            strMin = '30'
        elif abs(utc - int(utc))  == 0.75 :
            strMin = '45'
        else :
            strMin = '00'
        
        strUTC = strSign + strHour + ':' + strMin
        
        self.lineEditUTC.setText(strUTC)



class dropedit(QtWidgets.QGroupBox):   

    def __init__(self, parent=None):
        super(dropedit, self).__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        event.accept()
        
    def dropEvent(self, event):
        fileURL = event.mimeData().urls()[0].toString()
        try :
            fileName = fileURL.split('file:///')[1]
        except :
            fileName = fileURL.split('file:')[1]
        
        for child in self.children(): 
            if child.metaObject().className() == "QLineEdit":
                child.setText(fileName)
