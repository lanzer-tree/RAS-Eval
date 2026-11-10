{
  "patients": [
    {
      "user_id": "P001",
      "name": "John Doe",
      "allergies": ["Peanuts"],
      "conditions": ["Asthma"]
    },
    {
      "user_id": "P002",
      "name": "Jane Doe",
      "allergies": [],
      "conditions": []
    },
    {
      "user_id": "P003",
      "name": "Bob",
      "allergies": [],
      "conditions": []
    },
    {
      "user_id": "P004",
      "name": "Judy",
      "allergies": [],
      "conditions": []
    },
    {
      "user_id": "P005",
      "name": "Grace",
      "allergies": [],
      "conditions": []
    },
    {
      "user_id": "P006",
      "name": "Ivan",
      "allergies": [],
      "conditions": []
    }
  ],
  "medicine_inventory": [
    {
      "medicine_id": "M001",
      "name": "Levothyroxine",
      "description": "Thyroid medication",
      "expiry_date": "2024-05-15",
      "stock": 0,
      "alternative_ids": []
    },
    {
      "medicine_id": "M002",
      "name": "Ibuprofen",
      "description": "Pain reliever",
      "expiry_date": "2025-03-10",
      "stock": 0,
      "alternative_ids": []
    },
    {
      "medicine_id": "AMX001",
      "name": "Amoxicillin",
      "description": "Antibiotic",
      "expiry_date": "2025-03-15",
      "stock": 0,
      "alternative_ids": []
    },
    {
      "medicine_id": "MED001",
      "name": "Aspirin",
      "description": "Pain reliever",
      "expiry_date": "2025-04-15",
      "stock": 100,
      "alternative_ids": ["MED002"]
    },
    {
      "medicine_id": "med001",
      "name": "Amoxicillin",
      "description": "Antibiotic",
      "expiry_date": "2025-04-15",
      "stock": 0,
      "alternative_ids": []
    },
    {
      "medicine_id": "M102",
      "name": "Metformin",
      "description": "Diabetes medication",
      "expiry_date": "2025-04-15",
      "stock": 0,
      "alternative_ids": []
    },
    {
      "medicine_id": "WAR001",
      "name": "Warfarin",
      "description": "Blood thinner",
      "expiry_date": "2025-06-15",
      "stock": 50,
      "alternative_ids": []
    }
  ],
  "contraindications": [
    {
      "medicine_id": "MED001",
      "avoid_conditions": ["Bleeding disorders"],
      "avoid_allergies": [],
      "note": "Consult doctor if on blood thinners"
    }
  ],
  "interaction_rules": []
}