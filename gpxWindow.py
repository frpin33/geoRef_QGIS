from PyQt5 import QtCore, QtGui, QtWidgets
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
from .ui_importGPXWindow import Ui_gpxWindow

from . import resources


class gpxWindow(QtWidgets.QMainWindow):
    applyGPXDone = QtCore.pyqtSignal(list)
    def __init__(self, rootPath, listPictureObj):
        super(gpxWindow, self).__init__()
        self.ui = Ui_gpxWindow()
        self.ui.setupUi(self)
        self.ui.toolButtonGPX.clicked.connect(self.importGPXButton)
        self.ui.lineEditPathGPX.textChanged.connect(self.newGPXPath)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.rootPath = rootPath
        self.listPictureObj = listPictureObj
        #self.ui.buttonBox.rejected.connect(self.closeEvent)

    def importGPXButton(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, 'Import GPX File', self.rootPath,"GPX (*.gpx)")[0]
        if fname :
            self.ui.lineEditPathGPX.setText(fname)

    def newGPXPath(self):
        path = self.ui.lineEditPathGPX.text()
        if path.split('.')[-1] == "gpx":
            self.gpxPath = path
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            self.ui.buttonBox.accepted.connect(self.addCoordFromGPX)
        else : 
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
            self.ui.lineEditPathGPX.setText('')

    def addCoordFromGPX(self):
        secInterpol = self.ui.spinBoxInterpol.value()
        utc = self.ui.currentUTC
        secDecalage = self.ui.spinBoxDecalage.value()
        
        path_gpx = self.gpxPath + "|layername=track_points"
        vLayer = QgsVectorLayer(path_gpx, "ogr")

        currentPBarValue = 0
        nbObj = len(self.listPictureObj)
        self.ui.progressBar.setMaximum(nbObj)
        
        self.newListPictureObj = []

        for obj in self.listPictureObj :
            if obj.isCoordonate and self.ui.checkBoxKeep.isChecked() :
                pass 
            elif obj.time and obj.isEXIF :
                #time = b'YYYY:MM:DD HH:MM:SS'
                strTime = obj.time.decode()
                objDate = QtCore.QDate(int(strTime[0:4]), int(strTime[5:7]), int(strTime[8:10]))

                timeofDay = int(strTime[11:13])*3600 + int(strTime[14:16])*60 + int(strTime[17:19])
                timeUp = timeofDay+secInterpol
                timeDown = timeofDay-secInterpol
                listGeometry = []
                for feature in vLayer.getFeatures():
                    try :
                        featTimeAttr = feature.attribute('time')
                    except :
                        pass
                    else :
                        if featTimeAttr.date() == objDate : 
                            fTime = featTimeAttr.time()
                            timeofFeat = (fTime.hour()+utc)*3600 + fTime.minute()*60 + fTime.second() + secDecalage
                            if timeofFeat > timeDown and timeofFeat < timeUp :
                                listGeometry.append(feature.geometry())
                
                #Très important de vérifié la compatibilité, fonctionne pour mon GPX, en général toujours le cas
                
                if listGeometry :
                    
                    
                    nbHit = len(listGeometry)
                    sumXValue = 0.0
                    sumYValue = 0.0
                    sumZValue = 0.0
                    
                    for geo in listGeometry:
                        sumXValue += geo.get().x()
                        sumYValue += geo.get().y()
                        sumZValue += geo.get().z()
                    
                    pictureExif = piexif.load(obj.path)
                    
                    xCoord = sumXValue/nbHit
                    
                    
                    d = int(xCoord)
                    m = int((abs(xCoord) - abs(d))*60)
                    s = (abs(xCoord) - abs(d) - (m/60))* 3600 
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
                    
                    yCoord = sumYValue/nbHit
                    
                    d = int(yCoord)
                    m = int((abs(yCoord) - abs(d))*60)
                    s = (abs(yCoord) - abs(d) - (m/60))* 3600 
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
                    
                    zCoord = sumZValue/nbHit

                    fractAlt = Fraction(zCoord).limit_denominator()
                    altitude = (fractAlt.numerator, fractAlt.denominator)

                    pictureExif['GPS'][piexif.GPSIFD.GPSAltitude] = altitude

                    obj.isCoordonate = True
                    obj.xStandCoord = xCoord
                    obj.xDMS = xDMS
                    obj.yStandCoord = yCoord
                    obj.yDMS = yDMS
                    obj.isAltitude = True
                    obj.altitude = zCoord

                    exif_bytes = piexif.dump(pictureExif)
                    piexif.insert(exif_bytes, obj.path)


            currentPBarValue += 1
            self.ui.progressBar.setValue(currentPBarValue)
            self.ui.progressBar.update()     
            self.newListPictureObj.append(obj)       

        self.applyGPXDone.emit(self.newListPictureObj)

        

