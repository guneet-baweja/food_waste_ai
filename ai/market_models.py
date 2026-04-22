"""
FoodSave AI market primitives.

These functions keep the new restaurant network deterministic and auditable.
Computer-vision freshness can plug in at prediction time, but settlement,
matching, and credit math should remain explainable.
"""

import math
import uuid
from datetime import datetime, timedelta

from ai.matching import (
    find_nearby_restaurants,
    match_donation_to_biogas,
    match_donation_to_ngo,
    match_donation_to_poultry,
)


FOOD_RISK = {
    "meat": 1.45,
    "dairy": 1.32,
    "cooked": 1.18,
    "raw": 1.0,
    "bakery": 0.88,
    "packaged": 0.72,
    "other": 1.08,
}

LANDFILL_FACTORS = {
    "cooked": 2.8,
    "raw": 1.9,
    "bakery": 1.7,
    "dairy": 3.4,
    "packaged": 2.1,
    "meat": 8.0,
    "other": 2.3,
}

ROUTE_FACTORS = {
    "ngo": 0.35,
    "poultry": 0.75,
    "biogas": 0.55,
    "compost": 1.05,
    "landfill": 0,
}


def safe_float(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def confidence_from_prediction(prediction, food_type="other"):
    raw_conf = prediction.get("ai_confidence")
    if raw_conf is not None:
        conf = safe_float(raw_conf, 0.82)
        return round(conf if conf <= 1 else conf / 100, 3)

    hours = safe_float(prediction.get("hours_remaining"), 12)
    urgency = prediction.get("urgency", "medium")
    base = {
        "safe": 0.9,
        "low": 0.87,
        "medium": 0.82,
        "high": 0.78,
        "critical": 0.74,
        "expired": 0.94,
    }.get(urgency, 0.8)
    if hours < 6:
        base -= 0.04
    if food_type in ["meat", "dairy"]:
        base -= 0.03
    return round(max(0.62, min(base, 0.96)), 3)


def build_freshness_contract(payload, prediction):
    food_type = payload.get("food_type", "other")
    quantity_kg = max(safe_float(payload.get("quantity_kg"), 1), 0.1)
    insured_value = max(safe_float(payload.get("insured_value_inr"), quantity_kg * 110), 1)
    predicted_hours = max(safe_float(prediction.get("hours_remaining"), 0), 0)
    confidence = confidence_from_prediction(prediction, food_type)

    risk = FOOD_RISK.get(food_type, FOOD_RISK["other"])
    short_life_risk = 1.25 if predicted_hours < 12 else 1.0
    confidence_discount = 1 - ((confidence - 0.7) * 0.45)
    premium_rate = min(0.05, max(0.02, 0.026 * risk * short_life_risk * confidence_discount))
    premium = round(insured_value * premium_rate, 2)
    buffer_fund = round(premium * 0.35, 2)

    return {
        "id": f"fiaas-{uuid.uuid4().hex[:12]}",
        "restaurant_id": payload.get("restaurant_id", ""),
        "restaurant_name": payload.get("restaurant_name", ""),
        "supplier_name": payload.get("supplier_name", "Supplier"),
        "food_item": payload.get("food_item", "Food batch"),
        "food_type": food_type,
        "quantity_kg": quantity_kg,
        "insured_value_inr": round(insured_value, 2),
        "predicted_fresh_hours": round(predicted_hours, 2),
        "freshness_score": prediction.get("freshness_score"),
        "urgency": prediction.get("urgency"),
        "confidence": confidence,
        "premium_rate": round(premium_rate, 4),
        "premium_inr": premium,
        "buffer_fund_inr": buffer_fund,
        "settlement_rule": "Supplier pays early spoilage penalty; restaurant pays freshness bonus if the batch outlives the guaranteed window.",
        "status": "active",
        "created_at": datetime.now().isoformat(),
    }


def settle_freshness_contract(contract, actual_spoilage_hours):
    actual = max(safe_float(actual_spoilage_hours), 0)
    predicted = safe_float(contract.get("predicted_fresh_hours"))
    value = safe_float(contract.get("insured_value_inr"))
    delta = round(actual - predicted, 2)
    if delta < -0.5:
        amount = round(min(value * 0.35, abs(delta) * value * 0.018), 2)
        direction = "supplier_to_restaurant"
    elif delta > 2:
        amount = round(min(value * 0.18, delta * value * 0.006), 2)
        direction = "restaurant_to_supplier"
    else:
        amount = 0
        direction = "no_settlement"

    updated = dict(contract)
    updated.update({
        "actual_spoilage_hours": actual,
        "freshness_delta_hours": delta,
        "settlement_direction": direction,
        "settlement_amount_inr": amount,
        "status": "settled",
        "settled_at": datetime.now().isoformat(),
    })
    return updated


def predict_waste_streams(payload):
    menu = str(payload.get("menu_plan", "")).lower()
    inventory_kg = max(safe_float(payload.get("inventory_kg"), 50), 1)
    confidence_seed = 0.78 + min(inventory_kg, 200) / 2000

    has_meat = any(word in menu for word in ["chicken", "mutton", "fish", "meat", "bone", "kebab"])
    has_veg = any(word in menu for word in ["veg", "vegetable", "salad", "carrot", "potato", "paneer", "dal"])
    has_rice = any(word in menu for word in ["rice", "biryani", "pulao", "idli", "dosa", "roti", "bread"])
    has_dairy = any(word in menu for word in ["milk", "curd", "dairy", "paneer", "cream", "cheese"])

    streams = []
    if has_veg or not streams:
        streams.append({
            "stream_type": "vegetable_peels",
            "food_type": "raw",
            "freshness_category": "semi_fresh",
            "route": "poultry",
            "quantity_kg": round(inventory_kg * 0.16, 2),
            "base_price_per_kg": 5.5,
        })
    if has_rice or "buffet" in menu or "thali" in menu:
        streams.append({
            "stream_type": "cooked_leftovers",
            "food_type": "cooked",
            "freshness_category": "edible",
            "route": "ngo",
            "quantity_kg": round(inventory_kg * 0.11, 2),
            "base_price_per_kg": 0,
        })
    if has_meat:
        streams.append({
            "stream_type": "bones_and_trimmings",
            "food_type": "meat",
            "freshness_category": "rotten_risk",
            "route": "biogas",
            "quantity_kg": round(inventory_kg * 0.09, 2),
            "base_price_per_kg": 3.8,
        })
    if has_dairy:
        streams.append({
            "stream_type": "dairy_spoilage_risk",
            "food_type": "dairy",
            "freshness_category": "critical",
            "route": "biogas",
            "quantity_kg": round(inventory_kg * 0.045, 2),
            "base_price_per_kg": 4.2,
        })

    for stream in streams:
        confidence = min(0.96, confidence_seed + (0.04 if stream["route"] != "ngo" else 0.02))
        stream["confidence"] = round(confidence, 3)
        stream["token"] = f"PWX-{uuid.uuid4().hex[:8].upper()}"
        stream["delivery_window"] = payload.get(
            "delivery_window",
            (datetime.now() + timedelta(hours=24)).isoformat(timespec="minutes")
        )
    return streams


def build_waste_future(payload):
    lat = safe_float(payload.get("lat"), 28.6139)
    lng = safe_float(payload.get("lng"), 77.2090)
    streams = predict_waste_streams(payload)
    futures = []

    for stream in streams:
        probe = {
            "food_type": stream["food_type"],
            "quantity": stream["quantity_kg"],
            "urgency": "high" if stream["route"] in ["biogas", "poultry"] else "medium",
            "freshness_score": 45 if stream["route"] != "ngo" else 72,
            "coordinates": {"lat": lat, "lng": lng},
        }
        if stream["route"] == "ngo":
            matches = match_donation_to_ngo(probe, max_results=4)
        elif stream["route"] == "poultry":
            matches = match_donation_to_poultry(probe, max_results=4)
        else:
            matches = match_donation_to_biogas(probe, max_results=4)

        futures.append({
            "id": f"future-{uuid.uuid4().hex[:12]}",
            "restaurant_id": payload.get("restaurant_id", ""),
            "restaurant_name": payload.get("restaurant_name", "Restaurant"),
            "lat": lat,
            "lng": lng,
            "menu_plan": payload.get("menu_plan", ""),
            "stream": stream,
            "matches": matches,
            "bids": [],
            "status": "open",
            "created_at": datetime.now().isoformat(),
        })
    return futures


def price_future_bid(future, price_per_kg, quantity_kg):
    stream = future.get("stream", {})
    confidence = safe_float(stream.get("confidence"), 0.8)
    base = safe_float(stream.get("base_price_per_kg"), 0)
    quantity = max(safe_float(quantity_kg), 0.1)
    price = max(safe_float(price_per_kg), 0)
    premium = 1 + max(0, confidence - 0.9) * 1.7
    reserve = base * premium
    accepted = price >= reserve or stream.get("route") == "ngo"
    return {
        "id": f"bid-{uuid.uuid4().hex[:10]}",
        "future_id": future.get("id"),
        "bidder_name": "",
        "bidder_type": "",
        "quantity_kg": quantity,
        "price_per_kg": price,
        "gross_value_inr": round(quantity * price, 2),
        "reserve_price_per_kg": round(reserve, 2),
        "prediction_accuracy_fee_inr": round(quantity * price * (0.005 if confidence >= 0.95 else 0.0025), 2),
        "accepted": accepted,
        "created_at": datetime.now().isoformat(),
    }


def build_geo_credit(donation, route_type=None, distance_km=None, status="provisional", buyer_name=None):
    food_type = donation.get("food_type", "other")
    quantity = max(safe_float(donation.get("quantity"), 1), 0.1)
    urgency = donation.get("urgency", "medium")
    route = (route_type or donation.get("recommended_route") or "ngo").lower()
    if route in ["poultry_farm", "poultry_or_biogas"]:
        route = "poultry"
    if route == "biogas_routed":
        route = "biogas"

    distance = safe_float(distance_km)
    if not distance:
        matches = donation.get("matches", {})
        pools = matches.get("ngos", []) + matches.get("poultry_farms", [])
        if pools:
            distance = safe_float(pools[0].get("distance_km"), 5)
        else:
            distance = 5

    landfill = LANDFILL_FACTORS.get(food_type, LANDFILL_FACTORS["other"]) * quantity
    routed = ROUTE_FACTORS.get(route, 0.75) * quantity
    transport = distance * 0.19
    urgency_factor = {
        "expired": 0.8,
        "critical": 1.35,
        "high": 1.2,
        "medium": 1.0,
        "low": 0.9,
        "safe": 0.8,
    }.get(urgency, 1.0)
    locality_factor = 1 + min(0.45, 1 / (distance + 1))
    kg_co2e = max(0, (landfill - routed - transport) * urgency_factor * locality_factor)
    credit_value = round(kg_co2e * 2.8, 2)

    return {
        "id": donation.get("carbon_credit_id") or f"gcnc-{uuid.uuid4().hex[:12]}",
        "donation_id": donation.get("id"),
        "route_type": route,
        "food_type": food_type,
        "quantity_kg": quantity,
        "distance_km": round(distance, 2),
        "kg_co2e": round(kg_co2e, 3),
        "credit_value_inr": credit_value,
        "platform_fee_inr": round(credit_value * 0.2, 2),
        "status": status,
        "buyer_name": buyer_name or "",
        "formula": "(landfill - routed - transport) * urgency_factor * locality_factor",
        "created_at": datetime.now().isoformat(),
    }


def restaurant_network_snapshot(locations, insurance, futures, credits, lat=28.6139, lng=77.2090):
    return {
        "counts": {
            "restaurants": len(locations.get("restaurants", [])),
            "ngos": len(locations.get("ngos", [])),
            "poultry_farms": len(locations.get("poultry_farms", [])),
            "biogas_plants": len(locations.get("biogas_plants", [])),
            "insurance_contracts": len(insurance),
            "open_futures": len([f for f in futures if f.get("status") == "open"]),
            "carbon_credits": len(credits),
        },
        "nearby_restaurants": find_nearby_restaurants(lat, lng, radius_km=20, limit=8),
        "recent_insurance": insurance[-5:][::-1],
        "recent_futures": futures[-6:][::-1],
        "recent_credits": credits[-6:][::-1],
    }
