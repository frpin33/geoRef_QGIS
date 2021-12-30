from qgis.gui import *
from qgis.core import *
from qgis.PyQt import QtCore, QtGui, QtWidgets
from os.path import isdir


class Ui_geoRefMainWindow(object):
    def setupUi(self, geoRefMainWindow):
        geoRefMainWindow.setObjectName("geoRefMainWindow")
        geoRefMainWindow.resize(800, 665)
        self.centralwidget = QtWidgets.QWidget(geoRefMainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.graphicsView = QtWidgets.QGraphicsView(self.centralwidget)
        self.graphicsView.setGeometry(QtCore.QRect(220, 80, 561, 341))
        self.graphicsView.setObjectName("graphicsView")
        self.lineEditXCoordQGIS = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditXCoordQGIS.setGeometry(QtCore.QRect(260, 480, 113, 20))
        self.lineEditXCoordQGIS.setReadOnly(True)
        self.lineEditXCoordQGIS.setObjectName("lineEditXCoordQGIS")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(210, 480, 51, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(210, 510, 51, 16))
        self.label_2.setObjectName("label_2")
        self.lineEditYCoordQGIS = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditYCoordQGIS.setGeometry(QtCore.QRect(260, 510, 113, 20))
        self.lineEditYCoordQGIS.setReadOnly(True)
        self.lineEditYCoordQGIS.setObjectName("lineEditYCoordQGIS")
        self.pushButtonGPX = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonGPX.setEnabled(False)
        self.pushButtonGPX.setGeometry(QtCore.QRect(600, 560, 181, 23))
        self.pushButtonGPX.setObjectName("pushButtonGPX")
        self.pushButtonClick = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonClick.setGeometry(QtCore.QRect(550, 480, 161, 23))
        self.pushButtonClick.setCheckable(False)
        self.pushButtonClick.setObjectName("pushButtonClick")
        self.labelCurrentPic = QtWidgets.QLabel(self.centralwidget)
        self.labelCurrentPic.setGeometry(QtCore.QRect(220, 420, 561, 16))
        self.labelCurrentPic.setText("")
        self.labelCurrentPic.setObjectName("labelCurrentPic")
        self.lineEditXCoordStand = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditXCoordStand.setGeometry(QtCore.QRect(380, 480, 113, 20))
        self.lineEditXCoordStand.setReadOnly(True)
        self.lineEditXCoordStand.setObjectName("lineEditXCoordStand")
        self.lineEditYCoordStand = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditYCoordStand.setGeometry(QtCore.QRect(380, 510, 113, 20))
        self.lineEditYCoordStand.setReadOnly(True)
        self.lineEditYCoordStand.setObjectName("lineEditYCoordStand")
        self.groupBox = dropedit(self.centralwidget)
        self.groupBox.setGeometry(QtCore.QRect(210, 10, 581, 61))
        self.groupBox.setObjectName("groupBox")
        self.lineEditRootPath = QtWidgets.QLineEdit(self.groupBox)
        self.lineEditRootPath.setGeometry(QtCore.QRect(10, 30, 531, 20))
        self.lineEditRootPath.setObjectName("lineEditRootPath")
        self.toolButton = QtWidgets.QToolButton(self.groupBox)
        self.toolButton.setGeometry(QtCore.QRect(550, 30, 25, 19))
        self.toolButton.setObjectName("toolButton")
        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        self.treeWidget.setGeometry(QtCore.QRect(10, 20, 191, 251))
        self.treeWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.treeWidget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.treeWidget.setAutoScroll(False)
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setHeaderHidden(True)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.listAvailablePic = QtWidgets.QListWidget(self.centralwidget)
        self.listAvailablePic.setGeometry(QtCore.QRect(10, 290, 191, 221))
        self.listAvailablePic.setAutoScroll(False)
        self.listAvailablePic.setAlternatingRowColors(True)
        self.listAvailablePic.setObjectName("listAvailablePic")
        self.labelEPSG = QtWidgets.QLabel(self.centralwidget)
        self.labelEPSG.setGeometry(QtCore.QRect(260, 460, 91, 16))
        self.labelEPSG.setObjectName("labelEPSG")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(380, 460, 61, 16))
        self.label_4.setObjectName("label_4")
        self.lineEditHeading = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditHeading.setGeometry(QtCore.QRect(380, 560, 113, 20))
        self.lineEditHeading.setReadOnly(True)
        self.lineEditHeading.setObjectName("lineEditHeading")
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(380, 540, 51, 16))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setGeometry(QtCore.QRect(260, 540, 47, 13))
        self.label_7.setObjectName("label_7")
        self.lineEditAltitude = QtWidgets.QLineEdit(self.centralwidget)
        self.lineEditAltitude.setGeometry(QtCore.QRect(260, 560, 113, 20))
        self.lineEditAltitude.setReadOnly(True)
        self.lineEditAltitude.setObjectName("lineEditAltitude")
        self.pushButtonEdit = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonEdit.setGeometry(QtCore.QRect(270, 590, 100, 23))
        self.pushButtonEdit.setObjectName("pushButtonEdit")
        self.progressBar = QtWidgets.QProgressBar(self.centralwidget)
        self.progressBar.setGeometry(QtCore.QRect(10, 520, 191, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setTextVisible(False)
        self.progressBar.setObjectName("progressBar")
        self.labelProgress = QtWidgets.QLabel(self.centralwidget)
        self.labelProgress.setGeometry(QtCore.QRect(10, 550, 191, 20))
        self.labelProgress.setAlignment(QtCore.Qt.AlignCenter)
        self.labelProgress.setObjectName("labelProgress")
        self.radioButtonDD = QtWidgets.QRadioButton(self.centralwidget)
        self.radioButtonDD.setGeometry(QtCore.QRect(500, 480, 82, 17))
        self.radioButtonDD.setChecked(True)
        self.radioButtonDD.setObjectName("radioButtonDD")
        self.radioButtonDMS = QtWidgets.QRadioButton(self.centralwidget)
        self.radioButtonDMS.setGeometry(QtCore.QRect(500, 510, 82, 17))
        self.radioButtonDMS.setChecked(False)
        self.radioButtonDMS.setObjectName("radioButtonDMS")
        self.pushButtonApplySingle = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonApplySingle.setEnabled(False)
        self.pushButtonApplySingle.setGeometry(QtCore.QRect(560, 510, 115, 23))
        self.pushButtonApplySingle.setObjectName("pushButtonApplySingle")
        self.pushButtonCancelClick = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonCancelClick.setEnabled(False)
        self.pushButtonCancelClick.setGeometry(QtCore.QRect(720, 480, 75, 23))
        self.pushButtonCancelClick.setObjectName("pushButtonCancelClick")
        self.pushButtonApplyGroup = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonApplyGroup.setEnabled(False)
        self.pushButtonApplyGroup.setGeometry(QtCore.QRect(680, 510, 115, 23))
        self.pushButtonApplyGroup.setObjectName("pushButtonApplyGroup")
        self.pushButtonClone = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonClone.setGeometry(QtCore.QRect(390, 590, 101, 23))
        self.pushButtonClone.setObjectName("pushButtonClone")
        self.pushButtonShapefile = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonShapefile.setGeometry(QtCore.QRect(30, 600, 141, 23))
        self.pushButtonShapefile.setObjectName("pushButtonShapefile")
        self.checkBoxShowPosition = QtWidgets.QCheckBox(self.centralwidget)
        self.checkBoxShowPosition.setGeometry(QtCore.QRect(45, 575, 121, 17))
        self.checkBoxShowPosition.setChecked(True)
        self.checkBoxShowPosition.setObjectName("checkBoxShowPosition")
        geoRefMainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(geoRefMainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        geoRefMainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(geoRefMainWindow)
        self.statusbar.setObjectName("statusbar")
        geoRefMainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(geoRefMainWindow)
        QtCore.QMetaObject.connectSlotsByName(geoRefMainWindow)

    def retranslateUi(self, geoRefMainWindow):
        _translate = QtCore.QCoreApplication.translate
        geoRefMainWindow.setWindowTitle(_translate("geoRefMainWindow", "Outil de géoréférencement"))
        self.label.setText(_translate("geoRefMainWindow", "Longitude"))
        self.label_2.setText(_translate("geoRefMainWindow", "Latitude"))
        self.pushButtonGPX.setText(_translate("geoRefMainWindow", "Via un fichier GPX"))
        self.pushButtonClick.setText(_translate("geoRefMainWindow", "Via Clic sur Canvas"))
        self.groupBox.setTitle(_translate("geoRefMainWindow", "Dossier Sélectionné"))
        self.toolButton.setText(_translate("geoRefMainWindow", "..."))
        self.labelEPSG.setText(_translate("geoRefMainWindow", "EPSG :"))
        self.label_4.setText(_translate("geoRefMainWindow", "EPSG:4326"))
        self.label_6.setText(_translate("geoRefMainWindow", "Heading"))
        self.label_7.setText(_translate("geoRefMainWindow", "Altitude"))
        self.pushButtonEdit.setText(_translate("geoRefMainWindow", "Modif. Paramètres"))
        self.labelProgress.setText(_translate("geoRefMainWindow", "Dossiers traitées : 0/0"))
        self.radioButtonDD.setText(_translate("geoRefMainWindow", "DD"))
        self.radioButtonDMS.setText(_translate("geoRefMainWindow", "DMS"))
        self.pushButtonApplySingle.setText(_translate("geoRefMainWindow", "Appliquer Image Seule"))
        self.pushButtonCancelClick.setText(_translate("geoRefMainWindow", "Annuler"))
        self.pushButtonApplyGroup.setText(_translate("geoRefMainWindow", "Appliquer pour groupe"))
        self.pushButtonClone.setText(_translate("geoRefMainWindow", "Copier Paramètres"))
        self.pushButtonShapefile.setText(_translate("geoRefMainWindow", "Générer Shapefile de points"))
        self.checkBoxShowPosition.setText(_translate("geoRefMainWindow", "Afficher la position"))



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
        
        if isdir(fileName):
            for child in self.children(): 
                if child.metaObject().className() == "QLineEdit":
                    child.setText(fileName)