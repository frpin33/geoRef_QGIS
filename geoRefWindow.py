# https://exiv2.org/tags.html TAGS EXIT
# https://exiv2.org/iptc.html TAGS IPTC
# https://exiv2.org/tags-xmp-dc.html TAGS XMP

from qgis.gui import *
from qgis.core import *
from qgis.PyQt import QtCore, QtGui, QtWidgets

from os.path import splitext, dirname, abspath, join
from os import walk, listdir, environ, remove
from fractions import Fraction
from qimage2ndarray import array2qimage
from PIL import Image
import numpy as np
import piexif
#from iptcinfo3 import IPTCInfo

from .ui_geoRefWindow import Ui_geoRefMainWindow
from .gpxWindow import gpxWindow

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
        

        self.ui.pushButtonGPX.clicked.connect(self.actionClickGPX)
        self.ui.pushButtonClick.clicked.connect(self.actionClickCanvas)
        self.ui.pushButtonAltitude.clicked.connect(self.changeAltitude)
        self.ui.radioButtonDD.toggled.connect(self.changeDegreeType)
        self.isEditingAltitude = False

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

    def closeMainWindow(self,ev):
        if hasattr(self, 'pinkCross'):
            self.canvas.scene().removeItem(self.pinkCross)
        if hasattr(self, 'redLine'):
                self.canvas.scene().removeItem(self.redLine)


    def actionClickGPX(self):
        path = self.ui.lineEditRootPath.text()
        self.gpxUI = gpxWindow(path, self.listObjPicture)
        strLabel = 'Le traitement s\'appliquera sur les ' + str(len(self.listObjPicture))  + ' photos sélectionnées.'
        self.gpxUI.ui.labelNbSelect.setText(strLabel)
        self.gpxUI.ui.buttonBox.rejected.connect(self.closeGPXWindow)
        self.gpxUI.applyGPXDone.connect(self.applyGPXDone)
        self.gpxUI.show()

    def closeGPXWindow(self):
        self.gpxUI.close()
    
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
        
        self.newPictureSelection(firstItem) 
        self.ui.listAvailablePic.setCurrentItem(firstItem)
        


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
            self.ui.pushButtonApplyClick.clicked.disconnect(self.applyClickCanvas)
        except :
            pass

        self.ui.pushButtonClick.setEnabled(False)

        self.ui.pushButtonCancelClick.setEnabled(True)
        self.ui.pushButtonCancelClick.clicked.connect(self.cancelClickCanvas)

        self.itemInEdit = self.ui.listAvailablePic.currentItem()
        self.ui.listAvailablePic.itemClicked.disconnect(self.newPictureSelection)
        self.ui.listAvailablePic.itemClicked.connect(self.keepCurrentSelection)
    
    def keepCurrentSelection(self, item):
        self.ui.listAvailablePic.setCurrentItem(self.itemInEdit)

    def cancelClickCanvas(self):

        self.ui.pushButtonApplyClick.setEnabled(False)
        self.ui.pushButtonCancelClick.setEnabled(False)
        self.ui.pushButtonClick.setEnabled(True)
        
        self.ui.listAvailablePic.itemClicked.disconnect(self.keepCurrentSelection)
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
            
            if self.ui.radioButtonDD.isChecked() :
                xstr = str(round(objPic.xStandCoord,4)) + "°" 
                ystr = str(round(objPic.yStandCoord,4)) + "°" 
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

    def applyClickCanvas(self) :

        try :
            path = self.currentObjPicture.path

            pictureExif = piexif.load(path)
            objPic = self.currentObjPicture
            
            if self.headingClick >= 0 :
                direction = (int(round(self.headingClick)),1)
                pictureExif['GPS'][piexif.GPSIFD.GPSImgDirectionRef] = 'T'
                pictureExif['GPS'][piexif.GPSIFD.GPSImgDirection] = direction
                objPic.isHeading = True
                objPic.heading = int(round(self.headingClick))
            
            xStandCoord = self.clicInitCoord[0]
            d = int(xStandCoord)
            m = int((abs(xStandCoord) - abs(d))*60)
            s = (abs(xStandCoord) - abs(d) - (m/60))* 3600 
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
            
            yStandCoord = self.clicInitCoord[1]
            d = int(yStandCoord)
            m = int((abs(yStandCoord) - abs(d))*60)
            s = (abs(yStandCoord) - abs(d) - (m/60))* 3600 
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
            
            
            objPic.isCoordonate = True
            objPic.xStandCoord = xStandCoord
            objPic.xDMS = xDMS
            objPic.yStandCoord = yStandCoord
            objPic.yDMS = yDMS

            exif_bytes = piexif.dump(pictureExif)
            piexif.insert(exif_bytes, path)

            color = QtGui.QColor(QtCore.Qt.darkGreen)
            self.ui.listAvailablePic.currentItem().setForeground(QtGui.QBrush(color))
            
            self.listObjPicture.append(objPic)
            self.listObjPicture.remove(self.currentObjPicture)
            self.currentObjPicture = objPic

            #info = IPTCInfo(path, force=True)
            #info['keywords'].append('coordonnées approximatives')
            #info.save_as(path)
            #print(info.inp_charset)
            #print(info.out_charset)
            #path2Remove = path + "~"
            #remove(path2Remove)
        
        except :
            pass

        self.cancelClickCanvas()

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
        
        if self.ui.radioButtonDD.isChecked() :
            xstr = str(round(self.clicInitCoord[0],4)) + "°" 
            ystr = str(round(self.clicInitCoord[1],4)) + "°" 
            self.ui.lineEditXCoordStand.setText(xstr)
            self.ui.lineEditYCoordStand.setText(ystr)
        
        elif self.ui.radioButtonDMS.isChecked() :
            d = int(self.clicInitCoord[0])
            m = int((abs(self.clicInitCoord[0]) - abs(d))*60)
            
            if m >= 10 :
                strM = str(m)
            else : 
                strM = "0" + str(m)
            
            s = (abs(self.clicInitCoord[0]) - abs(d) - (m/60))* 3600 
            
            if s >= 10 :
                strS = str(round(s, 1))
            else : 
                strS = "0" + str(round(s, 1))
            
            xstr = str(d) + "°" + strM + "'" + strS + "''"
            self.ui.lineEditXCoordStand.setText(xstr)
            
            d = int(self.clicInitCoord[1])
            m = int((abs(self.clicInitCoord[1]) - abs(d))*60)
            
            if m >= 10 :
                strM = str(m)
            else : 
                strM = "0" + str(m)
            
            s = (abs(self.clicInitCoord[1]) - abs(d) - (m/60))* 3600 
        
            if s >= 10 :
                strS = str(round(s, 1))
            else : 
                strS = "0" + str(round(s, 1))

            ystr = str(d) + "°" + strM + "'" + strS + "''"
            self.ui.lineEditYCoordStand.setText(ystr)

        self.isPressed = True
        if self.currentObjPicture.path and self.currentObjPicture.isEXIF :
            self.ui.pushButtonApplyClick.setEnabled(True)
            self.ui.pushButtonApplyClick.clicked.connect(self.applyClickCanvas)


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


    def canvasRelease(self, ev):
        self.isPressed = False

    def changeDegreeType(self):

        if self.currentObjPicture.path and self.currentObjPicture.isCoordonate :
            objPic = self.currentObjPicture
            if self.ui.radioButtonDD.isChecked() :
                xstr = str(round(objPic.xStandCoord,4)) + "°" 
                ystr = str(round(objPic.yStandCoord,4)) + "°" 
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
        

    def importDirButton(self):
        #Lié vers le dossier Picture (comment ca fonctionne si en francais?)
        path = join(join(environ['USERPROFILE']), 'Pictures') 
        fname = QtWidgets.QFileDialog.getExistingDirectory(self.mainWindow, 'Import Directory', path)
        if fname:
            self.ui.lineEditRootPath.setText(fname)

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
                    
    def newPictureSelection(self, item):
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
            self.ui.lineEditXCoordQGIS.setText(xlocalstr)
            self.ui.lineEditYCoordQGIS.setText(ylocalstr)
            
            if self.ui.radioButtonDD.isChecked() :
                xstr = str(round(objPic.xStandCoord,4)) + "°" 
                ystr = str(round(objPic.yStandCoord,4)) + "°" 
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

    def changeAltitude(self):
        if self.currentObjPicture.path and self.currentObjPicture.isEXIF : 
            if self.isEditingAltitude :
                try :
                    path = self.currentObjPicture.path
                    newAlt = float(self.ui.lineEditAltitude.text())
                    
                    
                    pictureExif = piexif.load(path)

                    #Possibilité de réduire la limite si bug
                    fractAlt = Fraction(newAlt).limit_denominator()
                    altitude = (fractAlt.numerator, fractAlt.denominator)

                    pictureExif['GPS'][piexif.GPSIFD.GPSAltitude] = altitude

                    exif_bytes = piexif.dump(pictureExif)
                    piexif.insert(exif_bytes, path)

                    objPic = self.currentObjPicture
                    objPic.altitude = newAlt
                    self.listObjPicture.append(objPic)
                    self.listObjPicture.remove(self.currentObjPicture)
                    self.currentObjPicture = objPic

                except :
                    pass

                self.ui.lineEditAltitude.setReadOnly(True)
                self.ui.pushButtonAltitude.setText("Edit Altitude")
                self.isEditingAltitude = False

            else:
                self.ui.lineEditAltitude.setReadOnly(False)
                self.ui.lineEditAltitude.setFocus(QtCore.Qt.MouseFocusReason)
                self.ui.pushButtonAltitude.setText("Apply Altitude")
                self.isEditingAltitude = True
        elif self.currentObjPicture.isEXIF == False:
            self.ui.statusbar.showMessage("La photo n'a pas de fichier EXIF", 10000)

    def checkExif(self, obj):
        
        try : 
            pictureExif = piexif.load(obj.path)
            obj.isEXIF = True
        except : 
            return obj
            

        try :
            orientation = pictureExif['0th'][piexif.ImageIFD.Orientation] 
            obj.orientation = orientation
        except :
            pass

        try :
            time = pictureExif['Exif'][piexif.ExifIFD.DateTimeOriginal]
            obj.time = time
        except:
            pass

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
        except :
            pass

        try : 
            altitude = pictureExif["GPS"][piexif.GPSIFD.GPSAltitude]
            obj.altitude = altitude[0]/altitude[1]
            obj.isAltitude = True
        except :
            pass


        try :
            #Concidérer GPSImgDirectionRef Trouver quoi faire si pas T
            direction = pictureExif["GPS"][piexif.GPSIFD.GPSImgDirection]
            obj.heading = direction[0] / direction[1]
            obj.isHeading = True
        except :
            pass            

        return obj

class objDirectory:
    def __init__(self, path="", nameInTree="", idInTree=0, isCheck=0):
        self.path = path
        self.nameInTree = nameInTree
        self.idInTree = idInTree
        self.isCheck = isCheck # Checked = 2, unchecked = 0

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
        self.xDMS = [0.0, 0.0, 0.0]
        self.yStandCoord = yStandCoord
        self.yDMS = [0.0, 0.0, 0.0]
        self.isAltitude = isAltitude
        self.altitude = altitude
        self.isHeading = isHeading
        self.heading = heading



