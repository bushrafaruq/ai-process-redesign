"""Request taxonomy: categories, owning teams, priority levels and service levels.

The taxonomy is a design artefact of the case study (see docs/03_future_state.md).
It describes a generic residential operation (student / co-living building).
No employer data is used anywhere in this project.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    key: str
    label: str
    owner: str
    description: str


CATEGORIES: dict[str, Category] = {
    c.key: c
    for c in [
        Category("maintenance_plumbing", "Plumbing", "Maintenance",
                 "Leaks, blocked drains, toilets, showers, taps, water pressure"),
        Category("maintenance_general", "General repairs & appliances", "Maintenance",
                 "Sockets, lights, fuses, appliances, doors, windows, furniture, lifts"),
        Category("heating_hvac", "Heating & hot water", "Maintenance",
                 "Radiators, heating, hot water, ventilation"),
        Category("access_keys", "Access & keys", "Front Desk",
                 "Lockouts, lost key cards, door entry, fobs"),
        Category("billing_payments", "Billing & payments", "Finance",
                 "Rent, invoices, deposits, refunds, direct debits"),
        Category("noise_conduct", "Noise & neighbours", "Community Team",
                 "Noise complaints, disputes, house rules"),
        Category("cleaning_waste", "Cleaning & waste", "Housekeeping",
                 "Common-area cleaning, bins, pests"),
        Category("internet_wifi", "Internet & Wi-Fi", "IT Provider",
                 "Wi-Fi, network access, device connection"),
        Category("move_in_out", "Move-in & move-out", "Front Desk",
                 "Arrivals, check-out, inspections, contracts, transfers"),
        Category("general_enquiry", "General enquiry", "Front Desk",
                 "Parcels, guests, feedback, anything that fits no other category"),
        Category("safety_security", "Safety & security", "Duty Manager",
                 "Fire alarms, gas smell, injuries, intruders, threats"),
    ]
}

OWNERS = sorted({c.owner for c in CATEGORIES.values()})

# Priority definitions and target first-response times (hours).
PRIORITIES = {
    "P1": {"label": "Urgent", "first_response_hours": 1,
           "rule": "Risk to people or property, or resident cannot access or use their room"},
    "P2": {"label": "High", "first_response_hours": 8,
           "rule": "Essential service degraded (e.g. no hot water, no Wi-Fi) or money at stake"},
    "P3": {"label": "Standard", "first_response_hours": 48,
           "rule": "Everything else: routine repairs, questions, scheduling"},
}
