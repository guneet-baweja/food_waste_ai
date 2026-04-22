#!/usr/bin/env python3
"""Build a normalized location index for FoodSave AI matching."""

import csv
import json
import sys
from pathlib import Path

csv.field_size_limit(sys.maxsize)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "locations.json"

NGOS_RAW = DATA / "ngos_raw.json"
ZOMATO_ARCHIVE_1 = ROOT / "ai" / "dataset_raw" / "archive1" / "zomato.csv"
ZOMATO_ARCHIVE_2 = ROOT / "ai" / "dataset_raw" / "archive2" / "zomato.csv"
SEED_LOCATIONS = DATA / "location.json"

BANGALORE_CENTER = (12.9716, 77.5946)
BANGALORE_LOCALITIES = {
    "Banashankari": (12.9255, 77.5468),
    "Basavanagudi": (12.9417, 77.5750),
    "BTM": (12.9166, 77.6101),
    "Brigade Road": (12.9700, 77.6068),
    "Brookefield": (12.9663, 77.7169),
    "Church Street": (12.9755, 77.6046),
    "Electronic City": (12.8452, 77.6602),
    "Frazer Town": (12.9980, 77.6140),
    "HSR": (12.9116, 77.6389),
    "Indiranagar": (12.9784, 77.6408),
    "Jayanagar": (12.9308, 77.5838),
    "JP Nagar": (12.9063, 77.5857),
    "Kalyan Nagar": (13.0221, 77.6408),
    "Kammanahalli": (13.0159, 77.6379),
    "Koramangala": (12.9352, 77.6245),
    "Lavelle Road": (12.9719, 77.5993),
    "Malleshwaram": (13.0031, 77.5643),
    "Marathahalli": (12.9569, 77.7011),
    "MG Road": (12.9759, 77.6068),
    "Old Airport Road": (12.9608, 77.6508),
    "Rajajinagar": (12.9915, 77.5545),
    "Residency Road": (12.9705, 77.6092),
    "Richmond Road": (12.9662, 77.6093),
    "Sarjapur Road": (12.9081, 77.6476),
    "Whitefield": (12.9698, 77.7500),
    "Yelahanka": (13.1007, 77.5963),
}

CITY_CENTERS = {
    "Agra": (27.1767, 78.0081),
    "Ahmedabad": (23.0225, 72.5714),
    "Allahabad": (25.4358, 81.8463),
    "Amritsar": (31.6340, 74.8723),
    "Aurangabad": (19.8762, 75.3433),
    "Bangalore": (12.9716, 77.5946),
    "Bhopal": (23.2599, 77.4126),
    "Bhubaneshwar": (20.2961, 85.8245),
    "Chandigarh": (30.7333, 76.7794),
    "Chennai": (13.0827, 80.2707),
    "Coimbatore": (11.0168, 76.9558),
    "Dehradun": (30.3165, 78.0322),
    "Faridabad": (28.4089, 77.3178),
    "Ghaziabad": (28.6692, 77.4538),
    "Goa": (15.2993, 74.1240),
    "Gurgaon": (28.4595, 77.0266),
    "Guwahati": (26.1445, 91.7362),
    "Hyderabad": (17.3850, 78.4867),
    "Indore": (22.7196, 75.8577),
    "Jaipur": (26.9124, 75.7873),
    "Kanpur": (26.4499, 80.3319),
    "Kochi": (9.9312, 76.2673),
    "Kolkata": (22.5726, 88.3639),
    "Lucknow": (26.8467, 80.9462),
    "Ludhiana": (30.9010, 75.8573),
    "Mangalore": (12.9141, 74.8560),
    "Mohali": (30.7046, 76.7179),
    "Mumbai": (19.0760, 72.8777),
    "Mysore": (12.2958, 76.6394),
    "Nagpur": (21.1458, 79.0882),
    "Nashik": (19.9975, 73.7898),
    "New Delhi": (28.6139, 77.2090),
    "Noida": (28.5355, 77.3910),
    "Panchkula": (30.6942, 76.8606),
    "Patna": (25.5941, 85.1376),
    "Puducherry": (11.9416, 79.8083),
    "Pune": (18.5204, 73.8567),
    "Ranchi": (23.3441, 85.3096),
    "Secunderabad": (17.4399, 78.4983),
    "Surat": (21.1702, 72.8311),
    "Vadodara": (22.3072, 73.1812),
    "Varanasi": (25.3176, 82.9739),
    "Vizag": (17.6868, 83.2185),
}


def parse_float(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def clean(value):
    return str(value or "").strip()


def valid_coord(lat, lng):
    return lat is not None and lng is not None and -90 <= lat <= 90 and -180 <= lng <= 180


def load_ngos():
    if not NGOS_RAW.exists():
        return []
    raw = json.loads(NGOS_RAW.read_text())
    ngos = []
    for item in raw:
        lat = parse_float(item.get("lat"))
        lng = parse_float(item.get("lng"))
        if not valid_coord(lat, lng):
            continue
        ngo = dict(item)
        ngo.update({
            "id": clean(item.get("id")) or f"ngo-{len(ngos) + 1}",
            "type": "ngo",
            "lat": lat,
            "lng": lng,
            "active": bool(item.get("active", True)),
            "location_accuracy": "exact",
            "source": "data/ngos_raw.json",
        })
        ngos.append(ngo)
    return ngos


def load_archive2_restaurants():
    restaurants = []
    seen = set()
    if not ZOMATO_ARCHIVE_2.exists():
        return restaurants
    with ZOMATO_ARCHIVE_2.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            if clean(row.get("Country Code")) != "1":
                continue
            lat = parse_float(row.get("Latitude"))
            lng = parse_float(row.get("Longitude"))
            if not valid_coord(lat, lng):
                continue
            rid = clean(row.get("Restaurant ID")) or f"archive2-{len(restaurants) + 1}"
            if rid in seen:
                continue
            seen.add(rid)
            restaurants.append({
                "id": f"zomato2-{rid}",
                "type": "restaurant",
                "name": clean(row.get("Restaurant Name")),
                "address": clean(row.get("Address")),
                "area": clean(row.get("Locality")),
                "city": clean(row.get("City")),
                "lat": lat,
                "lng": lng,
                "cuisines": clean(row.get("Cuisines")),
                "rating": parse_float(row.get("Aggregate rating")) or 0,
                "votes": int(parse_float(row.get("Votes")) or 0),
                "cost_for_two": parse_float(row.get("Average Cost for two")) or 0,
                "has_online_delivery": clean(row.get("Has Online delivery")) == "Yes",
                "location_accuracy": "exact",
                "source": "ai/dataset_raw/archive2/zomato.csv",
                "active": True,
            })
    return restaurants


def load_archive1_restaurants():
    restaurants = []
    seen = set()
    if not ZOMATO_ARCHIVE_1.exists():
        return restaurants
    with ZOMATO_ARCHIVE_1.open(newline="", encoding="utf-8", errors="replace") as f:
        for row in csv.DictReader(f):
            name = clean(row.get("name"))
            address = clean(row.get("address"))
            area = clean(row.get("location"))
            key = (name.lower(), address.lower())
            if not name or key in seen:
                continue
            seen.add(key)
            lat, lng = BANGALORE_LOCALITIES.get(area, BANGALORE_CENTER)
            restaurants.append({
                "id": f"zomato1-{len(restaurants) + 1}",
                "type": "restaurant",
                "name": name,
                "address": address,
                "area": area,
                "city": "Bangalore",
                "lat": lat,
                "lng": lng,
                "cuisines": clean(row.get("cuisines")),
                "rating": parse_float(clean(row.get("rate")).split("/")[0]) or 0,
                "votes": int(parse_float(row.get("votes")) or 0),
                "phone": clean(row.get("phone")),
                "rest_type": clean(row.get("rest_type")),
                "location_accuracy": "locality_estimated" if area in BANGALORE_LOCALITIES else "city_estimated",
                "source": "ai/dataset_raw/archive1/zomato.csv",
                "active": True,
            })
    return restaurants


def load_seed_locations(key, entity_type):
    if not SEED_LOCATIONS.exists():
        return []
    data = json.loads(SEED_LOCATIONS.read_text())
    entities = []
    for idx, item in enumerate(data.get(key, []), start=1):
        lat = parse_float(item.get("lat"))
        lng = parse_float(item.get("lng"))
        if not valid_coord(lat, lng):
            continue
        entity = dict(item)
        entity.update({
            "id": clean(item.get("id")) or f"{entity_type}-{idx}",
            "type": entity_type,
            "lat": lat,
            "lng": lng,
            "active": bool(item.get("active", True)),
            "location_accuracy": "exact",
            "source": "data/location.json",
        })
        entities.append(entity)
    return entities


def merge_by_id(primary, secondary):
    merged = list(primary)
    seen = {item.get("id") for item in merged}
    for item in secondary:
        if item.get("id") in seen:
            continue
        seen.add(item.get("id"))
        merged.append(item)
    return merged


def build_poultry_partners(ngos):
    cities = {}
    for ngo in ngos:
        city = clean(ngo.get("city"))
        if city and city not in cities:
            cities[city] = (ngo["lat"], ngo["lng"], clean(ngo.get("state")))
    for city, center in CITY_CENTERS.items():
        cities.setdefault(city, (center[0], center[1], ""))

    farms = []
    for idx, (city, (lat, lng, state)) in enumerate(sorted(cities.items()), start=1):
        farms.append({
            "id": f"poultry-{idx:03d}",
            "type": "poultry_farm",
            "name": f"{city} Poultry Feed Partner",
            "address": f"{city}, {state or 'India'}",
            "city": city,
            "state": state,
            "lat": lat + 0.035,
            "lng": lng + 0.035,
            "capacity_kg": 250,
            "accepts": ["raw", "bakery", "packaged", "other"],
            "active": True,
            "location_accuracy": "city_partner_seed",
            "source": "generated_seed_partner",
        })
    return farms


def main():
    DATA.mkdir(exist_ok=True)
    ngos = merge_by_id(load_ngos(), load_seed_locations("ngos", "ngo"))
    restaurants = load_archive2_restaurants() + load_archive1_restaurants()
    restaurants = merge_by_id(restaurants, load_seed_locations("restaurants", "restaurant"))
    biogas_plants = load_seed_locations("biogas_plants", "biogas_plant")
    poultry_farms = build_poultry_partners(ngos)
    payload = {
        "schema_version": 1,
        "generated_from": [
            "data/ngos_raw.json",
            "ai/dataset_raw/archive2/zomato.csv",
            "ai/dataset_raw/archive1/zomato.csv",
        ],
        "ngos": ngos,
        "restaurants": restaurants,
        "poultry_farms": poultry_farms,
        "biogas_plants": biogas_plants,
        "cafeterias": [],
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUT}")
    print(f"NGOs: {len(ngos)}")
    print(f"Restaurants: {len(restaurants)}")
    print(f"Poultry partners: {len(poultry_farms)}")
    print(f"Biogas plants: {len(biogas_plants)}")


if __name__ == "__main__":
    main()
