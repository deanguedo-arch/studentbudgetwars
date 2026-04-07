import json
import os

filepath = r"c:\Users\dean.guedo\Documents\GitHub\studentbudgetwars\data\careers.json"

with open(filepath, 'r') as f:
    careers = json.load(f)

for career in careers:
    # Add skill_transfer_map
    if career['id'] == 'retail_service':
        career['skill_transfer_map'] = {'sales': 0.4, 'office_admin': 0.2}
    elif career['id'] == 'warehouse_logistics':
        career['skill_transfer_map'] = {'delivery_gig': 0.3, 'trades_apprenticeship': 0.2}
    elif career['id'] == 'delivery_gig':
        career['skill_transfer_map'] = {'warehouse_logistics': 0.3, 'sales': 0.2}
    elif career['id'] == 'office_admin':
        career['skill_transfer_map'] = {'sales': 0.3, 'degree_gated_professional': 0.3}
    elif career['id'] == 'trades_apprenticeship':
        career['skill_transfer_map'] = {'warehouse_logistics': 0.3}
    elif career['id'] == 'healthcare_support':
        career['skill_transfer_map'] = {'office_admin': 0.2}
    elif career['id'] == 'sales':
        career['skill_transfer_map'] = {'retail_service': 0.3, 'office_admin': 0.3}
    elif career['id'] == 'degree_gated_professional':
        career['skill_transfer_map'] = {'office_admin': 0.5, 'sales': 0.4}
    else:
        career['skill_transfer_map'] = {}

    tiers = career['tiers']
    
    # Add seniority_income_bonus to existing
    for i, tier in enumerate(tiers):
        tier['seniority_income_bonus'] = 15 + (i * 10)

    # Create 4th tier
    tier3 = tiers[2]
    tier4 = {
        "label": f"Senior {tier3['label']}",
        "monthly_income": int(tier3['monthly_income'] * 1.3),
        "energy_delta": tier3['energy_delta'] - 1,
        "stress_delta": tier3['stress_delta'] + 2,
        "life_satisfaction_delta": tier3['life_satisfaction_delta'] + 1,
        "social_stability_delta": tier3['social_stability_delta'],
        "promotion_target": tier3['promotion_target'] + 3,
        "required_credential_ids": list(tier3['required_credential_ids']),
        "required_minimum_gpa": tier3['required_minimum_gpa'],
        "required_pass_state": tier3['required_pass_state'],
        "seniority_income_bonus": 45
    }

    if career['id'] == 'retail_service':
        tier4['label'] = "Store Manager"
    elif career['id'] == 'warehouse_logistics':
        tier4['label'] = "Warehouse Manager"
    elif career['id'] == 'delivery_gig':
        tier4['label'] = "Fleet Operator"
    elif career['id'] == 'office_admin':
        tier4['label'] = "Office Manager"
    elif career['id'] == 'trades_apprenticeship':
        tier4['label'] = "Master Tradesperson"
    elif career['id'] == 'healthcare_support':
        tier4['label'] = "Department Supervisor"
    elif career['id'] == 'sales':
        tier4['label'] = "Sales Manager"
    elif career['id'] == 'degree_gated_professional':
        tier4['label'] = "Director"

    tiers.append(tier4)

    # Create 5th tier
    tier5 = {
        "label": f"Executive {tier4['label']}",
        "monthly_income": int(tier4['monthly_income'] * 1.4),
        "energy_delta": tier4['energy_delta'] - 1,
        "stress_delta": tier4['stress_delta'] + 3,
        "life_satisfaction_delta": tier4['life_satisfaction_delta'] + 2,
        "social_stability_delta": tier4['social_stability_delta'] + 1,
        "promotion_target": tier4['promotion_target'] + 4,
        "required_credential_ids": list(tier4['required_credential_ids']),
        "required_minimum_gpa": tier4['required_minimum_gpa'],
        "required_pass_state": tier4['required_pass_state'],
        "seniority_income_bonus": 60
    }

    if career['id'] == 'retail_service':
        tier5['label'] = "Regional Manager"
    elif career['id'] == 'warehouse_logistics':
        tier5['label'] = "Regional Logistics Director"
    elif career['id'] == 'delivery_gig':
        tier5['label'] = "Logistics Franchisee"
    elif career['id'] == 'office_admin':
        tier5['label'] = "VP of Operations"
    elif career['id'] == 'trades_apprenticeship':
        tier5['label'] = "Shop Owner"
    elif career['id'] == 'healthcare_support':
        tier5['label'] = "Facility Administrator"
    elif career['id'] == 'sales':
        tier5['label'] = "VP of Sales"
    elif career['id'] == 'degree_gated_professional':
        tier5['label'] = "Executive / Partner"

    tiers.append(tier5)

with open(filepath, 'w') as f:
    json.dump(careers, f, indent=2)

print("Updated careers.json successfully.")
