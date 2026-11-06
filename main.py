# module pour écrire dans le journal de trades
import logging
#module pour manipuler les chemins de fichiers 
import os

# On importe nos mudules, les fonctions de chargement et les différentes classes
from data_loader import (BlotterTradeSource, BrokerTradeSource, load_fx_rates,
                         load_instruments, load_price_corrections, load_prices)
from market_data import FxConverter
from portfolio import Portfolio
from report import EodReport
from risk import RiskEngine

# On stocke le chemin vers le dossier "data"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# On définit le nom du fichier texte des trades exécutés
TRADE_LOG_FILE = "trades_log.txt"


# Fonction principale du programme : évite que le code s'exécute dès l'import
def main() -> None:
    """Lance tout le programme : charge les données, book les trades, affiche le rapport."""
    
    # On configure le système de log pour écrire dans le fichier des trade ( il est créé s'il n'existe pas)
    logging.basicConfig(filename=TRADE_LOG_FILE, level=logging.INFO,
                        format="%(asctime)s - %(message)s")

    # Chargement des données
    prices = load_prices(DATA_DIR)
    fx = FxConverter(load_fx_rates(DATA_DIR))
    portfolio = Portfolio(load_instruments(DATA_DIR))

    # Charge et exécute les trades
    sources = [
        BlotterTradeSource(os.path.join(DATA_DIR, "blotter_trades.txt")),
        BrokerTradeSource(os.path.join(DATA_DIR, "broker_trades.csv")),
    ]
    for source in sources:
        portfolio.book_all(source.load())

    # Applique les corrections de marché 
    prices.apply_corrections(load_price_corrections(DATA_DIR))

    # Calcule le risque et génère le rapport
    risk = RiskEngine(portfolio, prices, fx)
    print(EodReport(portfolio, prices, fx, risk).render())


# Python met automatiquement la variable __name__ à "__main__" quand on lance
# CE fichier directement (python main.py). Si un autre fichier fait `import main`,
# __name__ vaut "main" et main() n'est PAS lancée.
if __name__ == "__main__":
    main()
