# data/json_manager.py
import json
import os
from abc import ABC, abstractmethod


class JsonManager(ABC):
    def __init__(self, json_path):
        self.json_path = json_path

    def load(self):
        if not os.path.exists(self.json_path):
            return []
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @abstractmethod
    def validate(self, item):
        """Implementáld az adott adattípus validációját."""
        pass

    def find_by_name(self, name):
        data = self.load()
        for item in data:
            if item.get("name", "").strip().lower() == name.strip().lower():
                return item
        return None