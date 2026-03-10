from datetime import datetime, date, timedelta
from typing import Optional, List


# ─── Date Helpers ─────────────────────────────────────────────────────
def parse_date(date_str: str) -> Optional[date]:
    if not date_str:
        return None
    try:
        return datetime.strptime(str(date_str)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def format_date(date_str: str, fmt: str = "%b %d, %Y") -> str:
    d = parse_date(date_str)
    return d.strftime(fmt) if d else "—"


def format_date_range(start: str, end: str) -> str:
    s, e = parse_date(start), parse_date(end)
    if not s or not e:
        return "—"
    if s.year == e.year:
        if s.month == e.month:
            return f"{s.strftime('%b %d')} – {e.strftime('%d, %Y')}"
        return f"{s.strftime('%b %d')} – {e.strftime('%b %d, %Y')}"
    return f"{s.strftime('%b %d, %Y')} – {e.strftime('%b %d, %Y')}"


def get_trip_days(start: str, end: str) -> int:
    s, e = parse_date(start), parse_date(end)
    if not s or not e:
        return 0
    return max(0, (e - s).days + 1)


def get_trip_status(trip: dict) -> str:
    today = date.today()
    s = parse_date(trip.get("start_date", ""))
    e = parse_date(trip.get("end_date", ""))
    if not s or not e:
        return "Planning"
    if today < s:
        return "Upcoming"
    elif today > e:
        return "Completed"
    return "Active"


def get_days_until(date_str: str) -> int:
    d = parse_date(date_str)
    if not d:
        return 0
    return (d - date.today()).days


def get_all_trip_dates(trip: dict) -> List[date]:
    s = parse_date(trip.get("start_date", ""))
    e = parse_date(trip.get("end_date", ""))
    if not s or not e:
        return []
    dates, cur = [], s
    while cur <= e:
        dates.append(cur)
        cur += timedelta(days=1)
    return dates


# ─── Formatting ───────────────────────────────────────────────────────
def format_currency(amount: float, currency: str = "USD") -> str:
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥",
        "AUD": "A$", "CAD": "C$", "CHF": "CHF ", "INR": "₹",
        "CNY": "¥", "SGD": "S$", "THB": "฿", "MXN": "MX$", "BRL": "R$",
    }
    sym = symbols.get(currency, currency + " ")
    if amount >= 1000:
        return f"{sym}{amount:,.0f}"
    return f"{sym}{amount:.2f}"


def get_status_color(status: str) -> str:
    return {
        "Planning": "#6b7280",
        "Upcoming": "#4a8cf0",
        "Active": "#10c97a",
        "Completed": "#9b6cf8",
    }.get(status, "#6b7280")


# ─── Constants ────────────────────────────────────────────────────────
TRIP_TYPES = [
    "Adventure", "Beach & Sun", "City Break", "Cultural",
    "Business", "Backpacking", "Luxury", "Road Trip", "Family", "Honeymoon",
]

CURRENCIES = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "INR", "CNY", "SGD", "THB", "MXN", "BRL"]

COVER_EMOJIS = [
    "✈️", "🗺️", "🏖️", "🏔️", "🗼", "🏯", "🗽", "🌴", "🎡", "🚂",
    "🛳️", "🌏", "🎌", "🦁", "🌺", "🏜️", "🌋", "🏰", "🎭", "🍜",
]

ACTIVITY_CATEGORIES = {
    "🍽️ Food & Dining": "food",
    "🏛️ Culture & History": "culture",
    "🌿 Nature & Outdoors": "nature",
    "🎭 Entertainment": "entertainment",
    "🛍️ Shopping": "shopping",
    "🚗 Transport": "transport",
    "🏨 Accommodation": "accommodation",
    "🏃 Activities & Sports": "activity",
    "📸 Sightseeing": "sightseeing",
    "🧘 Wellness": "wellness",
}

ACTIVITY_ICONS = {
    "food": "🍽️", "culture": "🏛️", "nature": "🌿", "entertainment": "🎭",
    "shopping": "🛍️", "transport": "🚗", "accommodation": "🏨",
    "activity": "🏃", "sightseeing": "📸", "wellness": "🧘",
}

EXPENSE_CATEGORIES = [
    "✈️ Flights", "🏨 Hotels", "🍽️ Food & Dining", "🎭 Activities",
    "🚗 Transport", "🛍️ Shopping", "🏥 Health", "📡 Communication", "💳 Misc",
]

EXPENSE_CAT_ICONS = {
    "✈️ Flights": "✈️", "🏨 Hotels": "🏨", "🍽️ Food & Dining": "🍽️",
    "🎭 Activities": "🎭", "🚗 Transport": "🚗", "🛍️ Shopping": "🛍️",
    "🏥 Health": "🏥", "📡 Communication": "📡", "💳 Misc": "💳",
}

EXPENSE_CAT_COLORS = {
    "✈️ Flights": "#4a8cf0",
    "🏨 Hotels": "#00d4aa",
    "🍽️ Food & Dining": "#e8a030",
    "🎭 Activities": "#9b6cf8",
    "🚗 Transport": "#6b7280",
    "🛍️ Shopping": "#f472b6",
    "🏥 Health": "#10c97a",
    "📡 Communication": "#60a5fa",
    "💳 Misc": "#a78bfa",
}

PACKING_CATEGORIES = [
    "📄 Documents", "👔 Clothing", "💻 Electronics", "🧴 Toiletries",
    "💊 Health & Safety", "💵 Money & Finance", "📷 Photography",
    "🎒 Gear", "🍎 Snacks", "🏖️ Beach / Outdoors",
]

DEFAULT_PACKING = {
    "📄 Documents": [
        ("Passport", True), ("Travel insurance docs", True), ("Visa documents", True),
        ("Hotel confirmations", False), ("Flight tickets", True), ("Driver's license", False), ("Emergency contacts", True),
    ],
    "👔 Clothing": [
        ("Underwear", True), ("Socks", True), ("T-shirts", True), ("Pants / Jeans", True),
        ("Formal wear", False), ("Pajamas", True), ("Swimwear", False),
        ("Rain jacket", False), ("Walking shoes", True), ("Sandals / Flip flops", False),
    ],
    "💻 Electronics": [
        ("Phone + charger", True), ("Laptop + charger", False), ("Universal power adapter", True),
        ("Headphones", False), ("Power bank", True), ("Camera", False),
    ],
    "🧴 Toiletries": [
        ("Toothbrush & paste", True), ("Shampoo", True), ("Conditioner", False),
        ("Body wash", True), ("Deodorant", True), ("Razor", False), ("Sunscreen", True),
    ],
    "💊 Health & Safety": [
        ("Prescription medications", True), ("Pain relievers", True), ("Antidiarrheal", False),
        ("Antihistamine", False), ("First aid kit", False), ("Hand sanitizer", True), ("Face masks", False),
    ],
    "💵 Money & Finance": [
        ("Cash (local currency)", True), ("Credit card", True), ("Debit card", True), ("Travel wallet", False),
    ],
}

MAP_LOCATION_CATEGORIES = {
    "🏛️ Attraction": "attraction",
    "🍽️ Restaurant": "restaurant",
    "🏨 Hotel / Stay": "hotel",
    "🚉 Transport Hub": "transport",
    "🛍️ Shopping": "shopping",
    "🌿 Nature / Park": "nature",
    "🏥 Medical": "medical",
    "📌 Other": "other",
}

MAP_MARKER_COLORS = {
    "attraction": "#4a8cf0",
    "restaurant": "#e8a030",
    "hotel": "#00d4aa",
    "transport": "#6b7280",
    "shopping": "#f472b6",
    "nature": "#10c97a",
    "medical": "#f04a4a",
    "other": "#9b6cf8",
}

TIME_SLOTS = ["🌅 Morning", "☀️ Afternoon", "🌆 Evening", "🌙 Night"]
SLOT_MAP = {
    "🌅 Morning": "morning", "☀️ Afternoon": "afternoon",
    "🌆 Evening": "evening", "🌙 Night": "night",
}
SLOT_EMOJI = {"morning": "🌅", "afternoon": "☀️", "evening": "🌆", "night": "🌙"}
