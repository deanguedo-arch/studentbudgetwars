import json

paths = {
    "housing": r"c:\Users\dean.guedo\Documents\GitHub\studentbudgetwars\data\housing.json",
    "transport": r"c:\Users\dean.guedo\Documents\GitHub\studentbudgetwars\data\transport.json"
}

with open(paths["housing"], "r") as f:
    housing = json.load(f)

for h in housing:
    if h["id"] == "solo_rental":
        h["minimum_credit_score"] = 680
    elif h["id"] == "roommates":
        h["minimum_credit_score"] = 550
    else:
        h["minimum_credit_score"] = 300 # Base score

with open(paths["housing"], "w") as f:
    json.dump(housing, f, indent=2)


with open(paths["transport"], "r") as f:
    transport = json.load(f)

for t in transport:
    if t["id"] == "financed_car":
        t["minimum_credit_score"] = 620
    elif t["id"] == "reliable_used_car":
        t["minimum_credit_score"] = 550
    elif t["id"] == "luxury_financed_car":
        t["minimum_credit_score"] = 720
    else:
        t["minimum_credit_score"] = 300

with open(paths["transport"], "w") as f:
    json.dump(transport, f, indent=2)

print("Updated credit constraints.")
