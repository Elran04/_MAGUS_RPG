"""
Character class database manager for MAGUS RPG.

This module provides the ClassDBManager for managing character class data
stored in an SQLite database, including stats, combat values, and level requirements.
"""

import sqlite3

DB_PATH = "d:/_Projekt/_MAGUS_RPG/data/Class/class_data.db"

class ClassDBManager:
    """
    Manages character class data from the SQLite database.
    
    Handles retrieval and updating of class information including stat ranges,
    combat statistics, level requirements, and starting currency.
    
    Attributes:
        db_path (str): Path to the class database file
    """
    def __init__(self, db_path=DB_PATH):
        """
        Initialize ClassDBManager.
        
        Args:
            db_path (str, optional): Path to the database file. Defaults to DB_PATH.
        """
        self.db_path = db_path

    def get_connection(self):
        """
        Get a connection to the database.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        return sqlite3.connect(self.db_path)

    def list_classes(self):
        """
        Get list of all available character classes.
        
        Returns:
            list: List of tuples (id, name) for all classes
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM classes ORDER BY name")
            return cursor.fetchall()

    def get_class_details(self, class_id):
        """
        Get complete details for a character class.
        
        Args:
            class_id: The class ID to retrieve
            
        Returns:
            dict: Dictionary containing class name, stats, combat_stats, 
                  level_requirements, starting_currency, and extra_xp
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Get class name
            cursor.execute("SELECT name FROM classes WHERE id = ?", (class_id,))
            name = cursor.fetchone()[0]
            # Get stat ranges, including double_chance
            cursor.execute("SELECT stat_name, min_value, max_value, double_chance FROM stats WHERE class_id = ?", (class_id,))
            stats = cursor.fetchall()
            # Get combat stats
            cursor.execute("SELECT * FROM combat_stats WHERE class_id = ?", (class_id,))
            combat_stats = cursor.fetchone()
            # Get level requirements
            cursor.execute("SELECT level, xp FROM level_requirements WHERE class_id = ? ORDER BY level", (class_id,))
            level_requirements = cursor.fetchall()
            # Get starting currency
            cursor.execute("SELECT min_gold, max_gold FROM starting_currency WHERE class_id = ?", (class_id,))
            starting_currency = cursor.fetchone()
            # Get further level requirements
            cursor.execute("SELECT extra_xp FROM further_level_requirements WHERE class_id = ?", (class_id,))
            extra_xp = cursor.fetchone()
            return {
                "name": name,
                "stats": stats,
                "combat_stats": combat_stats,
                "level_requirements": level_requirements,
                "starting_currency": starting_currency,
                "extra_xp": extra_xp[0] if extra_xp else None
            }

    def update_class_name(self, class_id, new_name):
        """
        Update the name of a character class.
        
        Args:
            class_id: The class ID to update
            new_name (str): New name for the class
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE classes SET name = ? WHERE id = ?", (new_name, class_id))
            conn.commit()

    # Add more update/insert/delete methods as needed for stats, combat stats, etc.
