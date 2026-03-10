import json
import os
import uuid
from datetime import datetime
from typing import Optional, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


class TripStorage:
    def __init__(self, filepath: str = None):
        if filepath is None:
            filepath = os.path.join(DATA_DIR, "trips.json")
        self.filepath = filepath
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        if not os.path.exists(filepath):
            self._write({"trips": []})

    def _read(self) -> dict:
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"trips": []}

    def _write(self, data: dict):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def _new_id(self) -> str:
        return str(uuid.uuid4())[:8]

    # ─── Trips ───────────────────────────────────────────────────────
    def get_all_trips(self) -> List[dict]:
        return self._read().get("trips", [])

    def get_trip(self, trip_id: str) -> Optional[dict]:
        return next((t for t in self.get_all_trips() if t["id"] == trip_id), None)

    def create_trip(self, trip_data: dict) -> dict:
        data = self._read()
        trip = {
            "id": self._new_id(),
            "created_at": datetime.now().isoformat(),
            "itinerary": {},
            "expenses": [],
            "accommodations": [],
            "packing_list": [],
            "map_locations": [],
            **trip_data,
        }
        data["trips"].append(trip)
        self._write(data)
        return trip

    def update_trip(self, trip_id: str, updates: dict) -> Optional[dict]:
        data = self._read()
        for i, trip in enumerate(data["trips"]):
            if trip["id"] == trip_id:
                data["trips"][i].update(updates)
                data["trips"][i]["updated_at"] = datetime.now().isoformat()
                self._write(data)
                return data["trips"][i]
        return None

    def delete_trip(self, trip_id: str) -> bool:
        data = self._read()
        original = len(data["trips"])
        data["trips"] = [t for t in data["trips"] if t["id"] != trip_id]
        if len(data["trips"]) < original:
            self._write(data)
            return True
        return False

    # ─── Itinerary ───────────────────────────────────────────────────
    def add_activity(self, trip_id: str, date_str: str, activity: dict) -> Optional[dict]:
        trip = self.get_trip(trip_id)
        if not trip:
            return None
        itinerary = trip.get("itinerary", {})
        if date_str not in itinerary:
            itinerary[date_str] = []
        activity["id"] = self._new_id()
        itinerary[date_str].append(activity)
        self.update_trip(trip_id, {"itinerary": itinerary})
        return activity

    def delete_activity(self, trip_id: str, date_str: str, activity_id: str) -> bool:
        trip = self.get_trip(trip_id)
        if not trip:
            return False
        itinerary = trip.get("itinerary", {})
        if date_str in itinerary:
            before = len(itinerary[date_str])
            itinerary[date_str] = [a for a in itinerary[date_str] if a["id"] != activity_id]
            self.update_trip(trip_id, {"itinerary": itinerary})
            return len(itinerary[date_str]) < before
        return False

    # ─── Expenses ────────────────────────────────────────────────────
    def add_expense(self, trip_id: str, expense: dict) -> Optional[dict]:
        trip = self.get_trip(trip_id)
        if not trip:
            return None
        expenses = trip.get("expenses", [])
        expense["id"] = self._new_id()
        expenses.append(expense)
        self.update_trip(trip_id, {"expenses": expenses})
        return expense

    def delete_expense(self, trip_id: str, expense_id: str) -> bool:
        trip = self.get_trip(trip_id)
        if not trip:
            return False
        expenses = trip.get("expenses", [])
        before = len(expenses)
        expenses = [e for e in expenses if e["id"] != expense_id]
        self.update_trip(trip_id, {"expenses": expenses})
        return len(expenses) < before

    # ─── Accommodations ──────────────────────────────────────────────
    def add_accommodation(self, trip_id: str, acc: dict) -> Optional[dict]:
        trip = self.get_trip(trip_id)
        if not trip:
            return None
        accs = trip.get("accommodations", [])
        acc["id"] = self._new_id()
        accs.append(acc)
        self.update_trip(trip_id, {"accommodations": accs})
        return acc

    def delete_accommodation(self, trip_id: str, acc_id: str) -> bool:
        trip = self.get_trip(trip_id)
        if not trip:
            return False
        accs = trip.get("accommodations", [])
        before = len(accs)
        accs = [a for a in accs if a["id"] != acc_id]
        self.update_trip(trip_id, {"accommodations": accs})
        return len(accs) < before

    # ─── Packing List ────────────────────────────────────────────────
    def add_packing_item(self, trip_id: str, item: dict) -> Optional[dict]:
        trip = self.get_trip(trip_id)
        if not trip:
            return None
        packing = trip.get("packing_list", [])
        item["id"] = self._new_id()
        packing.append(item)
        self.update_trip(trip_id, {"packing_list": packing})
        return item

    def toggle_packing_item(self, trip_id: str, item_id: str) -> bool:
        trip = self.get_trip(trip_id)
        if not trip:
            return False
        packing = trip.get("packing_list", [])
        for item in packing:
            if item["id"] == item_id:
                item["packed"] = not item.get("packed", False)
                self.update_trip(trip_id, {"packing_list": packing})
                return True
        return False

    def delete_packing_item(self, trip_id: str, item_id: str) -> bool:
        trip = self.get_trip(trip_id)
        if not trip:
            return False
        packing = trip.get("packing_list", [])
        before = len(packing)
        packing = [i for i in packing if i["id"] != item_id]
        self.update_trip(trip_id, {"packing_list": packing})
        return len(packing) < before

    # ─── Map Locations ───────────────────────────────────────────────
    def add_map_location(self, trip_id: str, location: dict) -> Optional[dict]:
        trip = self.get_trip(trip_id)
        if not trip:
            return None
        locations = trip.get("map_locations", [])
        location["id"] = self._new_id()
        locations.append(location)
        self.update_trip(trip_id, {"map_locations": locations})
        return location

    def delete_map_location(self, trip_id: str, loc_id: str) -> bool:
        trip = self.get_trip(trip_id)
        if not trip:
            return False
        locs = trip.get("map_locations", [])
        before = len(locs)
        locs = [l for l in locs if l["id"] != loc_id]
        self.update_trip(trip_id, {"map_locations": locs})
        return len(locs) < before
