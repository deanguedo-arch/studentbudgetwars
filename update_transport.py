import json

filepath = r"c:\Users\dean.guedo\Documents\GitHub\studentbudgetwars\data\transport.json"

with open(filepath, 'r') as f:
    transport = json.load(f)

transport.append({
    "id": "scooter_moped",
    "name": "Scooter / Moped",
    "description": "Faster than a bike, cheaper than a car, but vulnerable to bad weather and theft.",
    "upfront_cost": 800,
    "monthly_payment": 0,
    "insurance_cost": 30,
    "fuel_maintenance_cost": 35,
    "commute_stress_delta": 0,
    "commute_time_modifier": 1,
    "access_level": 2,
    "reliability": 0.85,
    "breakdown_risk": 0.05,
    "repair_event_weight": 0.15,
    "odd_hour_access": 60,
    "liquidity_pressure": 25,
    "quality_score": 62
})

transport.append({
    "id": "luxury_financed_car",
    "name": "Luxury Financed Car",
    "description": "Incredible comfort and reliability, but the massive payment will strangle your budget.",
    "upfront_cost": 1500,
    "monthly_payment": 650,
    "insurance_cost": 280,
    "fuel_maintenance_cost": 220,
    "commute_stress_delta": -1,
    "commute_time_modifier": -3,
    "access_level": 5,
    "reliability": 0.98,
    "breakdown_risk": 0.02,
    "repair_event_weight": 0.2, # repairs are rare but extremely expensive
    "odd_hour_access": 100,
    "liquidity_pressure": 95,
    "quality_score": 95
})

with open(filepath, 'w') as f:
    json.dump(transport, f, indent=2)

print("Updated transport.json successfully.")
