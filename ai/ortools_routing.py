"""
FoodSave AI — OR-Tools Vehicle Routing
Optimizes multi-stop volunteer pickup routes
Run standalone: python3 ai/ortools_routing.py
"""

import json
import math
import os
from typing import List, Dict, Optional

def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a  = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)), 2)

def simple_nearest_neighbor_route(
    depot: Dict,
    pickups: List[Dict],
    delivery: Dict
) -> Dict:
    """
    Simple nearest-neighbor routing when OR-Tools not available.
    depot    = volunteer start location {lat, lng, name}
    pickups  = list of donations {lat, lng, food_name, location}
    delivery = NGO/facility {lat, lng, name}
    """
    if not pickups:
        return {"route": [], "total_km": 0, "steps": []}

    unvisited = pickups.copy()
    route     = []
    steps     = []
    total_km  = 0
    current   = depot

    steps.append(f"🚗 Start from {depot.get('name', 'your location')}")

    while unvisited:
        # Find nearest unvisited pickup
        nearest  = min(
            unvisited,
            key=lambda p: haversine_km(
                current["lat"], current["lng"],
                p.get("lat", 0), p.get("lng", 0)
            )
        )
        dist = haversine_km(
            current["lat"], current["lng"],
            nearest.get("lat", 0), nearest.get("lng", 0)
        )
        total_km += dist
        route.append(nearest)
        steps.append(
            f"📦 Pick up '{nearest.get('food_name', 'Food')}' "
            f"at {nearest.get('location', 'Unknown')} ({dist:.1f} km)"
        )
        current   = nearest
        unvisited.remove(nearest)

    # Final delivery
    final_dist = haversine_km(
        current["lat"], current["lng"],
        delivery.get("lat", 0), delivery.get("lng", 0)
    )
    total_km += final_dist
    steps.append(
        f"🏥 Deliver to {delivery.get('name', 'NGO')} ({final_dist:.1f} km)"
    )
    steps.append(f"✅ Total route: {total_km:.1f} km")

    return {
        "route":     route,
        "delivery":  delivery,
        "total_km":  round(total_km, 2),
        "steps":     steps,
        "stop_count": len(route) + 1
    }

def ortools_route(
    depot: Dict,
    pickups: List[Dict],
    delivery: Dict,
    num_vehicles: int = 1
) -> Dict:
    """
    OR-Tools optimized routing.
    Falls back to nearest-neighbor if OR-Tools not installed.
    """
    try:
        from ortools.constraint_solver import routing_enums_pb2
        from ortools.constraint_solver import pywrapcp

        # Build location list: depot, all pickups, delivery
        locations = [depot] + pickups + [delivery]
        n         = len(locations)

        # Distance matrix (in meters × 10 for integer math)
        dist_matrix = []
        for i in range(n):
            row = []
            for j in range(n):
                d = haversine_km(
                    locations[i].get("lat", 0), locations[i].get("lng", 0),
                    locations[j].get("lat", 0), locations[j].get("lng", 0)
                )
                row.append(int(d * 1000))  # km → meters
            dist_matrix.append(row)

        # OR-Tools manager
        manager = pywrapcp.RoutingIndexManager(n, num_vehicles, 0)
        routing = pywrapcp.RoutingModel(manager)

        def dist_callback(from_idx, to_idx):
            f = manager.IndexToNode(from_idx)
            t = manager.IndexToNode(to_idx)
            return dist_matrix[f][t]

        transit_callback_index = routing.RegisterTransitCallback(dist_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Force visit all nodes
        routing.AddDimension(transit_callback_index, 0, 1000000, True, 'Distance')

        # Search parameters
        search_params = pywrapcp.DefaultRoutingSearchParameters()
        search_params.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_params.time_limit.seconds = 10

        solution = routing.SolveWithParameters(search_params)

        if not solution:
            print("⚠️ OR-Tools: no solution found, using nearest-neighbor")
            return simple_nearest_neighbor_route(depot, pickups, delivery)

        # Extract route
        route_nodes = []
        steps       = []
        total_dist  = 0
        index       = routing.Start(0)

        steps.append(f"🚗 Start from {depot.get('name', 'depot')}")
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            if 0 < node_index <= len(pickups):
                p = pickups[node_index - 1]
                route_nodes.append(p)
                steps.append(
                    f"📦 Pick up '{p.get('food_name','Food')}' at {p.get('location','')}"
                )
            next_index = solution.Value(routing.NextVar(index))
            total_dist += dist_matrix[manager.IndexToNode(index)][manager.IndexToNode(next_index)]
            index = next_index

        steps.append(f"🏥 Deliver to {delivery.get('name', 'NGO')}")
        steps.append(f"✅ Optimized route: {total_dist/1000:.1f} km")

        print("✅ OR-Tools route optimized")
        return {
            "route":     route_nodes,
            "delivery":  delivery,
            "total_km":  round(total_dist / 1000, 2),
            "steps":     steps,
            "stop_count": len(route_nodes) + 1,
            "method":    "ortools"
        }

    except ImportError:
        print("⚠️ OR-Tools not installed. pip3 install ortools. Using fallback.")
        return simple_nearest_neighbor_route(depot, pickups, delivery)
    except Exception as e:
        print(f"⚠️ OR-Tools error: {e}. Using fallback.")
        return simple_nearest_neighbor_route(depot, pickups, delivery)

def plan_volunteer_route(volunteer_id: str, donation_ids: List[str]) -> Dict:
    """
    High-level function: plan route for a volunteer.
    volunteer_id: user ID from users.json
    donation_ids: list of donation IDs to pick up
    """
    # Load data
    users     = json.load(open("data/users.json")) if os.path.exists("data/users.json") else []
    donations = json.load(open("data/donations.json")) if os.path.exists("data/donations.json") else []
    ngos      = json.load(open("data/ngos.json")) if os.path.exists("data/ngos.json") else []

    # Get volunteer
    volunteer = next((u for u in users if u["id"] == volunteer_id), None)
    if not volunteer:
        return {"error": "Volunteer not found"}

    depot = {
        "lat":  volunteer.get("lat", 28.6139),
        "lng":  volunteer.get("lng", 77.2090),
        "name": volunteer.get("name", "Volunteer")
    }

    # Get donations to pick up
    pickups = []
    for did in donation_ids:
        d = next((x for x in donations if x["id"] == did), None)
        if d:
            pickups.append({
                "lat":       d.get("coordinates", {}).get("lat", 28.6),
                "lng":       d.get("coordinates", {}).get("lng", 77.2),
                "food_name": d.get("food_name", "Food"),
                "location":  d.get("location", "Unknown"),
                "id":        did
            })

    if not pickups:
        return {"error": "No valid donations found"}

    # Get best NGO as delivery point
    active_ngos = [n for n in ngos if n.get("active", True)]
    if not active_ngos:
        return {"error": "No NGOs available"}

    # Find nearest NGO to centroid of pickups
    avg_lat = sum(p["lat"] for p in pickups) / len(pickups)
    avg_lng = sum(p["lng"] for p in pickups) / len(pickups)
    delivery = min(active_ngos, key=lambda n: haversine_km(avg_lat, avg_lng, n.get("lat",0), n.get("lng",0)))

    # Run routing
    result = ortools_route(depot, pickups, delivery)
    result["volunteer"] = volunteer.get("name")
    result["volunteer_id"] = volunteer_id

    return result


# ── API endpoint to add in app.py ──
# @app.route("/api/plan_route", methods=["POST"])
# @login_required
# def plan_route():
#     data = request.get_json()
#     volunteer_id  = data.get("volunteer_id", session["user_id"])
#     donation_ids  = data.get("donation_ids", [])
#     result = plan_volunteer_route(volunteer_id, donation_ids)
#     return jsonify({"success": True, "route": result})


if __name__ == "__main__":
    # Test
    print("🗺️  Testing OR-Tools routing...")
    test_result = plan_volunteer_route("u004", ["d001", "d002"])
    print(json.dumps(test_result, indent=2))