# ...existing code...
"""
FoodSave AI — Basic Volunteer Routing
Assigns nearest available volunteer to an accepted donation.
"""

import json, os
from ai.matching import haversine_km
from math import inf

def get_active_volunteers():
    users_file = os.path.join("data", "users.json")
    users = json.load(open(users_file)) if os.path.exists(users_file) else []
    return [u for u in users if u.get("role") == "volunteer" and u.get("approved")]

# ...existing code...
def _coord(v, lat_key="lat", lng_key="lng"):
    # Helper to read coordinates from either nested 'coordinates' or top-level keys
    coords = v.get("coordinates") if isinstance(v, dict) else None
    if isinstance(coords, dict):
        return coords.get("lat"), coords.get("lng")
    return v.get(lat_key), v.get(lng_key)

def _load_all_ngos():
    # Try JSON first, fallback to CSV (simple CSV loader)
    ngos_file = os.path.join("data", "ngos.json")
    if os.path.exists(ngos_file):
        return json.load(open(ngos_file))
    ngos_csv = os.path.join("data", "ngos.csv")
    if os.path.exists(ngos_csv):
        import csv
        ngos = []
        with open(ngos_csv, newline='') as f:
            reader = csv.DictReader(f)
            for r in reader:
                ngos.append(r)
        return ngos
    return []

def assign_volunteer_route(donation, max_ngos=5, include_all_ngos=False):
    """
    Returns an ordered structure for routing:
      - Nearest volunteer to donor
      - Ranked list of NGOs (nearest first). If include_all_ngos True, we load all NGOs from data/
    Notes:
      - donation is expected to include either donation['coordinates'] = {'lat':..,'lng':..}
        or top-level 'lat' and 'lng'.
    """
    from ai.matching import match_donation_to_ngo

    volunteers = get_active_volunteers()
    if not volunteers:
        return {"error": "No volunteers available"}

    # donation coordinates (fallback to sensible defaults only if missing)
    d_lat, d_lng = _coord(donation)
    if d_lat is None or d_lng is None:
        d_lat, d_lng = 20.5937, 78.9629

    # Find nearest volunteer (skip volunteers without coords)
    nearest = None
    min_dist = inf
    for v in volunteers:
        v_lat, v_lng = _coord(v)
        if v_lat is None or v_lng is None:
            continue
        dist = haversine_km(v_lat, v_lng, d_lat, d_lng)
        if dist < min_dist:
            min_dist = dist
            nearest = v

    # Get NGO matches: prefer match_donation_to_ngo if available
    ngo_matches = []
    if not include_all_ngos:
        try:
            ngo_matches = match_donation_to_ngo(donation, max_results=max_ngos or 5) or []
        except Exception:
            ngo_matches = []
    if include_all_ngos or not ngo_matches:
        # Load all NGOs from disk and compute distances to donation
        all_ngos = _load_all_ngos()
        for n in all_ngos:
            n_lat, n_lng = _coord(n)
            if n_lat is None or n_lng is None:
                continue
            n_dist = haversine_km(d_lat, d_lng, n_lat, n_lng)
            ngo_matches.append({"ngo": n, "distance_km": round(n_dist, 2)})

        ngo_matches = sorted(ngo_matches, key=lambda x: x.get("distance_km", inf))
        if max_ngos:
            ngo_matches = ngo_matches[:max_ngos]

    # Build route_steps with all NGO options and distances
    route_steps = []
    route_steps.append("🚗 Start from your location")
    pickup_name = donation.get("food_name") or donation.get("name") or "food donation"
    pickup_location = donation.get("location") or f"{d_lat:.5f},{d_lng:.5f}"
    route_steps.append(f"📍 Pick up '{pickup_name}' at {pickup_location}")

    for i, nm in enumerate(ngo_matches, 1):
        ngo = nm.get("ngo")
        dist_to_ngo = nm.get("distance_km")
        ngo_name = ngo.get("name") if isinstance(ngo, dict) else str(ngo)
        route_steps.append(f"🏥 Option {i}: Deliver to {ngo_name} — {dist_to_ngo} km from donor")

    total_estimated = round(min_dist + (ngo_matches[0]["distance_km"] if ngo_matches else 0), 1) if nearest else None

    return {
        "volunteer":    nearest,
        "pickup":       donation,
        "ngos":         ngo_matches,
        "total_dist_km": total_estimated,
        "route_steps":  route_steps,
    }
# ...existing code...