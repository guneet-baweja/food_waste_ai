"""
Convert downloaded CSV datasets to FoodSave AI JSON format
Usage: python3 scripts/convert_dataset.py
"""

import pandas as pd
import json
import os

# ── 1. Convert NGO CSV ──
def convert_ngos(csv_path, output_path):
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} NGOs")
    print("Columns:", df.columns.tolist())

    ngos = []
    for _, row in df.iterrows():
        try:
            ngo = {
                "id":          f"ngo_{len(ngos)+1:04d}",
                "name":        str(row.get("Name", row.get("name", "Unknown"))),
                "address":     str(row.get("Address", row.get("address", ""))),
                "city":        str(row.get("City", row.get("city", ""))),
                "state":       str(row.get("State", row.get("state", ""))),
                "lat":         float(row.get("Latitude",  row.get("lat",  0))),
                "lng":         float(row.get("Longitude", row.get("lng", 0))),
                "phone":       str(row.get("Phone", row.get("phone", ""))),
                "capacity_kg": 200,   # default, update manually
                "active":      True,
                "accepts":     ["cooked", "raw", "bakery", "dairy"]
            }
            if ngo["lat"] != 0 and ngo["lng"] != 0:
                ngos.append(ngo)
        except Exception as e:
            continue

    with open(output_path, "w") as f:
        json.dump(ngos, f, indent=2)
    print(f"✅ Saved {len(ngos)} NGOs to {output_path}")


# ── 2. Convert Restaurant CSV ──
def convert_restaurants(csv_path, output_path):
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} restaurants")

    restaurants = []
    for _, row in df.iterrows():
        try:
            rest = {
                "id":                f"res_{len(restaurants)+1:04d}",
                "name":              str(row.get("name", "Unknown")),
                "address":           str(row.get("address", "")),
                "city":              str(row.get("city", "")),
                "lat":               float(row.get("latitude",  row.get("lat",  0))),
                "lng":               float(row.get("longitude", row.get("lng", 0))),
                "avg_daily_waste_kg": 30,
                "cuisine":           str(row.get("cuisines", "")),
                "active":            True
            }
            if rest["lat"] != 0:
                restaurants.append(rest)
        except Exception:
            continue

    with open(output_path, "w") as f:
        json.dump(restaurants, f, indent=2)
    print(f"✅ Saved {len(restaurants)} restaurants to {output_path}")


# ── 3. Convert Biogas / Poultry CSV ──
def convert_facilities(csv_path, output_path, facility_type):
    df = pd.read_csv(csv_path)
    facilities = []
    for _, row in df.iterrows():
        try:
            item = {
                "id":           f"{facility_type[:3]}_{len(facilities)+1:04d}",
                "type":         facility_type,
                "name":         str(row.get("name", "Unknown")),
                "address":      str(row.get("address", "")),
                "state":        str(row.get("state", "")),
                "lat":          float(row.get("latitude",  row.get("lat",  0))),
                "lng":          float(row.get("longitude", row.get("lng", 0))),
                "capacity_kg":  int(row.get("capacity", 500)),
                "active":       True
            }
            if item["lat"] != 0:
                facilities.append(item)
        except Exception:
            continue

    with open(output_path, "w") as f:
        json.dump(facilities, f, indent=2)
    print(f"✅ Saved {len(facilities)} {facility_type} to {output_path}")


# ── RUN ──
os.makedirs("data/raw", exist_ok=True)

# Uncomment each as you download the CSVs
# convert_ngos("data/raw/ngos.csv", "data/ngos.json")
# convert_restaurants("data/raw/restaurants.csv", "data/restaurants.json")
# convert_facilities("data/raw/biogas.csv", "data/biogas.json", "biogas")
# convert_facilities("data/raw/poultry.csv", "data/poultry.json", "poultry")

print("Done. Uncomment the lines above after downloading CSVs")
# Add to scripts/convert_dataset.py if lat/lng columns are missing

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

def add_coordinates(json_path):
    """Add lat/lng to entries that are missing coordinates."""
    geolocator = Nominatim(user_agent="foodsave_ai")
    geocode    = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    with open(json_path) as f:
        items = json.load(f)

    fixed = 0
    for item in items:
        if item.get("lat", 0) == 0:
            query = f"{item.get('address', '')} {item.get('city', '')} India"
            try:
                loc = geocode(query)
                if loc:
                    item["lat"] = loc.latitude
                    item["lng"] = loc.longitude
                    fixed += 1
                    print(f"📍 Found: {item['name']} → {loc.latitude}, {loc.longitude}")
            except Exception:
                pass

    with open(json_path, "w") as f:
        json.dump(items, f, indent=2)
    print(f"✅ Fixed coordinates for {fixed} entries")

# add_coordinates("data/ngos.json")