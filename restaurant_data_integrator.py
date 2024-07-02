# restaurant_data_integrator.py
import json
from difflib import SequenceMatcher

class RestaurantDataIntegrator:
    def __init__(self):
        self.restaurants = []

    def load_data(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.restaurants.extend(data)

    def deduplicate(self):
        unique_restaurants = []
        for restaurant in self.restaurants:
            if not any(self._similar(restaurant['name'], unique['name']) for unique in unique_restaurants):
                unique_restaurants.append(restaurant)
        self.restaurants = unique_restaurants

    def _similar(self, a, b):
        return SequenceMatcher(None, a, b).ratio() > 0.8

    def merge_data(self):
        merged = {}
        for restaurant in self.restaurants:
            name = restaurant['name']
            if name not in merged:
                merged[name] = restaurant
            else:
                for key, value in restaurant.items():
                    if key not in merged[name] or (value and not merged[name][key]):
                        merged[name][key] = value
        self.restaurants = list(merged.values())

    def save_integrated_data(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.restaurants, f, ensure_ascii=False, indent=4)