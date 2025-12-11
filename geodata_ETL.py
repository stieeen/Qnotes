from qgis.core import QgsVectorLayer, QgsFeature, QgsProject, QgsVectorFileWriter, QgsCoordinateReferenceSystem
from qgis import processing

vector = QgsProject.instance().mapLayersByName("izuch_A")[0]
csv = QgsProject.instance().mapLayersByName("izuch")[0]
join_field = csv.fields()[0].name()
csv_index = {}
for feat in csv.getFeatures():
    val = feat[join_field]
    if val:
        key = str(val).strip()
        csv_index[key] = feat
new_layer = QgsVectorLayer("Polygon", "izuch_joined", "memory")
provider = new_layer.dataProvider()

provider.addAttributes(vector.fields())
for field in csv.fields():
    if field.name() != join_field:
        provider.addAttributes([field])
new_layer.updateFields()

features = []
for v_feat in vector.getFeatures():
    n_feat = QgsFeature(new_layer.fields())
    n_feat.setGeometry(v_feat.geometry())
    
    for field in vector.fields():
        n_feat[field.name()] = v_feat[field.name()]
    
    search_key = str(v_feat["ukID"]).strip()
    
    if search_key in csv_index:
        c_feat = csv_index[search_key]
        for field in csv.fields():
            if field.name() != join_field:
                n_feat[field.name()] = c_feat[field.name()]
    
    features.append(n_feat)

provider.addFeatures(features)

output_path = r"\\crat\GIS\NextGIS\GPKG\izuch_joined.gpkg"

pulkovo_crs = QgsCoordinateReferenceSystem("EPSG:4284")

QgsVectorFileWriter.writeAsVectorFormat(
    new_layer,
    output_path,
    "UTF-8",
    pulkovo_crs,
    "GPKG"
)

saved_layer = QgsVectorLayer(output_path, "izuch_joined", "ogr")
QgsProject.instance().addMapLayer(saved_layer)

layer = saved_layer

check_result = processing.run("qgis:checkvalidity", {
    'INPUT_LAYER': layer,
    'METHOD': 2,
    'IGNORE_RING_SELF_INTERSECTION': False,
    'VALID_OUTPUT': 'memory:',
    'INVALID_OUTPUT': 'memory:',
    'ERROR_OUTPUT': 'memory:'
})

if check_result['INVALID_OUTPUT'].featureCount() > 0:
    fixed_result = processing.run("native:fixgeometries", {
        'INPUT': layer,
        'METHOD': 1,
        'OUTPUT': 'memory:'
    })
    layer = fixed_result['OUTPUT']

clean_layer = QgsVectorLayer("Polygon", "temp", "memory")
provider_clean = clean_layer.dataProvider()

columns_to_delete = ["field_14", "IDотчетаРГФ", "nom_1000", "name_otch", 
                     "god_end", "god_nach", "in_n_tgf", "in_n_rosg", "tgf", "vid_name"]

for field in layer.fields():
    if field.name() not in columns_to_delete:
        provider_clean.addAttributes([field])

clean_layer.updateFields()

features_clean = []
for feat in layer.getFeatures():
    new_feat = QgsFeature(clean_layer.fields())
    new_feat.setGeometry(feat.geometry())
    
    for field in clean_layer.fields():
        field_name = field.name()
        new_feat[field_name] = feat[field_name]
    
    features_clean.append(new_feat)

provider_clean.addFeatures(features_clean)

clean_file = r"\\cr\GIS\NextGIS\GPKG\izuch_joined_clean.gpkg"

QgsVectorFileWriter.writeAsVectorFormat(
    clean_layer,
    clean_file,
    "UTF-8",
    QgsCoordinateReferenceSystem("EPSG:4284"),
    "GPKG"
)
saved_clean_layer = QgsVectorLayer(clean_file, "izuch_joined_clean", "ogr")
if saved_clean_layer.isValid():
    QgsProject.instance().addMapLayer(saved_clean_layer)   
    actual_layer_name = saved_clean_layer.name()
    check = processing.run("qgis:checkvalidity", {
        'INPUT_LAYER': saved_clean_layer,
        'METHOD': 2,
        'VALID_OUTPUT': 'TEMPORARY_OUTPUT',
        'INVALID_OUTPUT': 'TEMPORARY_OUTPUT',
        'ERROR_OUTPUT': 'TEMPORARY_OUTPUT'
    })
    if check['INVALID_OUTPUT'].featureCount() > 0:
        fixed = processing.run("native:fixgeometries", {
            'INPUT': saved_clean_layer,
            'OUTPUT': clean_file.replace(".gpkg", "_fixed.gpkg")
        })
        fixed_layer = QgsVectorLayer(fixed['OUTPUT'], "izuch_fixed", "ogr")
        if fixed_layer.isValid():
            QgsProject.instance().addMapLayer(fixed_layer)
