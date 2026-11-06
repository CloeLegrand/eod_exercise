from dataclasses import dataclass
from datetime import datetime

@dataclass
class PricePoint:
    """Un prix de clôture à une date donnée.
    @dataclass crée automatiquement le __init__ : on peut écrire
    PricePoint(une_date, 150.0) sans code supplémentaire.
    """
    date: datetime
    close: float

class PriceHistory:
    """Stocke l'historique des prix et les éventuelles corrections de clôture."""

    def __init__(self, series: dict):
        """'series' est un dict {ticker: [PricePoint, PricePoint, ...]}."""
        self._series = series      # historique brut (jamais modifié)
        self._corrections = {}     # {ticker: prix corrigé}, rangé à part

    def apply_corrections(self, corrections: dict) -> None:
        """Enregistre les prix corrigés envoyés par la bourse ({ticker: prix}).

        Lève une erreur si on corrige un ticker qui n'existe pas.
        """
        for ticker, close in corrections.items():
            if ticker not in self._series:
                raise KeyError(f"Correction for unknown ticker: {ticker}")
            self._corrections[ticker] = close

    def closes(self, ticker: str) -> list:
        """Retourne la liste des prix bruts d'un ticker (sert aux calculs de risque)."""
        return [point.close for point in self._series[ticker]]

    def last_price(self, ticker: str) -> float:
        """Retourne le prix de valorisation : la correction si elle existe,
        sinon la dernière clôture."""
        if ticker in self._corrections:
            return self._corrections[ticker]
        return self._series[ticker][-1].close

    def as_of(self) -> datetime:
        """Retourne la date du rapport (la dernière date de prix disponible)."""
        return max(points[-1].date for points in self._series.values())

class FxConverter:
    """Convertit des montants dans la devise du rapport (l'EUR)."""

    def __init__(self, rates: dict):
        """'rates' est un dict de taux, ex. {"EURUSD": 1.08}."""
        self._rates = rates

    def to_eur(self, amount: float, ccy: str) -> float:
        """Convertit 'amount' (exprimé en devise 'ccy') en euros."""
        if ccy == "EUR":
            return amount
        pair = "EUR" + ccy  # ex. "EURUSD"
        if pair not in self._rates:
            raise ValueError(f"Missing FX rate {pair}")
        return amount / self._rates[pair]
