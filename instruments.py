from abc import ABC, abstractmethod

class Instrument(ABC):
    """Modèle commun à tous les instruments (classe mère abstraite).
    Les classes Equity, Future ou Bond héritent de cette classe.
    """

    def __init__(self, ticker: str, ccy: str):
        """Mémorise le ticker (ex. "AAPL") et la devise de cotation (ex. "USD")."""
        self.ticker = ticker
        self.ccy = ccy

    @abstractmethod
    def _scale(self, amount: float) -> float:
        """Applique la règle propre au type d'instrument à un montant brut.
        Chaque classe fille la doit définir.
        """

    def compute_exposure(self, qty: float, price: float) -> float:
        """Retourne l'exposition (valeur de marché) dans la devise de l'instrument.
        On fait quantité x prix, puis on applique la règle du type via _scale.
        """
        return self._scale(qty * price)

    def compute_pnl(self, qty: float, entry_price: float, exit_price: float) -> float:
        """Retourne le gain/perte (PnL) dans la devise de l'instrument.
        On fait quantité x (prix de sortie - prix d'entrée), puis on applique
        la règle du type via _scale.
        """
        return self._scale(qty * (exit_price - entry_price))


class Equity(Instrument):
    """Une action : le montant brut est déjà le bon montant."""

    def _scale(self, amount: float) -> float:
        """Ne change rien au montant."""
        return amount


class Future(Instrument):
    """Un future : chaque point de prix vaut 'multiplier' unités de devise."""

    def __init__(self, ticker: str, ccy: str, multiplier: int):
        """Appel le constructeur de la classe mère, plus le multiplicateur du contrat (ex. 10)."""
        super().__init__(ticker, ccy) 
        self.multiplier = multiplier

    def _scale(self, amount: float) -> float:
        """Multiplie le montant par le multiplicateur du contrat."""
        return amount * self.multiplier


# constante explicite déclarée pour convertir un prix en % en chiffre.
BOND_PAR = 100


class Bond(Instrument):
    """Une obligation : prix en % du nominal, quantité = nominal."""

    def _scale(self, amount: float) -> float:
        """Divise par 100 (passage de "%" à un montant)."""
        return amount / BOND_PAR


# Dictionnaire qui associe le texte lu dans les csv aux classes respectives 
INSTRUMENT_TYPES = {
    "equity": Equity,
    "future": Future,
    "bond": Bond,
}

def create_instrument(row: dict) -> Instrument:
    """Crée le bon objet (Equity, Future ou Bond) à partir d'une ligne du CSV.
    'row' est un dict du genre {"ticker": "AAPL", "type": "equity", "ccy": "USD", ...}.
    Lève une erreur si le type est inconnu.
    """
    type_name = row["type"]
    if type_name not in INSTRUMENT_TYPES:
        raise ValueError(f"Unknown instrument type: {type_name}")

    if type_name == "future":  # seul type qui a besoin d'une donnée en plus
        return Future(row["ticker"], row["ccy"], int(row["multiplier"]))
    return INSTRUMENT_TYPES[type_name](row["ticker"], row["ccy"])
