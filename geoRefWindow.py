'''
L'entièreté du code a été réalisé par Frédérick Pineault (frederick.pineault@mffp.gouv.qc.ca)

Ce dossier contient la classe principale de l'application Qt, elle est appelé par QGIS pour ouvrir la fenêtre principale

Ce dossier contient deux objets qui sont utile pour le traitement des photos. Les objets permettent de concerver de l'information
spécifique pour chacune des photos. Elles permettent de faciliter le traitement et la recherche d'information.  

La classe geoRefWindow permet de :
    - Écrire et lire les information EXIF d'une photo
    - Visualiser les photos, les coordonnées XY, l'orientation (heading) et l'altitude
    - Produire des coordonnées et une orientation via QGIS et la souris
    - Modifier les coordonnées XYZ d'une photo
    - Utiliser un fichier GPX pour faire un traitement sur les photos 
    - Copier les information d'une photo vers d'autres images
    - Transformer les informations des photos géoréférencement en un shapefile de points
    - Afficher les images géoréférencées via un point dans QGIS

'''

from qgis.gui import *
from qgis.core import *
from qgis.PyQt import QtCore, QtGui, QtWidgets

from os.path import splitext, dirname, abspath, join, exists
from os import walk, listdir, environ, remove
from fractions import Fraction
from qimage2ndarray import array2qimage
from PIL import Image
import numpy as np
import piexif
#from iptcinfo3 import IPTCInfo

from .ui_geoRefWindow import Ui_geoRefMainWindow
from .gpxWindow import gpxWindow
from .ui_selectionWindow import getSelectionWindow

from . import resources

fileAcceptFormat = [".jpg", ".jpeg"]

class geoRefWindow(object): 
    def __init__(self, iface):
        self.iface = iface
        self.canvas = self.iface.mapCanvas()

    #Place le bouton de l'application dans QGIS
    def initGui(self):
        urlPicture = ":/geoRef/logo.png"
        self.action = QtWidgets.QAction(QtGui.QIcon(urlPicture), "geoRef_DIF", self.iface.mainWindow())
        
        self.action.triggered.connect(self.run)
         
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&geoRef_DIF", self.action)

    #Retire le bout de l'application dans QGIS
    def unload(self):
        self.iface.removePluginMenu("&geoRef_DIF", self.action)
        self.iface.removeToolBarIcon(self.action)
    
    #Fonction appelée lorsque l'application est lancé
    #Initialise le fenêtre principale et l'ouvre
    #Récupération du SIG en cours
    def run(self):
    
        self.mainWindow = QtWidgets.QMainWindow()
        self.mainWindow.closeEvent = self.closeMainWindow
        
        
        self.ui = Ui_geoRefMainWindow()
        
        self.ui.setupUi(self.mainWindow)
        
        self.ui.lineEditRootPath.textChanged.connect(self.newRootPath)
        self.ui.toolButton.clicked.connect(self.importDirButton)
        self.ui.listAvailablePic.itemClicked.connect(self.newPictureSelection)
        
        self.listObjDirectory = []
        self.listObjPicture = []
        self.currentObjPicture = objPicture()
        self.currentMarkers = {}
        self.markerPositions = {}
        
        self.ui.checkBoxShowPosition.stateChanged.connect(self.actionPositionMarker)
        self.ui.pushButtonGPX.clicked.connect(self.actionClickGPX)
        self.ui.pushButtonClick.clicked.connect(self.actionClickCanvas)
        self.ui.pushButtonEdit.clicked.connect(self.changeParameters)
        self.ui.pushButtonClone.clicked.connect(self.openCloneParameters)
        self.ui.pushButtonShapefile.clicked.connect(self.openShapefileSelection)
        self.ui.radioButtonDD.toggled.connect(self.radioDegreeChange)
        self.activateEditing = False

        self.crsQGIS = QgsProject.instance().crs().authid()
        self.crsUniversal = "EPSG:4326"
        
        crsU = QgsCoordinateReferenceSystem(self.crsUniversal)
        crsQ = QgsCoordinateReferenceSystem(self.crsQGIS)

        #Transform = QgsCoordinateTransform(crsSource, crsTarget, QgsProject.instance()) 
        #LocalPos[0][1] = Transform.transform(QgsPointXY(x,y))
        self.coordQ2U = QgsCoordinateTransform(crsQ, crsU, QgsProject.instance())
        self.coordU2Q = QgsCoordinateTransform(crsU, crsQ, QgsProject.instance())
        
        self.ui.labelEPSG.setText(self.crsQGIS)
       
        self.mainWindow.show()

    #Fonction de fermeture de la fenêtre
    #Retire la croix et la line du canvas QGIS
    def closeMainWindow(self,ev):
        if hasattr(self, 'pinkCross'):
            self.canvas.scene().removeItem(self.pinkCross)
        if hasattr(self, 'redLine'):
            self.canvas.scene().removeItem(self.redLine)
        self.removeCanvasMarker()

    #Fonction appelée par le bouton GPX
    #Ouvre l'interface graphique qui gère le traitement
    def actionClickGPX(self):
        path = self.ui.lineEditRootPath.text()
        self.gpxUI = gpxWindow(path, self.listObjPicture)
        strLabel = 'Le traitement s\'appliquera sur les ' + str(len(self.listObjPicture))  + ' photos sélectionnées.'
        self.gpxUI.ui.labelNbSelect.setText(strLabel)
        self.gpxUI.ui.buttonBox.rejected.connect(self.closeGPXWindow)
        self.gpxUI.applyGPXDone.connect(self.applyGPXDone)
        self.gpxUI.show()

    #Fonction de fermeture de la fenêtre GPX
    def closeGPXWindow(self):
        self.gpxUI.close()
    
    #Fonction appelée à la fin du traitement GPX
    #Rafraîchis les information des objets qui ont reçu une modication suite au traitement
    def applyGPXDone(self, newListObj):
        
        self.closeGPXWindow()
        isFirstObj = True

        self.listObjPicture = newListObj
        self.ui.listAvailablePic.clear()

        for obj in self.listObjPicture :

            listItem = QtWidgets.QListWidgetItem(obj.nameInList)
            if isFirstObj :
                firstItem = listItem
                isFirstObj = False

            obj.idInList =id(listItem)
       
            if obj.isCoordonate :
                color = QtGui.QColor(QtCore.Qt.darkGreen)
                listItem.setForeground(QtGui.QBrush(color))
            elif obj.isEXIF :
                color = QtGui.QColor(QtCore.Qt.red)
                listItem.setForeground(QtGui.QBrush(color))
            else :
                color = QtGui.QColor(QtCore.Qt.darkRed)
                listItem.setForeground(QtGui.QBrush(color))

            self.ui.listAvailablePic.addItem(listItem)  
        
        self.addCanvasMarker(refresh=True)
        self.newPictureSelection(firstItem) 
        self.ui.listAvailablePic.setCurrentItem(firstItem)
        

    #Fonction appelée par le bouton Clic sur Canvas
    #Création d'un outil de détection pour recevoir les clics sur le Canvas QGIS
    #Rafraîchis le SIG en cours de QGIS
    def actionClickCanvas(self):

        if self.crsQGIS != QgsProject.instance().crs().authid() :
            self.crsQGIS = QgsProject.instance().crs().authid()
            crsU = QgsCoordinateReferenceSystem(self.crsUniversal)
            crsQ = QgsCoordinateReferenceSystem(self.crsQGIS)
            self.coordQ2U = QgsCoordinateTransform(crsQ, crsU, QgsProject.instance())
            self.coordU2Q = QgsCoordinateTransform(crsU, crsQ, QgsProject.instance())
            self.ui.labelEPSG.setText(self.crsQGIS)

        self.clickTool = QgsMapToolEmitPoint(self.canvas)
        self.canvas.setMapTool(self.clickTool)
        self.clickTool.canvasPressEvent = self.canvasPress
        self.clickTool.canvasReleaseEvent = self.canvasRelease
        self.clickTool.canvasMoveEvent = self.canvasMove
        self.isPressed = False

        try :
            self.ui.pushButtonCancelClick.clicked.disconnect(self.cancelClickCanvas)
            self.ui.pushButtonApplySingle.clicked.disconnect(self.applyClickCanvas)
            self.ui.pushButtonApplyGroup.clicked.disconnect(self.openClickSelection)
        except : pass

        self.ui.pushButtonClick.setEnabled(False)

        self.ui.pushButtonCancelClick.setEnabled(True)
        self.ui.pushButtonCancelClick.clicked.connect(self.cancelClickCanvas)

        self.itemInEdit = self.ui.listAvailablePic.currentItem()
        try :
            self.ui.listAvailablePic.itemClicked.disconnect(self.newPictureSelection)
        except : pass
        self.ui.listAvailablePic.itemClicked.connect(self.keepCurrentSelection)
    
    #Fonction qui permet de conserver l'objet de la liste lors du Click sur Canvas
    def keepCurrentSelection(self, item):
        self.ui.listAvailablePic.setCurrentItem(self.itemInEdit)

    #Fonction appelée par le bouton Cancel du Click sur Canvas
    #Réinitialise les informations de la photos
    #Retir la détection du clic, la croix et la ligne de QGIS
    def cancelClickCanvas(self):

        self.ui.pushButtonApplySingle.setEnabled(False)
        self.ui.pushButtonApplyGroup.setEnabled(False)
        self.ui.pushButtonCancelClick.setEnabled(False)
        self.ui.pushButtonClick.setEnabled(True)
        
        try :
            self.ui.listAvailablePic.itemClicked.disconnect(self.keepCurrentSelection)
        except : pass
        self.ui.listAvailablePic.itemClicked.connect(self.newPictureSelection)

        self.canvas.unsetMapTool(self.clickTool)
        if hasattr(self, 'pinkCross'):
            self.canvas.scene().removeItem(self.pinkCross)
        if hasattr(self, 'redLine'):
            self.canvas.scene().removeItem(self.redLine)
        
        objPic = self.currentObjPicture

        if objPic.isCoordonate :
            localCoord = self.coordU2Q.transform(QgsPointXY(objPic.xStandCoord, objPic.yStandCoord))
            xlocalstr = str(round(localCoord[0],1))
            ylocalstr = str(round(localCoord[1],1)) 
            self.ui.lineEditXCoordQGIS.setText(xlocalstr)
            self.ui.lineEditYCoordQGIS.setText(ylocalstr)
            
            self.changeDegreeType(objPic)
        
        else : 
            self.ui.lineEditXCoordStand.setText("")
            self.ui.lineEditYCoordStand.setText("")
            self.ui.lineEditXCoordQGIS.setText("")
            self.ui.lineEditYCoordQGIS.setText("")
                
        if objPic.isHeading :
            strH = str(round(objPic.heading,1)) + "°"
            self.ui.lineEditHeading.setText(strH) 
        else :
            self.ui.lineEditHeading.setText("") 

    #Fonction appelée par le bouton Appliquer Image Seule du Clic sur Canvas
    #Écris sur le EXIF de la photo les nouvelles informations
    def applyClickCanvas(self) :

        try :
            path = self.currentObjPicture.path

            if self.headingClick >= 0 : direction = self.headingClick
            else :  direction = None

            objPic = self.writeCoordOnObj(self.currentObjPicture, path, heading=direction, long=self.clicInitCoord[0], lat=self.clicInitCoord[1])

            color = QtGui.QColor(QtCore.Qt.darkGreen)
            self.ui.listAvailablePic.currentItem().setForeground(QtGui.QBrush(color))
            self.listObjPicture.remove(self.currentObjPicture)
            self.listObjPicture.append(objPic)
            self.currentObjPicture = objPic

            self.addCanvasMarker(refresh=True)

            #info = IPTCInfo(path, force=True)
            #info['keywords'].append('coordonnées approximatives')
            #info.save_as(path)
            #print(info.inp_charset)
            #print(info.out_charset)
            #path2Remove = path + "~"
            #remove(path2Remove)
        
        except : pass

        self.cancelClickCanvas()

    #Fonction appelée par le bouton Appliquer Image Seule du Clic sur Canvas
    #Elle ouvre une liste des images importées
    #L'utilisateur sélectionne les photos sur lesquelles il désire écrire l'information
    #La photo qui en cours de sélection sera automatique choisie 
    def openClickSelection(self):
        select = [self.currentObjPicture.nameInList]
        lName=[]
        for i in range(self.ui.listAvailablePic.count()) : lName.append(self.ui.listAvailablePic.item(i).text())
        self.clickSelectWindow = getSelectionWindow(lName, setTrue=select)
        self.clickSelectWindow.ui.buttonBox.accepted.connect(self.applyClickGroup)
        self.clickSelectWindow.ui.buttonBox.rejected.connect(lambda : self.clickSelectWindow.close())
        self.clickSelectWindow.show()
    
    #Fonction appelée par la fênetre de sélection des images lorsque la sélection est terminé
    #Écris sur le EXIF des photos les nouvelles informations
    def applyClickGroup(self) :
        #automatiquement avoir la sélection
        #path = self.currentObjPicture.path

        if self.headingClick >= 0 : direction = self.headingClick
        else :  direction = None

        l2Apply = []
        for i in range(self.clickSelectWindow.ui.listWidget.count()) :
            item = self.clickSelectWindow.ui.listWidget.item(i)
            if item.checkState() == QtCore.Qt.Checked : l2Apply.append(item.text())
        
        toRemove = []
        toAdd = []
        for obj in self.listObjPicture : 
            if obj.nameInList in l2Apply :
                path = obj.path
                objPic = self.writeCoordOnObj(obj, path, heading=direction, long=self.clicInitCoord[0], lat=self.clicInitCoord[1])
                toRemove.append(obj)
                toAdd.append(objPic)
        
        for item in toRemove : self.listObjPicture.remove(item)
        for item in toAdd :self.listObjPicture.append(item)
        
        for name in l2Apply :
            searchItem = self.ui.listAvailablePic.findItems(name, QtCore.Qt.MatchExactly)
            for i in searchItem :
                color = QtGui.QColor(QtCore.Qt.darkGreen)
                i.setForeground(QtGui.QBrush(color))
        
        self.addCanvasMarker(refresh=True)
        self.clickSelectWindow.close()
        self.cancelClickCanvas()


    #Fonction appelée lors d'un clic de souris sur le canvas QGIS
    #Ajoute la croix rose sur le canvas
    #Récupére les coordonnées et les afficher
    def canvasPress(self, ev):
        
        self.currentPoint = ev.mapPoint()
        self.headingClick = -1

        if hasattr(self, 'pinkCross'):
            self.canvas.scene().removeItem(self.pinkCross)
        
        self.pinkCross = QgsVertexMarker(self.canvas)
        self.pinkCross.setCenter(self.currentPoint)
        self.pinkCross.setColor(QtGui.QColor(255, 122, 255))
        self.pinkCross.setIconSize(10)
        self.pinkCross.setIconType(QgsVertexMarker.ICON_CROSS)
        self.pinkCross.setPenWidth(10)

        xlocalstr = str(round(self.currentPoint.x(),1))
        ylocalstr = str(round(self.currentPoint.y(),1)) 
        self.ui.lineEditXCoordQGIS.setText(xlocalstr)
        self.ui.lineEditYCoordQGIS.setText(ylocalstr)

        self.clicInitCoord = self.coordQ2U.transform(self.currentPoint)
        objPic = objPicture(xStandCoord=self.clicInitCoord[0],yStandCoord=self.clicInitCoord[1])
        self.changeDegreeType(objPic)
        
        self.isPressed = True
        if self.currentObjPicture.path and self.currentObjPicture.isEXIF :
            self.ui.pushButtonApplySingle.setEnabled(True)
            self.ui.pushButtonApplySingle.clicked.connect(self.applyClickCanvas)
            self.ui.pushButtonApplyGroup.setEnabled(True)
            self.ui.pushButtonApplyGroup.clicked.connect(self.openClickSelection)

    #Fonction appelée lors d'un déplacement de la souris sur le canvas QGIS
    #Cacul le heading via les coordonnées en cours de la souris
    def canvasMove(self,ev):
        if self.isPressed :

            point = ev.mapPoint()

            if hasattr(self, 'redLine'):
                self.canvas.scene().removeItem(self.redLine)
        
            self.redLine = QgsRubberBand(self.canvas)
            points = [point, self.currentPoint]
            self.redLine.setToGeometry(QgsGeometry.fromPolygonXY([points]))
            self.redLine.setColor(QtGui.QColor(255, 0, 0))
            self.redLine.setIconSize(10)

            self.clicMoveCoord = self.coordQ2U.transform(point)
            x = self.clicMoveCoord[0] - self.clicInitCoord[0]
            y = self.clicMoveCoord[1] - self.clicInitCoord[1]
            if x != 0 :
                degH = np.arctan(y/x)*180/np.pi
            else :
                degH = 0

            if x >= 0 :
                heading = 90 - degH
            else :
                heading = 270 - degH
            heading = heading % 360

            strH = str(int(round(heading))) + "°"
            self.ui.lineEditHeading.setText(strH)
            self.headingClick = heading

    #Fonction appelée lorsque le bouton de la souris est relâché
    def canvasRelease(self, ev):
        self.isPressed = False
        self.mainWindow.show()
        self.mainWindow.raise_()
        #self.mainWindow.setActiveWindow()

    #Fonction appelée lorsqu'il y a un changement entre l'affichage DMS et DD
    #Réalise la traduction DD vers DMS
    def radioDegreeChange(self):
        if self.currentObjPicture.path and self.currentObjPicture.isCoordonate :
            self.changeDegreeType(self.currentObjPicture)
            
    #Fonction appelée par différentes fonctions de l'application
    #Permet de changer la représentation des coordonnées dans le SIG 4326
    #Les représentations possible sont degré décimal et degré, minute, seconde 
    def changeDegreeType(self, objPic) :
        if self.ui.radioButtonDD.isChecked() :
            xstr = str(round(objPic.xStandCoord,5)) + "°" 
            ystr = str(round(objPic.yStandCoord,5)) + "°" 
            self.ui.lineEditXCoordStand.setText(xstr)
            self.ui.lineEditYCoordStand.setText(ystr)
        
        elif self.ui.radioButtonDMS.isChecked() :
            if objPic.xDMS[1] >= 10 :
                strM = str(objPic.xDMS[1])
            else : 
                strM = "0" + str(objPic.xDMS[1])

            if objPic.xDMS[2] >= 10 :
                strS = str(round(objPic.xDMS[2], 1))
            else : 
                strS = "0" + str(round(objPic.xDMS[2], 1))
            
            xstr = str(objPic.xDMS[0]) + "°" + strM + "'" + strS + "''"
            self.ui.lineEditXCoordStand.setText(xstr)
            
            if objPic.yDMS[1] >= 10 :
                strM = str(objPic.yDMS[1])
            else : 
                strM = "0" + str(objPic.yDMS[1])
            
            if objPic.yDMS[2] >= 10 :
                strS = str(round(objPic.yDMS[2], 1))
            else : 
                strS = "0" + str(round(objPic.yDMS[2], 1))
            
            ystr = str(objPic.yDMS[0]) + "°" + strM + "'" + strS + "''"
            self.ui.lineEditYCoordStand.setText(ystr)
        
    #Fonction appelée par le bouton du choix de chemin
    #Ouvre la fenêtre de navigation
    def importDirButton(self):
        #Lié vers le dossier Picture (comment ca fonctionne si en francais?)
        path = join(join(environ['USERPROFILE']), 'Pictures') 
        fname = QtWidgets.QFileDialog.getExistingDirectory(self.mainWindow, 'Import Directory', path)
        if fname:
            self.ui.lineEditRootPath.setText(fname)

    #Fonction appelée lors de l'ouverture d'un nouveau chemin
    #Rafraîchis l'interface utilisateur pour considérer le nouveau chemin
    #Récupère tous les sous dossiers du chemin racine
    #Création d'objet Directory (fichier) pour chaque sous dossiers
    #Lance le traitement du nouveau chemin et de ses sous dossiers
    def newRootPath(self) :

        try : 
            self.ui.treeWidget.clear()
            self.ui.listAvailablePic.clear()
            scene = QtWidgets.QGraphicsScene()
            self.ui.graphicsView.setScene(scene)
            self.ui.lineEditXCoordQGIS.setText("")
            self.ui.lineEditYCoordQGIS.setText("")
            self.ui.lineEditXCoordStand.setText("")
            self.ui.lineEditYCoordStand.setText("")
            self.ui.labelCurrentPic.setText("")
            self.ui.lineEditAltitude.setText("")
            self.ui.lineEditHeading.setText("")
            self.ui.progressBar.setValue(0)
            self.listObjDirectory = []
            self.listObjPicture = []
            self.ui.treeWidget.model().dataChanged.disconnect(self.checkBoxChange)
        except:
            pass

        genWalk = walk(self.ui.lineEditRootPath.text())
        rootDone = False
        for item in genWalk:
            dirPath = item[0].replace("\\","/")
            dirName = dirPath.split("/")[-1]
            
            if rootDone == False :
                treeItem = QtWidgets.QTreeWidgetItem(self.ui.treeWidget, [dirName])
                treeItem.setCheckState(0, QtCore.Qt.Checked) 
                self.rootName = dirName
                rootDone = True
            else :
                dirParentName = dirPath.split("/")[-2]
                treeParentItem = self.ui.treeWidget.findItems(dirParentName, QtCore.Qt.MatchExactly| QtCore.Qt.MatchRecursive)
                if treeParentItem :
                    if len(treeParentItem) == 1 :  
                        treeItem = QtWidgets.QTreeWidgetItem(treeParentItem[0], [dirName])
                        treeItem.setCheckState(0, QtCore.Qt.Checked) 
                    else : 
                        for parent in treeParentItem :
                            for obj in self.listObjDirectory :
                                    if obj.idInTree == id(parent) : 
                                        removePart = "/" + dirName
                                        nb2Remove = -len(removePart)
                                        parentPath = dirPath[:nb2Remove]
                                        if obj.path == parentPath : 
                                            treeItem = QtWidgets.QTreeWidgetItem(parent, [dirName])
                                            treeItem.setCheckState(0, QtCore.Qt.Checked) 
                                            break
                            else :
                                continue
                            break

            objDir = objDirectory(path=dirPath, nameInTree=dirName, idInTree=id(treeItem), isCheck=2)
            self.listObjDirectory.append(objDir)

        
        self.importNewRoot()
        self.ui.treeWidget.expandAll()
        self.ui.pushButtonGPX.setEnabled(True)
        for i in range(self.ui.treeWidget.columnCount()):
            self.ui.treeWidget.resizeColumnToContents(i)
        self.ui.treeWidget.model().dataChanged.connect(self.checkBoxChange)
        self.addCanvasMarker()

    #Fonction qui réalise le traitement des sous dossiers 
    #Récupère les photos des formats acceptés
    #Lance le traitement de la gestion des photos
    def importNewRoot(self):
        currentImportedDir = 0
        if self.listObjDirectory :

            nbDir = len(self.listObjDirectory)
            self.ui.progressBar.setMaximum(nbDir)
            
            for obj in self.listObjDirectory:
                STRbar = " Dossiers traitées " + str(currentImportedDir)  + "/" + str(nbDir)
                self.ui.labelProgress.setText(STRbar)
                self.ui.progressBar.setValue(currentImportedDir)
                self.ui.labelProgress.update()
                self.ui.progressBar.update()
                
                listPicPath = []
                for File in listdir(obj.path):
                    ext = splitext(File)[1]
                    if ext.lower() in fileAcceptFormat : 
                        picturePath = obj.path + "/" + File
                        listPicPath.append(picturePath)
                
                if listPicPath:
                    for path in listPicPath :
                        self.addPictureObject(path, obj)
                currentImportedDir += 1
            
            STRbar = " Dossiers traitées " + str(currentImportedDir)  + "/" + str(nbDir)
            self.ui.labelProgress.setText(STRbar)
            self.ui.progressBar.setValue(currentImportedDir)
    
    #Fonction qui ajoute la photo dans la liste
    #Lance la lecture du EXIF
    def addPictureObject(self, path, objDir) :
        picName = path.split("/")[-1]
        listItem = QtWidgets.QListWidgetItem(picName)
    
        objPic = objPicture(
            path=path, 
            nameInList=picName, 
            idInList=id(listItem), 
            objDir=objDir
        )
        objPic = self.checkExif(objPic)

        if objPic.isCoordonate :
            color = QtGui.QColor(QtCore.Qt.darkGreen)
            listItem.setForeground(QtGui.QBrush(color))
        elif objPic.isEXIF :
            color = QtGui.QColor(QtCore.Qt.red)
            listItem.setForeground(QtGui.QBrush(color))
        else :
            color = QtGui.QColor(QtCore.Qt.darkRed)
            listItem.setForeground(QtGui.QBrush(color))
        
        self.ui.listAvailablePic.addItem(listItem)    
        self.listObjPicture.append(objPic)

    #Fonction appelée lorsqu'un dossier change de type de sélection
    #Retire/Ajoute les photos correspondantes au dossier en question 
    def checkBoxChange(self) :

        treeItems = self.ui.treeWidget.findItems("", QtCore.Qt.MatchContains| QtCore.Qt.MatchRecursive)
        listCheckedPath = []
        nameOfChecked = []
        nbBoxChecked = 0
        for item in treeItems :
            for obj in self.listObjDirectory :
                if obj.idInTree == id(item): 
                    if item.checkState(0) != obj.isCheck : 
                        obj.path
                        if item.checkState(0) == QtCore.Qt.Unchecked :
                            pic2Remove = []
                            for objPic in self.listObjPicture :
                                if objPic.objDir.path == obj.path :
                                    pic2Remove.append(objPic)
                            
                            if pic2Remove :
                                for pic in pic2Remove :
                                    name2Remove = pic.nameInList
                                    item2Remove = self.ui.listAvailablePic.findItems(name2Remove, QtCore.Qt.MatchExactly)
                                    for widgetItem in item2Remove:
                                        if pic.idInList == id(widgetItem) :
                                            row = self.ui.listAvailablePic.row(widgetItem)
                                            self.ui.listAvailablePic.takeItem(row)
                                            break
                                    self.listObjPicture.remove(pic)
                            obj.isCheck = 0 # Checked = 2, Unchecked = 0
                        
                        
                        elif item.checkState(0) == QtCore.Qt.Checked :
                            listPicPath = []
                            for File in listdir(obj.path):
                                ext = splitext(File)[1]
                                if ext.lower() in fileAcceptFormat : 
                                    picturePath = obj.path + "/" + File
                                    listPicPath.append(picturePath)
                                    
                            if listPicPath:
                                for path in listPicPath :
                                    self.addPictureObject(path, obj)
                            obj.isCheck = 2 # Checked = 2, Unchecked = 0
                        
                        break
            else :
                continue
            break
        
        self.addCanvasMarker(refresh=True)

    #Fonction appelée lorsqu'une nouvelle photo est sélectionnée
    #Rafraîchis les information et l'image sur l'interface graphique
    #Rafraîchis le SIG QGIS en cours                
    def newPictureSelection(self, item):

        if self.currentObjPicture.nameInList in self.currentMarkers.keys() : 
            marker = self.currentMarkers[self.currentObjPicture.nameInList]
            marker.setColor(QtGui.QColor(255, 0, 0))
            marker.setIconSize(10)
            marker.setIconType(QgsVertexMarker.ICON_CROSS)
            marker.setPenWidth(10)

        if self.crsQGIS != QgsProject.instance().crs().authid():

            self.crsQGIS = QgsProject.instance().crs().authid()
            
            crsU = QgsCoordinateReferenceSystem(self.crsUniversal)
            crsQ = QgsCoordinateReferenceSystem(self.crsQGIS)
            
            self.coordQ2U = QgsCoordinateTransform(crsQ, crsU, QgsProject.instance())
            self.coordU2Q = QgsCoordinateTransform(crsU, crsQ, QgsProject.instance())
            
            self.ui.labelEPSG.setText(self.crsQGIS)

        for obj in self.listObjPicture :
            if obj.idInList == id(item) :
                objPic = obj
                break
        else :
            return
        self.currentObjPicture = objPic
        self.ui.labelCurrentPic.setText(objPic.path)
        picture = Image.open(objPic.path)

        
        if self.currentObjPicture.nameInList in self.currentMarkers.keys() : 
            marker = self.currentMarkers[self.currentObjPicture.nameInList]
            marker.setColor(QtGui.QColor(0, 0, 255))
            marker.setIconSize(14)
            marker.setIconType(QgsVertexMarker.ICON_CROSS)
            marker.setPenWidth(14)

        self.canvas.refresh()
        
        #Orientation entre 1 et 8, 1 normal, 2,4,5,7 ont un effet mirroir, pas concidérer sauf si j'ai la demande
        if objPic.orientation == 8 :
            newpicture = picture.rotate(90, expand=1)
            picture.close()
            picture = newpicture
        
        elif objPic.orientation == 3 :
            newpicture = picture.rotate(180, expand=0)
            picture.close()
            picture = newpicture
        
        elif objPic.orientation == 6 :
            newpicture = picture.rotate(270, expand=1)
            picture.close()
            picture = newpicture

        if objPic.isCoordonate :
            localCoord = self.coordU2Q.transform(QgsPointXY(objPic.xStandCoord, objPic.yStandCoord))
            xlocalstr = str(round(localCoord[0],1))
            ylocalstr = str(round(localCoord[1],1)) 
            rect = QgsRectangle(QgsPointXY(localCoord[0]+75, localCoord[1]+75), QgsPointXY(localCoord[0]-75, localCoord[1]-75))
            self.canvas.setExtent(rect)
            self.ui.lineEditXCoordQGIS.setText(xlocalstr)
            self.ui.lineEditYCoordQGIS.setText(ylocalstr)
            
            self.changeDegreeType(objPic)

        else : 
            self.ui.lineEditXCoordStand.setText("")
            self.ui.lineEditYCoordStand.setText("")
            self.ui.lineEditXCoordQGIS.setText("")
            self.ui.lineEditYCoordQGIS.setText("")
        
        if objPic.isAltitude :
            self.ui.lineEditAltitude.setText(str(round(objPic.altitude,1))) 
        else :
            self.ui.lineEditAltitude.setText("")

        
        if objPic.isHeading :
            strH = str(round(objPic.heading,1)) + "°"
            self.ui.lineEditHeading.setText(strH) 
        else :
            self.ui.lineEditHeading.setText("") 


        pictureArray = np.array(picture)
        qPicture = array2qimage(pictureArray)
        scene = QtWidgets.QGraphicsScene()
        scene.addPixmap(QtGui.QPixmap.fromImage(qPicture))
        self.ui.graphicsView.setScene(scene)
        rect = QtCore.QRectF(0,0, picture.size[0], picture.size[1])
        self.ui.graphicsView.fitInView(rect, QtCore.Qt.KeepAspectRatio)

        picture.close()

    #Fonction appelée par le bouton Modif. Paramètre
    #Il est possible de modifié manuellement la longitude, latitude et altitude de chaque image
    #Il est possible d'ajouter des coordonnées à une photo qui n'en contient aucune si elle possède un exif
    def changeParameters(self):
        if self.currentObjPicture.path and self.currentObjPicture.isEXIF : 
            if self.activateEditing :

                coordBound = QgsCoordinateReferenceSystem(self.crsQGIS).bounds()
                path = self.currentObjPicture.path

                try : newAlt = float(self.ui.lineEditAltitude.text())
                except : newAlt = None
                
                try : 
                    newLong = float(self.ui.lineEditXCoordQGIS.text())
                    newLat = float(self.ui.lineEditYCoordQGIS.text())
                    coord = self.coordQ2U.transform(QgsPointXY(newLong,newLat))
                    long = coord[0]
                    lat = coord[1]
                except : 
                    lat = None
                    long = None

                objPic = self.writeCoordOnObj(self.currentObjPicture, path, alt=newAlt, long=long, lat=lat)
                self.listObjPicture.remove(self.currentObjPicture)
                self.listObjPicture.append(objPic)
                self.currentObjPicture = objPic
                self.addCanvasMarker(refresh=True)

                

                self.ui.lineEditAltitude.setReadOnly(True)
                self.ui.lineEditXCoordQGIS.setReadOnly(True)
                self.ui.lineEditYCoordQGIS.setReadOnly(True)
                self.ui.pushButtonEdit.setText("Modif. Paramètres")
                self.activateEditing = False
                

            else:
                self.ui.lineEditAltitude.setReadOnly(False)
                #self.ui.lineEditAltitude.setFocus(QtCore.Qt.MouseFocusReason)
                self.ui.lineEditXCoordQGIS.setReadOnly(False)
                #self.ui.lineEditXCoordQGIS.setFocus(QtCore.Qt.MouseFocusReason)
                self.ui.lineEditYCoordQGIS.setReadOnly(False)
                #self.ui.lineEditYCoordQGIS.setFocus(QtCore.Qt.MouseFocusReason)
                self.ui.pushButtonEdit.setText("Écrire Paramètres")
                self.activateEditing = True
        elif self.currentObjPicture.isEXIF == False:
            self.ui.statusbar.showMessage("La photo n'a pas de fichier EXIF", 10000)

    #Fonction appelée par le bouton Copier Paramètres
    #Elle ouvre une liste des images importées
    #L'utilisateur sélectionne les photos sur lesquelles il désire écrire l'information
    #Les informations de la photo qui en cours de sélection seront utilisées
    def openCloneParameters(self) : 
        if self.currentObjPicture.path and self.currentObjPicture.isEXIF : 
            lName=[]
            for i in range(self.ui.listAvailablePic.count()) : lName.append(self.ui.listAvailablePic.item(i).text())
            self.picSelectWindow = getSelectionWindow(lName, heading=True)
            self.picSelectWindow.ui.buttonBox.accepted.connect(self.cloneParameters)
            self.picSelectWindow.ui.buttonBox.rejected.connect(lambda : self.picSelectWindow.close())
            self.picSelectWindow.show()

        elif self.currentObjPicture.isEXIF == False:
            self.ui.statusbar.showMessage("La photo n'a pas de fichier EXIF", 10000)
    
    #Fonction appelée par la fênetre de sélection des images lorsque la sélection est terminé
    #Écris sur le EXIF des photos les nouvelles informations
    def cloneParameters(self) : 

        if self.currentObjPicture.isCoordonate:
            cX = self.currentObjPicture.xStandCoord
            cY = self.currentObjPicture.yStandCoord
        else : cX = cY = None
        if self.currentObjPicture.isAltitude: alt = self.currentObjPicture.altitude
        else : alt = None
        if self.currentObjPicture.isHeading and self.picSelectWindow.ui.checkBox.isChecked() : heading = self.currentObjPicture.heading
        else : heading = None
        
        l2Clone = []
        for i in range(self.picSelectWindow.ui.listWidget.count()) :
            item = self.picSelectWindow.ui.listWidget.item(i)
            if item.checkState() == QtCore.Qt.Checked : l2Clone.append(item.text())
        toRemove = []
        toAdd = []
        for obj in self.listObjPicture : 
            if obj.nameInList in l2Clone :
                path = obj.path
                objPic = self.writeCoordOnObj(obj, path, alt=alt, long=cX, lat=cY, heading=heading)
                toRemove.append(obj)
                toAdd.append(objPic)
        
        for item in toRemove : self.listObjPicture.remove(item)
        for item in toAdd :self.listObjPicture.append(item)
                

        if self.currentObjPicture.isCoordonate:
            for name in l2Clone :
                searchItem = self.ui.listAvailablePic.findItems(name, QtCore.Qt.MatchExactly)
                for i in searchItem :
                    color = QtGui.QColor(QtCore.Qt.darkGreen)
                    i.setForeground(QtGui.QBrush(color))
        
        self.addCanvasMarker(refresh=True)
        self.picSelectWindow.close()

    #Fonction qui permet l'écriture des coordonnées XYZ ainsi que la direction
    #L'écriture se fait sur le EXIF des images
    def writeCoordOnObj(self, obj, path, long=None, lat=None, alt=None, heading=None) : 
        
        pictureExif = piexif.load(path)
        
        if heading :
            direction = (int(round(heading)),1)
            pictureExif['GPS'][piexif.GPSIFD.GPSImgDirectionRef] = 'T'
            pictureExif['GPS'][piexif.GPSIFD.GPSImgDirection] = direction
            obj.isHeading = True
            obj.heading = (direction[0] / direction[1])
        
        if long :
            d = int(long)
            m = int((abs(long) - abs(d))*60)
            s = (abs(long) - abs(d) - (m/60))* 3600 
            xDMS = [d,m,s]
            
            if d > 0 :
                refLong = 'E'
            else :
                refLong = 'W'
            
            deg = (abs(d),1)
            minute = (m,1)
            fractSec = Fraction(s).limit_denominator()
            sec = (fractSec.numerator, fractSec.denominator)

            longitude = (deg,minute,sec)
            
            pictureExif['GPS'][piexif.GPSIFD.GPSLongitudeRef] = refLong
            pictureExif['GPS'][piexif.GPSIFD.GPSLongitude] = longitude
            obj.isCoordonate = True
            obj.xStandCoord = long
            obj.xDMS = xDMS
        
        if lat : 
            d = int(lat)
            m = int((abs(lat) - abs(d))*60)
            s = (abs(lat) - abs(d) - (m/60))* 3600 
            yDMS = [d,m,s]
            
            if d > 0 :
                refLat = 'N'
            else :
                refLat = 'S'
            
            deg = (abs(d),1)
            minute = (m,1)
            fractSec = Fraction(s).limit_denominator()
            sec = (fractSec.numerator, fractSec.denominator)

            latitude = (deg,minute,sec)

            pictureExif['GPS'][piexif.GPSIFD.GPSLatitudeRef] = refLat
            pictureExif['GPS'][piexif.GPSIFD.GPSLatitude] = latitude

            obj.yStandCoord = lat
            obj.yDMS = yDMS
            obj.isCoordonate = True

        if alt : 
            fractAlt = Fraction(alt).limit_denominator()
            altitude = (fractAlt.numerator, fractAlt.denominator)

            pictureExif['GPS'][piexif.GPSIFD.GPSAltitude] = altitude
            obj.altitude = alt
            obj.isAltitude = True

        exif_bytes = piexif.dump(pictureExif)
        piexif.insert(exif_bytes, path)
        return obj
    
    #Fonction appelée pour activer/désactiver la visualisation des points
    def actionPositionMarker(self) : 
        if self.ui.checkBoxShowPosition.isChecked() : self.addCanvasMarker()
        else : self.removeCanvasMarker()

    #Fonction qui ajoute des points dans QGIS pour informer de la position des images importées
    #Lorsqu'une image est sélectionnée sont point change de couleur et devient plus grand
    def addCanvasMarker(self, refresh=False) :
        
        if refresh : self.removeCanvasMarker()

        for objPic in self.listObjPicture :

            if objPic.isCoordonate : 
                
                localCoord = self.coordU2Q.transform(QgsPointXY(objPic.xStandCoord, objPic.yStandCoord))
                
                if localCoord in self.markerPositions.keys() : 
                    self.currentMarkers[objPic.nameInList] =  self.currentMarkers[self.markerPositions[localCoord]]
                    continue

                marker = QgsVertexMarker(self.canvas)
                marker.setCenter(localCoord)
                marker.setColor(QtGui.QColor(255, 0, 0))
                marker.setIconSize(10)
                marker.setIconType(QgsVertexMarker.ICON_CROSS)
                marker.setPenWidth(10)
                
                self.currentMarkers[objPic.nameInList] = marker
                self.markerPositions[localCoord] = objPic.nameInList
    
    #Fonction qui retire les points dans QGIS
    def removeCanvasMarker(self) : 
        #print(self.canvas.renderedItemResults())
        #print(len(self.canvas.renderedItemResults().renderedItems()))
        #print(list(self.markerPositions.keys())[0])
        #for item in self.canvas.scene().items() :
        #    center = QgsPointXY(item.x(), item.y())
        #    if center in self.markerPositions.keys() :
        #        self.canvas.scene().removeItem(item)
        for marker in self.currentMarkers.values() :
            try : self.canvas.scene().removeItem(marker)
            except : pass
        self.currentMarkers = {}
        self.markerPositions = {} 
        #print(self.canvas.renderedItemResults())
        #print(len(self.canvas.renderedItemResults().renderedItems()))
    
    #Fonction appelé par le bouton Générer Shapefile de points
    #Permet de choisir les images que l'on voudrait inclure dans le shapefile (de base elles le sont tous)
    #Il faut choisir le nom du fichier
    def openShapefileSelection(self):
        lName=[]
        for i in range(self.ui.listAvailablePic.count()) : lName.append(self.ui.listAvailablePic.item(i).text())
        self.shpSelectWindow = getSelectionWindow(lName, shpName=True, setTrue=lName)
        self.shpSelectWindow.ui.buttonBox.accepted.connect(self.generateShapefile)
        self.shpSelectWindow.ui.buttonBox.rejected.connect(lambda : self.shpSelectWindow.close())
        self.shpSelectWindow.show()
    
    #Fonction qui génère le fichier de point et l'importe dans QGIS 
    #Le sig choisi est celui en cours dans QGIS
    def generateShapefile(self) : 
        filePath = join(self.ui.lineEditRootPath.text(), self.shpSelectWindow.ui.lineEdit.text() +'.shp')
        if not exists(filePath) :

            fields = QgsFields()
            fields.append(QgsField("Name", QtCore.QVariant.String))
            crsQ = QgsCoordinateReferenceSystem(self.crsQGIS)
            
            vectorWriter = QgsVectorFileWriter(filePath, "System", fields, QgsWkbTypes.MultiPoint, crsQ, "ESRI Shapefile")
                
            l2Use = []
            for i in range(self.shpSelectWindow.ui.listWidget.count()) :
                item = self.shpSelectWindow.ui.listWidget.item(i)
                if item.checkState() == QtCore.Qt.Checked : l2Use.append(item.text())
            
            for obj in self.listObjPicture : 
                if obj.nameInList in l2Use and obj.isCoordonate :
                    localCoord = self.coordU2Q.transform(QgsPointXY(obj.xStandCoord, obj.yStandCoord))
                    feature = QgsFeature(fields)
                    feature.setAttribute(0,obj.nameInList)
                    geo = QgsGeometry.fromPointXY(QgsPointXY(localCoord[0],localCoord[1]))
                    feature.setGeometry(geo)
                    vectorWriter.addFeature(feature)
            vectorWriter = None
            self.iface.addVectorLayer(filePath, self.shpSelectWindow.ui.lineEdit.text(), "ogr")
        self.shpSelectWindow.close()
    

    #Fonction qui réalise l'analyse de l'EXIF d'une photo
    #Récupère, si possible, la rotation, le temps original, latitude, longitude, altitude, orientation
    def checkExif(self, obj):
        
        try : 
            pictureExif = piexif.load(obj.path)
            obj.isEXIF = True
        except : 
            return obj
            

        try :
            orientation = pictureExif['0th'][piexif.ImageIFD.Orientation] 
            obj.orientation = orientation
        except : pass

        try :
            time = pictureExif['Exif'][piexif.ExifIFD.DateTimeOriginal]
            obj.time = time
        except : pass

        try :
            latitude = pictureExif["GPS"][piexif.GPSIFD.GPSLatitude]
            deg= latitude[0][0]/latitude[0][1]
            minute = (latitude[1][0]/latitude[1][1])/60.0
            sec = (latitude[2][0]/latitude[2][1])/3600.0
            Nord = deg + minute + sec
            
            d = int(Nord)
            m = int((Nord - d)*60)
            s = (Nord - d - (m/60))* 3600
            
            if  pictureExif["GPS"][piexif.GPSIFD.GPSLatitudeRef] == b"S":
                Nord *= -1 
                d *= -1
            
            obj.yDMS = [d, m, s]
            obj.yStandCoord = Nord
            
            longitude = pictureExif['GPS'][piexif.GPSIFD.GPSLongitude]
            deg= longitude[0][0]/longitude[0][1]
            minute = (longitude[1][0]/longitude[1][1])/60.0
            sec = (longitude[2][0]/longitude[2][1])/3600.0
            Est = deg + minute + sec
            
            d = int(Est)
            m = int((Est - d)*60)
            s = (Est - d - (m/60))* 3600      
            
            if pictureExif["GPS"][piexif.GPSIFD.GPSLongitudeRef] == b"W":
                Est *= -1
                d *= -1
            
            obj.xDMS = [d, m, s]
            obj.xStandCoord = Est
            
            obj.isCoordonate = True
        except : pass
            
        try : 
            altitude = pictureExif["GPS"][piexif.GPSIFD.GPSAltitude]
            obj.altitude = altitude[0]/altitude[1]
            obj.isAltitude = True
        except : pass


        try :
            #Concidérer GPSImgDirectionRef Trouver quoi faire si pas T
            direction = pictureExif["GPS"][piexif.GPSIFD.GPSImgDirection]
            obj.heading = direction[0] / direction[1]
            obj.isHeading = True
        except : pass            

        return obj


#Classe de l'objet lié à un dossier
#Contiens le chemin du dossier, le nom du dossier, le id du nom et le bool de la sélection
class objDirectory:
    def __init__(self, path="", nameInTree="", idInTree=0, isCheck=0):
        self.path = path
        self.nameInTree = nameInTree
        self.idInTree = idInTree
        self.isCheck = isCheck # Checked = 2, unchecked = 0

#Classe de l'objet lié à une photo
#Contiens le chemin, le nom de la photo, le id du nom, l'objet lié au dossier, la présence d'un EXIF,
#le code de rotation, le temps, la présence de coordonnées, longitude, latitude,
#la présence de l'altitude, l'altitude, la présence de l'orientation et l'orientation
class objPicture:
    def __init__(self, path="", 
            nameInList="", 
            idInList=0, 
            objDir=objDirectory(), 
            isEXIF=False, 
            orientation=1,
            time = b'', 
            isCoordonate=False,
            xStandCoord=0.0, 
            yStandCoord=0.0,
            isAltitude=False,
            altitude=0.0, 
            isHeading=False, 
            heading=0.0):
        
        self.path = path
        self.nameInList = nameInList
        self.idInList = idInList
        self.objDir = objDir
        self.isEXIF = isEXIF
        self.orientation = orientation
        self.time = time
        self.isCoordonate = isCoordonate
        self.xStandCoord = xStandCoord
        d = int(self.xStandCoord)
        m = int((abs(self.xStandCoord) - abs(d))*60)
        s = (abs(self.xStandCoord) - abs(d) - (m/60))* 3600 
        self.xDMS = [d,m,s]
        self.yStandCoord = yStandCoord
        d = int(self.yStandCoord)
        m = int((abs(self.yStandCoord) - abs(d))*60)
        s = (abs(self.yStandCoord) - abs(d) - (m/60))* 3600 
        self.yDMS = [d,m,s]
        self.isAltitude = isAltitude
        self.altitude = altitude
        self.isHeading = isHeading
        self.heading = heading



