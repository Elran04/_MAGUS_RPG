from __future__ import annotations


class CurrencyManager:
    RATES: dict[str, int] = {"réz": 1, "ezüst": 100, "arany": 1000, "mithrill": 100000}
    ORDER: list[str] = ["réz", "ezüst", "arany", "mithrill"]

    def to_base(self, amount: int, currency: str) -> int:
        """
        Bármely pénznemet átvált rézre (alap).
        """
        return int(amount) * self.RATES[currency]

    def from_base(self, amount: int) -> dict[str, int]:
        """
        Réz összeget felbont a legnagyobb pénznemekre.
        """
        result: dict[str, int] = {}
        remaining = int(amount)
        for curr in reversed(self.ORDER):
            count = remaining // self.RATES[curr]
            if count:
                result[curr] = int(count)
                remaining -= count * self.RATES[curr]
        if remaining:
            result["réz"] = int(remaining)
        return result

    def convert(self, amount: int, from_curr: str, to_curr: str) -> int:
        """
        Átvált egyik pénznemből a másikba.
        """
        base = self.to_base(amount, from_curr)
        return int(base // self.RATES[to_curr])

    def format(self, amount: int) -> str:
        """
        Formázott szöveg (pl. 2 arany, 5 ezüst, 13 réz).
        """
        parts: list[str] = []
        remaining = int(amount)
        for curr in reversed(self.ORDER):
            count = remaining // self.RATES[curr]
            if count:
                parts.append(f"{int(count)} {curr}")
                remaining -= int(count) * self.RATES[curr]
        return ", ".join(parts) if parts else "0 réz"
