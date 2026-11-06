import csv
import os
from abc import ABC, abstractmethod
from datetime import datetime

from instruments import create_instrument
from market_data import PriceHistory, PricePoint
from portfolio import Trade

def load_instruments(data_dir: str) -> dict:
    """Lit instruments.csv et retourne un dict {ticker: Instrument}."""
    catalog = {}
    with open(os.path.join(data_dir, "instruments.csv")) as f:
        for row in csv.DictReader(f):
            instrument = create_instrument(row)
            catalog[instrument.ticker] = instrument
    return catalog


def load_fx_rates(data_dir: str) -> dict:
    """Lit fx_rates.csv et retourne un dict {paire: taux}, ex. {"EURUSD": 1.08}."""
    with open(os.path.join(data_dir, "fx_rates.csv")) as f:
        return {row["pair"]: float(row["rate"]) for row in csv.DictReader(f)}


def load_prices(data_dir: str) -> PriceHistory:
    """Lit prices.csv et retourne un PriceHistory (historique des clôtures)."""
    series = {}
    with open(os.path.join(data_dir, "prices.csv")) as f:
        reader = csv.reader(f)
        next(reader)  # on saute la ligne d'en-tête
        for date_text, ticker, close in reader:
            point = PricePoint(datetime.strptime(date_text, "%Y-%m-%d"), float(close))
            series.setdefault(ticker, []).append(point)
    return PriceHistory(series)


def load_price_corrections(data_dir: str) -> dict:
    """Lit price_corrections.csv et retourne un dict {ticker: prix corrigé}."""
    with open(os.path.join(data_dir, "price_corrections.csv")) as f:
        return {row["ticker"]: float(row["close"]) for row in csv.DictReader(f)}

class TradeSource(ABC):
    """Modèle commun des sources de trades : savoir lire un fichier et
    retourner une liste de Trade."""

    def __init__(self, path: str):
        """Mémorise le chemin du fichier à lire."""
        self.path = path

    @abstractmethod
    def load(self) -> list:
        """Lit le fichier et retourne une liste de Trade (à définir dans chaque sous-classe)."""


class BlotterTradeSource(TradeSource):
    """Trades saisis par le desk. Format d'une ligne : date|ticker|side|qty|price"""

    def load(self) -> list:
        """Lit le fichier blotter ; SELL rend la quantité négative."""
        trades = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue  # on ignore les lignes vides
                date_text, ticker, side, qty, price = line.split("|")
                sign = -1 if side == "SELL" else 1
                trades.append(Trade(
                    date=datetime.strptime(date_text, "%Y-%m-%d"),
                    ticker=ticker,
                    qty=sign * float(qty),
                    price=float(price),
                ))
        return trades


class BrokerTradeSource(TradeSource):
    """Trades reçus du broker : CSV avec quantité non signée et colonne side (B/S)."""

    def load(self) -> list:
        """Lit le fichier broker ; side "S" rend la quantité négative."""
        trades = []
        with open(self.path) as f:
            for row in csv.DictReader(f):
                sign = -1 if row["side"] == "S" else 1
                trades.append(Trade(
                    date=datetime.fromisoformat(row["ts"]),
                    ticker=row["sym"],
                    qty=sign * float(row["q"]),
                    price=float(row["px"]),
                ))
        return trades
