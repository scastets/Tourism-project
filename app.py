# Import des librairies 
import folium
from geopy.geocoders import Nominatim
import osmnx as ox
import networkx as nx
from shapely.geometry import LineString
import geopandas as gpd
import pandas as pd


# ------------------------------------------ # 
# --- Initialisations point A et point B --- # 
# ------------------------------------------ #
# Initialisation du géocodeur
geolocator = Nominatim(user_agent="apptourism")

# Adresse point A 
address_pt_A = "57 Rue de l'université, Paris"

# Géocodage
location_pt_A = geolocator.geocode(address_pt_A)

if location_pt_A is None:
    raise ValueError("Adresse point A introuvable")
else: 
    lat_pt_A, lon_pt_A = location_pt_A.latitude, location_pt_A.longitude

print(f"- POINT A : {location_pt_A.address} \n -> coordonnées : ({lat_pt_A}, {lon_pt_A})")


# # Adresse point B 
# address_pt_B = "38 Cr Albert 1er, Paris"

# # Géocodage
# location_pt_B = geolocator.geocode(address_pt_B)

# if location_pt_B is None:
#     raise ValueError("Adresse point A introuvable")
# else: 
#     lat_pt_B, lon_pt_B = location_pt_B.latitude, location_pt_B.longitude

# print(f"- POINT B : {location_pt_B.address} \n -> coordonnées : ({lat_pt_B}, {lon_pt_B})")
lat_pt_B, lon_pt_B = 48.86486074362772, 2.3046092778933756

# ------------------------------------------ # 
# ---   Calcul itinéraire entre A et B   --- # 
# ------------------------------------------ #
# Points
point_A = (lat_pt_A, lon_pt_A)
point_B = (lat_pt_B, lon_pt_B)

# Calcul de la distance pour définir la zone
distance = ox.distance.great_circle(lat_pt_A, lon_pt_A, lat_pt_B, lon_pt_B)

# Réseau routier autour de la zone
G = ox.graph_from_point(point_A, dist=distance * 1.5, network_type='drive')

# Noeux du réseau les plus proches des points A et B
orig_node = ox.distance.nearest_nodes(G, lon_pt_A, lat_pt_A)
dest_node = ox.distance.nearest_nodes(G, lon_pt_B, lat_pt_B)

# Calcul de l'itinéraire le plus court 
route = nx.shortest_path(G, orig_node, dest_node, weight='length')

# Extraction coordonnées du chemin 
route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in route]


# ------------------------------------------ # 
# ---   Extrations quartiers traversés   --- # 
# ------------------------------------------ #
route_line = LineString([(lon, lat) for lat, lon in route_coords])
quartiers = ox.features_from_point(
    point_A, 
    tags={'admin_level': '10'}, 
    dist=distance
)

quartiers_gdf = gpd.GeoDataFrame(quartiers, geometry='geometry', crs='EPSG:4326')
quartiers_traverses = quartiers_gdf[quartiers_gdf.intersects(route_line)]


# ------------------------------------------ # 
# ---  Extrations des points d'intêrets  --- # 
# ------------------------------------------ #
poi_list = []

for idx, row in quartiers_traverses.iterrows():
    if not pd.isna(row.short_name):
        # récupérer les POI dans le polygone
        pois = ox.features_from_polygon(
            row.geometry,
            tags={'tourism': 'attraction', 
                'historic': 'monument'}  # monuments / sites touristiques
        )
        if not pois.empty:
            poi_list.append(pois)

# Combiner tous les GeoDataFrames en un seul
if poi_list:
    pois_gdf = gpd.GeoDataFrame(pd.concat(poi_list, ignore_index=True))
else:
    pois_gdf = gpd.GeoDataFrame(columns=['geometry'])

print("Nombre de POI récupérés :", len(pois_gdf))
print(pois_gdf.shape)
print(pois_gdf.columns)
print(pois_gdf)

# ------------------------------------------ # 
# ---       Création de la carte         --- # 
# ------------------------------------------ # 
# Centre de la carte (point A)
center_lat = lat_pt_A 
center_lon = lon_pt_A

# Création de la carte
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=13,
    tiles="OpenStreetMap"
)

# Ajout marqueur point A 
folium.Marker(
    location=[lat_pt_A, lon_pt_A],
    popup="Maison",
    icon=folium.Icon(color="blue", icon="home")
).add_to(m)

# Ajout marqueur point B 
folium.Marker(
    location=[lat_pt_B, lon_pt_B],
    popup="Travail",
    icon=folium.Icon(color="red", icon="briefcase")
).add_to(m)

# Ajout des quartiers traversés
folium.GeoJson(
    quartiers_traverses,
    name='Quartiers traversés',
    style_function=lambda x: {
        'fillColor': 'green',
        'color': 'darkgreen',
        'weight': 3,
        'fillOpacity': 0.3
    },
    tooltip=folium.GeoJsonTooltip(fields=['short_name'])
).add_to(m)

# Tracé de l'itinéraire
folium.PolyLine(
    route_coords,
    color="blue",
    weight=5,
    opacity=0.7,
    # popup=f"Distance: {sum(ox.utils_graph.get_route_edge_attributes(G, route, 'length')):.0f}m"
).add_to(m)

# Ajout des points d'intêrets
for idx, poi in pois_gdf.iterrows():
    if poi.geometry.is_empty:
        continue

    geom = poi.geometry

    if geom.geom_type == "Point":
        lon, lat = geom.x, geom.y
    else:
        lon, lat = geom.centroid.x, geom.centroid.y
    
    name = poi.get('name', 'Monument')
    folium.Marker(
        location=[lat, lon],
        popup=name,
        icon=folium.Icon(color='orange', icon='info-sign')
    ).add_to(m)

# Sauvegarde HTML
m.save("map.html")

print("Carte générée : map.html")