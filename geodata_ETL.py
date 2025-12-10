from qgis.core import QgsVectorLayer, QgsFeature, QgsProject, QgsVectorFileWriter, QgsCoordinateReferenceSystem
from qgis import processing
vector = QgsProject.instance().mapLayersByName("izuch_Area")[0]
csv = QgsProject.instance().mapLayersByName("izuch")[0]
join_field = csv.fields()[0].name()
csv_index = {}
