"""
FoodSave AI — Smart Donation-to-NGO Matching
"""

import math
import json
import os

LOCATIONS_FILE = os.path.join("data", "locations.json")
NGOS_RAW_FILE = os.path.join("data", "ngos_raw.json")

def haversine_km(lat1, lng1, lat2, lng2):
    """Calculate distance in km between two coordinates."""
    lat1, lng1, lat2, lng2 = map(float, (lat1, lng1, lat2, lng2))
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlmbd = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlmbd/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

URGENCY_SCORE = {
    'critical': 100,
    'high':     75,
    'medium':   50,
    'low':      25,
    'safe':     10,
    'expired':  0
}

def _safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_locations():
    if os.path.exists(LOCATIONS_FILE):
        with open(LOCATIONS_FILE) as f:
            return json.load(f)
    if os.path.exists(NGOS_RAW_FILE):
        with open(NGOS_RAW_FILE) as f:
            return {"ngos": json.load(f), "restaurants": [], "poultry_farms": [], "biogas_plants": []}
    return {"ngos": [], "restaurants": [], "poultry_farms": [], "biogas_plants": []}


def _donation_coords(donation):
    coords = donation.get("coordinates") or {}
    lat = _safe_float(coords.get("lat"))
    lng = _safe_float(coords.get("lng"))
    if lat is None or lng is None:
        lat = _safe_float(donation.get("lat"))
        lng = _safe_float(donation.get("lng"))
    return lat, lng


def _accepts_food(entity, food_type):
    accepts = entity.get("accepts")
    if not accepts:
        return True
    return food_type in accepts or "other" in accepts


def _distance_score(distance_km, radius_km):
    radius = max(_safe_float(radius_km, 15), 1)
    return max(0, 100 * (1 - min(distance_km, radius) / radius))


def _capacity_score(entity, quantity):
    capacity = _safe_float(entity.get("capacity_kg"), 100) or 100
    quantity = max(_safe_float(quantity, 1) or 1, 1)
    if capacity >= quantity:
        return min(100, 70 + (capacity / quantity))
    return max(0, (capacity / quantity) * 70)


def _rank_entities(donation, entities, max_results=5, entity_key="entity", default_radius_km=15):
    d_lat, d_lng = _donation_coords(donation)
    if d_lat is None or d_lng is None:
        return []

    food_type = donation.get("food_type", "other")
    urgency = donation.get("urgency", "medium")
    quantity = donation.get("quantity", 1)
    urgency_boost = URGENCY_SCORE.get(urgency, 50) / 100

    results = []
    for entity in entities:
        if entity.get("active") is False:
            continue
        lat = _safe_float(entity.get("lat"))
        lng = _safe_float(entity.get("lng"))
        if lat is None or lng is None:
            continue
        if not _accepts_food(entity, food_type):
            continue

        dist_km = haversine_km(d_lat, d_lng, lat, lng)
        radius = _safe_float(entity.get("coverage_radius_km"), default_radius_km) or default_radius_km
        dist_score = _distance_score(dist_km, radius)
        cap_score = _capacity_score(entity, quantity)
        transport_score = 8 if entity.get("has_transport") else 0
        refrigeration_score = 5 if food_type in ["dairy", "cooked"] and entity.get("has_refrigeration") else 0
        exactness_penalty = 0 if entity.get("location_accuracy") == "exact" else 8
        final_score = (
            dist_score * 0.58
            + cap_score * 0.27
            + transport_score
            + refrigeration_score
            + urgency_boost * 10
            - exactness_penalty
        )

        result = {
            entity_key: entity,
            "distance_km": round(dist_km, 2),
            "score": round(max(final_score, 0), 1),
            "location_accuracy": entity.get("location_accuracy", "unknown"),
            "reason": (
                f"{round(dist_km, 1)}km away, "
                f"{entity.get('capacity_kg', 'unknown')}kg/day capacity, "
                f"{'exact GPS' if entity.get('location_accuracy') == 'exact' else 'estimated location'}"
            )
        }
        results.append(result)

    results.sort(key=lambda x: (x["score"], -x["distance_km"]), reverse=True)
    return results[:max_results]


def match_donation_to_ngo(donation, max_results=5):
    """
    Match a donation to best NGOs based on:
    - Distance (closer = better)
    - NGO capacity vs donation quantity
    - Urgency level priority
    Returns ranked list of NGOs with scores.
    """
    locations = _load_locations()
    ngos = [n for n in locations.get("ngos", []) if n.get("active")]
    return _rank_entities(donation, ngos, max_results=max_results, entity_key="ngo", default_radius_km=15)


def match_donation_to_poultry(donation, max_results=5):
    """Route non-human-grade or semi-fresh food to nearby poultry feed partners."""
    locations = _load_locations()
    farms = [p for p in locations.get("poultry_farms", []) if p.get("active")]
    return _rank_entities(donation, farms, max_results=max_results, entity_key="poultry_farm", default_radius_km=25)


def match_donation_to_biogas(donation, max_results=5):
    """Route rotten or unavoidable organic waste to nearby biogas plants."""
    locations = _load_locations()
    plants = [p for p in locations.get("biogas_plants", []) if p.get("active")]
    return _rank_entities(donation, plants, max_results=max_results, entity_key="biogas_plant", default_radius_km=35)


def find_nearby_restaurants(lat, lng, radius_km=10, limit=20, city=None):
    """Find restaurants near an NGO, volunteer, poultry farm, or typed coordinate."""
    locations = _load_locations()
    radius_km = max(_safe_float(radius_km, 10) or 10, 1)
    lat = _safe_float(lat)
    lng = _safe_float(lng)
    if lat is None or lng is None:
        return []

    city_norm = str(city or "").strip().lower()
    restaurants = []
    for restaurant in locations.get("restaurants", []):
        if restaurant.get("active") is False:
            continue
        if city_norm and city_norm not in str(restaurant.get("city", "")).lower():
            continue
        r_lat = _safe_float(restaurant.get("lat"))
        r_lng = _safe_float(restaurant.get("lng"))
        if r_lat is None or r_lng is None:
            continue
        dist_km = haversine_km(lat, lng, r_lat, r_lng)
        if dist_km > radius_km:
            continue
        rating = _safe_float(restaurant.get("rating"), 0) or 0
        votes = _safe_float(restaurant.get("votes"), 0) or 0
        exactness_bonus = 8 if restaurant.get("location_accuracy") == "exact" else 0
        score = max(0, 100 - (dist_km / radius_km) * 80) + rating * 3 + min(votes / 500, 8) + exactness_bonus
        restaurants.append({
            "restaurant": restaurant,
            "distance_km": round(dist_km, 2),
            "score": round(score, 1),
            "location_accuracy": restaurant.get("location_accuracy", "unknown"),
            "reason": f"{round(dist_km, 1)}km away, {restaurant.get('rating', 0)} rating",
        })
    restaurants.sort(key=lambda x: (x["score"], -x["distance_km"]), reverse=True)
    return restaurants[:limit]


def assign_to_biogas(donation):
    """
    Fallback: assign expired/critical unaccepted food to nearest biogas plant.
    Returns best biogas plant or None.
    """
    locations = _load_locations()

    plants = [p for p in locations.get("biogas_plants", []) if p.get("active")]
    if not plants:
        return None

    d_lat = donation.get("coordinates", {}).get("lat", 20.5937)
    d_lng = donation.get("coordinates", {}).get("lng", 78.9629)

    closest = min(
        plants,
        key=lambda p: haversine_km(d_lat, d_lng, p["lat"], p["lng"])
    )
    dist = haversine_km(d_lat, d_lng, closest["lat"], closest["lng"])

    return {
        "plant":       closest,
        "distance_km": round(dist, 1),
        "message":     f"Food assigned to {closest['name']} ({round(dist,1)}km away)"
    }
