#Fichier utiliser par QGIS pour lancer l'application
def classFactory(iface):
    from .geoRefWindow import geoRefWindow
    return geoRefWindow(iface)
