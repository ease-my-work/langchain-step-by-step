"""Fake data for Bean Street Coffee: products, customers and orders.

This plays the part of the shop's database, so results are predictable and need no internet.
In a real app, the tools in each step would query your database or API instead.
Prices are in Indian rupees (₹). "Today" in this made-up shop is 10 October 2026.
"""

PRODUCTS = {
    "BEAN-MAL": {
        "name": "Monsoon Malabar beans, 250 g",
        "category": "beans",
        "price": 650,
        "stock": 42,
        "notes": "Low acidity, earthy and spicy. Medium-dark roast.",
    },
    "BEAN-CRG": {
        "name": "Coorg Estate Arabica beans, 250 g",
        "category": "beans",
        "price": 720,
        "stock": 0,
        "notes": "Chocolate and orange notes. Medium roast. Back in stock on 20 October.",
    },
    "BEAN-CHK": {
        "name": "Chikmagalur Dark Roast beans, 250 g",
        "category": "beans",
        "price": 580,
        "stock": 18,
        "notes": "Bold and smoky. Great for espresso and South Indian filter coffee.",
    },
    "BEAN-DCF": {
        "name": "Swiss Water Decaf beans, 250 g",
        "category": "beans",
        "price": 790,
        "stock": 7,
        "notes": "99.9% caffeine free, caramel sweetness. Medium roast.",
    },
    "GRD-HAND": {
        "name": "Steel Hand Grinder",
        "category": "grinders",
        "price": 2400,
        "stock": 12,
        "notes": "Conical steel burrs, 40 grind settings. Fits in a travel bag.",
    },
    "GRD-ELEC": {
        "name": "Flat Burr Electric Grinder",
        "category": "grinders",
        "price": 8900,
        "stock": 3,
        "notes": "64 mm flat burrs, from espresso fine to cold-brew coarse.",
    },
    "BRW-FRP": {
        "name": "French Press, 600 ml",
        "category": "brewers",
        "price": 1450,
        "stock": 25,
        "notes": "Borosilicate glass with a double steel filter.",
    },
    "BRW-POUR": {
        "name": "Pour-Over Starter Kit",
        "category": "brewers",
        "price": 1990,
        "stock": 9,
        "notes": "Ceramic dripper, glass server and 100 paper filters.",
    },
    "BRW-FILT": {
        "name": "South Indian Filter, steel",
        "category": "brewers",
        "price": 890,
        "stock": 30,
        "notes": "Classic two-part steel filter for strong decoction.",
    },
    "ESP-HOME": {
        "name": "Home Espresso Machine",
        "category": "espresso machines",
        "price": 24500,
        "stock": 2,
        "notes": "15-bar pump, steam wand, 2-year warranty.",
    },
}

CUSTOMERS = {
    "C-001": {"name": "Asha", "email": "asha@example.com", "tier": "gold", "points": 1840},
    "C-002": {"name": "Rahul", "email": "rahul@example.com", "tier": "silver", "points": 420},
    "C-003": {"name": "Meera", "email": "meera@example.com", "tier": "bronze", "points": 60},
}

ORDERS = {
    "BS-1001": {
        "customer_id": "C-001",
        "placed": "2026-10-02",
        "items": ["BEAN-MAL", "BEAN-MAL", "BRW-FRP"],
        "total": 2750,
        "status": "delivered",
        "delivered_on": "2026-10-06",
    },
    "BS-1002": {
        "customer_id": "C-001",
        "placed": "2026-10-08",
        "items": ["GRD-ELEC"],
        "total": 8900,
        "status": "shipped",
        "courier": "BlueDart",
        "tracking": "BD7731002",
        "expected_delivery": "2026-10-12",
    },
    "BS-1003": {
        "customer_id": "C-002",
        "placed": "2026-10-09",
        "items": ["BEAN-CHK", "BRW-FILT"],
        "total": 1470,
        "status": "processing",
        "expected_dispatch": "2026-10-11",
    },
    "BS-1004": {
        "customer_id": "C-002",
        "placed": "2026-09-20",
        "items": ["ESP-HOME"],
        "total": 24500,
        "status": "delivered",
        "delivered_on": "2026-09-24",
    },
    "BS-1005": {
        "customer_id": "C-003",
        "placed": "2026-10-01",
        "items": ["BEAN-DCF"],
        "total": 790,
        "status": "cancelled",
        "cancel_reason": "Payment failed",
    },
}
