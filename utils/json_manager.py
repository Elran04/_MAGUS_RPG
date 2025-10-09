"""
Abstract JSON data manager for MAGUS RPG.

This module provides a base class for managing JSON data files with
common load/save functionality and abstract validation.
"""
# data/json_manager.py
import json
import os
from abc import ABC, abstractmethod

class JsonManager(ABC):
    """
    Abstract base class for JSON data management.
    
    Provides common functionality for loading and saving JSON data files,
    with abstract validation that must be implemented by subclasses.
    
    Attributes:
        json_path (str): Path to the JSON data file
    """
    def __init__(self, json_path):
        """
        Initialize JsonManager with a file path.
        
        Args:
            json_path (str): Path to the JSON data file
        """
        self.json_path = json_path

    def load(self):
        """
        Load data from the JSON file.
        
        Returns:
            list: Loaded data, or empty list if file doesn't exist
        """
        if not os.path.exists(self.json_path):
            return []
        with open(self.json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, data):
        """
        Save data to the JSON file.
        
        Args:
            data: Data to save (typically a list or dict)
        """
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @abstractmethod
    def validate(self, item):
        """
        Validate an item's data structure (must be implemented by subclasses).
        
        Args:
            item: Item to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        pass

    def find_by_name(self, name):
        """
        Find an item by name (case-insensitive).
        
        Args:
            name (str): Name to search for
            
        Returns:
            dict or None: Found item, or None if not found
        """
        data = self.load()
        for item in data:
            if item.get("name", "").strip().lower() == name.strip().lower():
                return item
        return None