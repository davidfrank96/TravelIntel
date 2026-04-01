"""
Prompt templates for the TravelIntel briefing generator.
"""

FACTS_SYSTEM = """
You are an intelligence analyst producing factual, structured travel intelligence.
Return ONLY valid JSON that matches the requested schema. Do not include markdown.
""".strip()

FACTS_USER = """
Generate structured travel intelligence for the traveler below.

Traveler:
- Name: {name}
- Nationality: {nationality}
- Destination country: {country}
- Destination city: {city}
- Travel date: {travel_date}
- Trip type: {trip_type}

Schema (JSON keys and types):
{{
  "risk_grade": "A|B|C|D|E",
  "security_snapshot": "short paragraph",
  "emergency_numbers": [{{"label": "string", "number": "string"}}],
  "consulate": {{"name": "string", "address": "string", "phone": "string", "website": "string"}},
  "hospitals": [{{"name": "string", "address": "string", "phone": "string"}}],
  "legal_restrictions": ["string"],
  "cultural_dos": ["string"],
  "cultural_donts": ["string"],
  "operational_guidance": ["string"],
  "key_locations": ["string"]
}}

If any item is unknown, return an empty string or empty list for that field.
""".strip()

NARRATIVE_SYSTEM = """
You are an intelligence briefer writing a concise, personalized, CIA-style travel briefing.
Use the provided facts and address the traveler directly by name.
""".strip()

NARRATIVE_USER = """
Traveler name: {name}
Nationality: {nationality}
Destination: {city}, {country}
Travel date: {travel_date}
Trip type: {trip_type}

Facts JSON:
{facts_json}

Write a clear, structured briefing with headings. Keep it actionable.
""".strip()
