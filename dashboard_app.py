import streamlit as st
from streamlit_folium import st_folium
from streamlit_searchbox import st_searchbox
import folium
import requests
from utils import search_photon, geocode_address


# --------------------------------------# 
# Config de la page                     #
# --------------------------------------#
st.set_page_config(page_title="AppTourism", layout="wide")
st.title("Test App Tourism")

# --------------------------------------# 
# Création colonnes                     #
# --------------------------------------#
buttons_col, map_col = st.columns([1, 3])
def photon_autocomplete(query, limit=5):
    """Retourne une liste de tuples (label, coords)"""
    if not query or len(query) < 3:
        return []
    
    url = "https://photon.komoot.io/api/"
    params = {
        "q": query,
        "limit": limit,
        "lang": "fr"
    }
    headers = {
        "User-Agent": "AppTourism/1.0 (contact: test@example.com)"
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=5)
        r.raise_for_status()
        
        if not r.text.strip():
            return []
        
        data = r.json()
        
    except Exception as e:
        print(f"Erreur API : {e}")
        return []
    
    results = []
    for f in data.get("features", []):
        props = f.get("properties", {})
        geom = f.get("geometry", {})
        housenumber = props.get("housenumber", "")
        street = props.get("street", "")
        name = props.get("name", "")
        postcode = props.get("postcode", "")
        city = props.get("city", "")

        # 📍 Construction de l'adresse
        if housenumber and street:
            address_line = f"{housenumber} {street}"
        elif street:
            address_line = street
        else:
            address_line = name

        city_line = " ".join(part for part in [postcode, city] if part)

        # Assemblage final
        full_address = ", ".join(
            part for part in [address_line, city_line] if part
        )

        # Coordonnées [lon, lat] → on inverse pour [lat, lon]
        coords_raw = geom.get("coordinates", [])
        if len(coords_raw) == 2:
            coords = [coords_raw[1], coords_raw[0]]  # [lat, lon]
        else:
            coords = None

            if full_address:
                results.append({
                    "label": full_address,
                    "coords": coords
                })
    
    return results


def search_photon(query):
    """Fonction pour st_searchbox - retourne uniquement les labels"""
    results = photon_autocomplete(query, limit=10)
    return [r["label"] for r in results]


# Stocker les coordonnées dans session_state
if "coords_cache" not in st.session_state:
    st.session_state.coords_cache = {}


def get_coords_from_address(address):
    """Récupère les coordonnées depuis le cache ou via géocodage"""
    if not address:
        return None
    
    # Vérifier le cache
    if address in st.session_state.coords_cache:
        return st.session_state.coords_cache[address]
    
    # Sinon, géocoder et mettre en cache
    results = photon_autocomplete(address, limit=1)
    if results:
        coords = results[0]["coords"]
        st.session_state.coords_cache[address] = coords
        return coords
    
    return None


with buttons_col:
    st.subheader("Itinéraire")

    address_A = st_searchbox(
        search_photon,
        placeholder="Ex: 57 Rue de l'Université, Paris",
        label="Adresse de départ",
        key="searchbox_A"
    )

    address_B = st_searchbox(
        search_photon,
        placeholder="Ex: 38 Cr Albert 1er, Paris",
        label="Adresse d'arrivée",
        key="searchbox_B"
    )
    
    run = st.button("Calculer l'itinéraire")


with map_col:
    # Récupérer les coordonnées
    coords_A = get_coords_from_address(address_A)
    coords_B = get_coords_from_address(address_B)
    
    # Créer la carte avec logique de zoom
    if coords_A and coords_B:
        center_lat = (coords_A[0] + coords_B[0]) / 2
        center_lon = (coords_A[1] + coords_B[1]) / 2
        center = [center_lat, center_lon]
        
        m = folium.Map(
            location=center,
            control_scale=True,
            prefer_canvas=True, 
            tiles=None
        )
        
        bounds = [coords_A, coords_B]
        m.fit_bounds(bounds, padding=[50, 50])
        
    elif coords_A:
        m = folium.Map(
            location=coords_A,
            zoom_start=15,
            control_scale=True,
            prefer_canvas=True, 
            tiles=None
        )
    elif coords_B:
        m = folium.Map(
            location=coords_B,
            zoom_start=15,
            control_scale=True,
            prefer_canvas=True, 
            tiles=None
        )
    else:
        m = folium.Map(
            location=[48.8566, 2.3522],
            zoom_start=13,
            control_scale=True,
            prefer_canvas=True, 
            tiles=None
        )

    # Couches
    folium.TileLayer("OpenStreetMap", control=True, show=True).add_to(m)
    folium.TileLayer("CartoDB positron", control=True, show=False).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="© Esri",
        name="ESRI Satellite",
        control=True,
        show=False,
        max_zoom=19
    ).add_to(m)

    # Marqueurs
    if coords_A:
        folium.Marker(
            coords_A,
            popup=f"<b>Départ</b><br>{address_A}",
            tooltip="Point de départ",
            icon=folium.Icon(color='green', icon='play', prefix='fa')
        ).add_to(m)
    
    if coords_B:
        folium.Marker(
            coords_B,
            popup=f"<b>Arrivée</b><br>{address_B}",
            tooltip="Point d'arrivée",
            icon=folium.Icon(color='red', icon='stop', prefix='fa')
        ).add_to(m)

    folium.LayerControl(position="topright", collapsed=True).add_to(m)

    st_folium(m, height=450, use_container_width=True, returned_objects=[])


# with buttons_col:
#     # Header de la colonne 
#     st.subheader("Itinéraire")

#     # Adresse de départ 
#     address_A = st_searchbox(
#         search_photon,
#         placeholder="Ex: 57 Rue de l'Université, Paris",
#         label="Adresse de départ",
#         key="searchbox_A"
#     )

#     # Adresse d'arrivée 
#     address_B = st_searchbox(
#         search_photon,
#         placeholder="Ex: 38 Cr Albert 1er, Paris",
#         label="Adresse d'arrivée",
#         key="searchbox_B"
#     )
    
#     # Bouton pour lancer calcul de l'itinéraire
#     run = st.button("Calculer l’itinéraire")

# with map_col:
#     # Géocodage des adresses
#     coords_A = geocode_address(address_A) if address_A else None
#     coords_B = geocode_address(address_B) if address_B else None
#     print(coords_A, coords_B)

#     # Déterminer le centre et le zoom
#     if coords_A and coords_B:
#         # Centre entre les deux points
#         center_lat = (coords_A[0] + coords_B[0]) / 2
#         center_lon = (coords_A[1] + coords_B[1]) / 2
#         center = [center_lat, center_lon]
        
#         # Créer la carte centrée entre les deux points
#         m = folium.Map(
#             location=center,
#             control_scale=True,
#             prefer_canvas=True, 
#             tiles=None
#         )
        
#         # Ajuster le zoom pour voir les deux points
#         bounds = [coords_A, coords_B]
#         m.fit_bounds(bounds, padding=[50, 50])
        
#     elif coords_A:
#         # Seulement point A
#         m = folium.Map(
#             location=coords_A,
#             zoom_start=15,
#             control_scale=True,
#             prefer_canvas=True, 
#             tiles=None
#         )
#     elif coords_B:
#         # Seulement point B
#         m = folium.Map(
#             location=coords_B,
#             zoom_start=15,
#             control_scale=True,
#             prefer_canvas=True, 
#             tiles=None
#         )
#     else:
#         # Aucun point : carte par défaut sur Paris
#         m = folium.Map(
#             location=[48.8566, 2.3522],
#             zoom_start=13,
#             control_scale=True,
#             prefer_canvas=True, 
#             tiles=None
#         )
#     # Couche OpenStreetMap (fond par défaut)
#     folium.TileLayer(
#         tiles="OpenStreetMap",
#         name="OpenStreetMap",
#         control=True,
#         show=True 
#     ).add_to(m)

#     # Couche CartoDB clair
#     folium.TileLayer(
#     "CartoDB positron",
#     name="CartoDB", 
#     control=True,
#     show=False,
#     ).add_to(m)

#     # Couche image satellite ESRI
#     folium.TileLayer(
#         tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
#         attr="© Esri",
#         name="ESRI Satellite",
#         control=True,
#         show=False,
#         max_zoom=19
#     ).add_to(m)

#     # Contrôleur de couches
#     folium.LayerControl(
#         position="topright",
#         collapsed=True
#     ).add_to(m)

#     # Ajout des marqueurs
#     if coords_A:
#         folium.Marker(
#             coords_A,
#             popup=f"<b>Départ</b><br>{address_A}",
#             tooltip="Point de départ",
#             icon=folium.Icon(color='green', icon='play', prefix='fa')
#         ).add_to(m)
    
#     if coords_B:
#         folium.Marker(
#             coords_B,
#             popup=f"<b>Arrivée</b><br>{address_B}",
#             tooltip="Point d'arrivée",
#             icon=folium.Icon(color='red', icon='stop', prefix='fa')
#         ).add_to(m)

#     # Ajout au dashboard
#     st_folium(
#         m,
#         height=450, 
#         use_container_width=True,
#         returned_objects=[]
#     )
    




