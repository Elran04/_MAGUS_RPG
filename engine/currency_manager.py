"""
Currency management system for MAGUS RPG.

This module handles currency conversions, calculations, and formatting
for the game's currency system (réz, ezüst, arany, mithrill).
"""

class CurrencyManager:
    """
    Manages currency conversions and formatting for the game.
    
    Supports conversion between réz (copper), ezüst (silver), arany (gold), 
    and mithrill currencies with fixed exchange rates.
    
    Attributes:
        RATES (dict): Exchange rates relative to réz (base currency)
        ORDER (list): Currency order from smallest to largest denomination
    """
    RATES = {
        "réz": 1,
        "ezüst": 100,
        "arany": 1000,
        "mithrill": 100000
    }
    ORDER = ["réz", "ezüst", "arany", "mithrill"]

    def to_base(self, amount, currency):
        """
        Bármely pénznemet átvált rézre (alap).
        """
        return amount * self.RATES[currency]

    def from_base(self, amount):
        """
        Réz összeget felbont a legnagyobb pénznemekre.
        """
        result = {}
        remaining = amount
        for curr in reversed(self.ORDER):
            count = remaining // self.RATES[curr]
            if count:
                result[curr] = int(count)
                remaining -= count * self.RATES[curr]
        if remaining:
            result["réz"] = remaining
        return result

    def convert(self, amount, from_curr, to_curr):
        """
        Átvált egyik pénznemből a másikba.
        """
        base = self.to_base(amount, from_curr)
        return base // self.RATES[to_curr]

    def format(self, amount):
        """
        Formázott szöveg (pl. 2 arany, 5 ezüst, 13 réz).
        """
        parts = []
        for curr in reversed(self.ORDER):
            count = amount // self.RATES[curr]
            if count:
                parts.append(f"{count} {curr}")
                amount -= count * self.RATES[curr]
        return ', '.join(parts) if parts else "0 réz"
