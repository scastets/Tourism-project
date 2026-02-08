import requests
import streamlit as st

@st.cache_data(ttl=3600)
def search_photon(query):
    """Fonction appelée automatiquement lors de la frappe"""
    if not query or len(query) < 3:
        return []
    return photon_autocomplete(query, limit=10)
@st.cache_data(ttl=3600)
def photon_autocomplete(query, limit=5):
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
            print("Réponse vide")
            return []
        
        data = r.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur réseau : {e}")
        return []
    except ValueError as e:
        print(f"JSON invalide : {e}")
        return []
    
    results = []
    for f in data.get("features", []):
        props = f.get("properties", {})

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

        if full_address:
            results.append(full_address)

    # Évite les doublons
    return list(dict.fromkeys(results))

def geocode_address(address):
    """Géocode une adresse avec Photon (récupère lat/lon)"""
    if not address:
        return None
    
    url = "https://photon.komoot.io/api/"
    params = {
        "q": address,
        "limit": 1,
        "lang": "fr"
    }
    
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        
        if data.get("features"):
            coords = data["features"][0]["geometry"]["coordinates"]
            # Photon renvoie [lon, lat], on inverse pour Folium [lat, lon]
            return [coords[1], coords[0]]
    except:
        return None
    
    return None