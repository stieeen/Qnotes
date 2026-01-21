from qgis.core import *
import processing

conic_proj4 = "+proj=eqdc +lat_0=0 +lon_0=100 +lat_1=46.4 +lat_2=71.8 +x_0=0 +y_0=0 +ellps=GSK2011 +units=m +no_defs"
conic_crs = QgsCoordinateReferenceSystem()
conic_crs.createFromProj4(conic_proj4)
QgsProject.instance().setCrs(conic_crs)

active_id = iface.activeLayer().id() if iface.activeLayer() else None

line = QgsVectorLayer("LineString?crs=epsg:4326", "temp", "memory")
f = QgsFeature(); f.setGeometry(QgsGeometry.fromWkt("LINESTRING(180 -90, 180 90)"))
line.dataProvider().addFeature(f)

line = processing.run("native:reprojectlayer", {'INPUT': line, 'TARGET_CRS': conic_crs, 'OUTPUT': 'memory:'})['OUTPUT']

buffer = processing.run("native:buffer", {'INPUT': line, 'DISTANCE': 0.0001, 'SEGMENTS': 5, 'OUTPUT': 'memory:'})['OUTPUT']
QgsProject.instance().addMapLayer(buffer)
QgsProject.instance().removeMapLayer(line.id())

target_layer = QgsProject.instance().mapLayer(active_id)
if target_layer and target_layer.geometryType() == QgsWkbTypes.PolygonGeometry:
    diff = processing.run("native:difference", {'INPUT': target_layer, 'OVERLAY': buffer, 'OUTPUT': 'memory:'})['OUTPUT']
    
    temp = QgsVectorLayer(f"Polygon?crs={diff.crs().authid()}", "temp_no_fid", "memory")
    
    new_fields = []
    for field in diff.fields():
        if field.name().lower() != 'fid':
            new_fields.append(field)
    temp.dataProvider().addAttributes(new_fields)
    temp.updateFields()
    
    features = []
    for feat in diff.getFeatures():
        new_feat = QgsFeature(temp.fields())
        for field in new_fields:
            new_feat.setAttribute(field.name(), feat.attribute(field.name()))
        new_feat.setGeometry(feat.geometry())
        features.append(new_feat)
    
    temp.dataProvider().addFeatures(features)
    
    parts = processing.run("native:multiparttosingleparts", {'INPUT': temp, 'OUTPUT': 'memory:'})['OUTPUT']
    parts.setName(f"{target_layer.name()}_cut")
    QgsProject.instance().addMapLayer(parts)
    
    QgsProject.instance().removeMapLayer(buffer.id())
