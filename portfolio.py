import logging
from dataclasses import dataclass
from datetime import datetime

from instruments import Instrument

# Crée un canal log dédié au fichier courant
logger = logging.getLogger(__name__)

@dataclass
class Trade:
    """Un trade : date, ticker, quantité signée (+ achat / - vente) et prix."""
    date: datetime
    ticker: str
    qty: float
    price: float

    def __post_init__(self):
        """Vérifie le trade juste après sa création (appelée automatiquement).
        Refuse un prix <= 0 ou une quantité nulle, comme l'original.
        """
        if self.price <= 0:
            raise ValueError(f"Invalid price for {self.ticker}: {self.price}")
        if self.qty == 0:
            raise ValueError(f"Zero quantity for {self.ticker}")

class Position:
    """La position sur un instrument : quantité, prix moyen, PnL réalisé."""

    def __init__(self, instrument: Instrument):
        """Crée une position vide (quantité 0) sur l'instrument donné."""
        self.instrument = instrument
        self.qty = 0.0
        self.avg_price = 0.0
        self.realized_pnl = 0.0  # dans la devise de l'instrument

    def book_trade(self, trade: Trade) -> None:
        """Met à jour la position avec un nouveau trade.
        - Même sens que la position (ou position vide) : nouveau prix moyen.
        - Sens contraire : on réalise du PnL sur la quantité fermée.
        - Si on dépasse la quantité détenue, la position se retourne.
        """
        old_qty = self.qty
        qty = trade.qty
        price = trade.price

        if old_qty == 0 or (old_qty > 0) == (qty > 0):
            # On ouvre ou on renforce : prix moyen pondéré.
            self.avg_price = (self.avg_price * old_qty + price * qty) / (old_qty + qty)
            self.qty = old_qty + qty
        else:
            # On réduit, on ferme ou on retourne : PnL réalisé sur la partie fermée.
            sign = 1 if old_qty > 0 else -1
            closed_qty = min(abs(qty), abs(old_qty)) * sign
            self.realized_pnl += self.instrument.compute_pnl(closed_qty, self.avg_price, price)

            new_qty = old_qty + qty
            if new_qty == 0:
                self.avg_price = 0.0
            elif (new_qty > 0) != (old_qty > 0):
                self.avg_price = price  # retournement : le reste est une nouvelle position
            self.qty = new_qty

    def unrealized_pnl(self, price: float) -> float:
        """Retourne le PnL latent (non encore encaissé) au prix donné."""
        return self.instrument.compute_pnl(self.qty, self.avg_price, price)

    def exposure(self, price: float) -> float:
        """Retourne l'exposition de la position au prix donné."""
        return self.instrument.compute_exposure(self.qty, price)

class Portfolio:
    """Contient toutes les positions et sait y enregistrer des trades."""

    def __init__(self, instrument_catalog: dict):
        """'instrument_catalog' est un dict {ticker: Instrument} des instruments connus."""
        self._catalog = instrument_catalog
        self.positions = {}  # {ticker: Position}, rempli au fur et à mesure

    def book_trade(self, trade: Trade) -> None:
        """Enregistre un trade : trouve (ou crée) la bonne position, puis la met à jour."""
        if trade.ticker not in self._catalog:
            raise ValueError(f"Unknown instrument: {trade.ticker}")

        # On crée la position la première fois qu'on voit ce ticker.
        if trade.ticker not in self.positions:
            self.positions[trade.ticker] = Position(self._catalog[trade.ticker])

        self.positions[trade.ticker].book_trade(trade)
        logger.info("BOOKED - %s", trade)  # message de journal (voir main.py)

    def book_all(self, trades) -> None:
        """Enregistre une liste de trades, un par un."""
        for trade in trades:
            self.book_trade(trade)
