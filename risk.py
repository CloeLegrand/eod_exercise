import math
import statistics

TRADING_DAYS = 252


class RiskEngine:
    """Calcule les indicateurs de risque du portefeuille."""

    def __init__(self, portfolio, prices, fx):
        """Reçoit le portefeuille, l'historique de prix (PriceHistory) et le
        convertisseur de devises (FxConverter)."""
        self.portfolio = portfolio
        self.prices = prices
        self.fx = fx
        self._vol_cache = {}  # mémoire des volatilités déjà calculées

    @staticmethod
    def compute_returns(closes: list) -> list:
        """Transforme une liste de prix en rendements quotidiens (variation en %).

        @staticmethod : cette méthode n'utilise pas self, c'est une simple
        fonction rangée dans la classe parce qu'elle concerne le risque.
        """
        return [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]

    def compute_volatility(self, ticker: str) -> float:
        """Retourne la volatilité annualisée d'un ticker.

        Le résultat est gardé en mémoire (cache) pour ne pas refaire le calcul.
        """
        if ticker not in self._vol_cache:
            returns = self.compute_returns(self.prices.closes(ticker))
            self._vol_cache[ticker] = statistics.stdev(returns) * math.sqrt(TRADING_DAYS)
        return self._vol_cache[ticker]

    def compute_max_drawdown(self, ticker: str) -> float:
        """Retourne la plus grande baisse (en %) entre un sommet et le creux suivant."""
        closes = self.prices.closes(ticker)
        peak = closes[0]  # plus haut atteint jusqu'ici
        max_dd = 0.0
        for close in closes:
            peak = max(peak, close)
            max_dd = max(max_dd, (peak - close) / peak)
        return max_dd

    def compute_portfolio_daily_pnl(self) -> list:
        """Retourne le PnL quotidien (en EUR) du portefeuille.

        On suppose que les positions ACTUELLES étaient déjà détenues pendant
        tout l'historique, et on regarde ce qu'elles auraient gagné chaque jour.
        """
        closes = {t: self.prices.closes(t) for t in self.portfolio.positions}

        # L'original supposait des dates identiques pour tous : on le vérifie.
        lengths = {len(c) for c in closes.values()}
        if len(lengths) != 1:
            raise ValueError("Price histories have different lengths")
        n_days = lengths.pop()

        daily_pnl = []
        for i in range(1, n_days):
            total = 0.0
            for ticker, pos in self.portfolio.positions.items():
                # Plus de if/elif : l'instrument sait calculer son propre PnL.
                pnl = pos.instrument.compute_pnl(pos.qty, closes[ticker][i - 1], closes[ticker][i])
                total += self.fx.to_eur(pnl, pos.instrument.ccy)
            daily_pnl.append(total)
        return daily_pnl

    @staticmethod
    def pnl_volatility(daily_pnl: list) -> float:
        """Retourne la volatilité annualisée du PnL quotidien (en EUR)."""
        return statistics.stdev(daily_pnl) * math.sqrt(TRADING_DAYS)

    @staticmethod
    def pnl_max_drawdown(daily_pnl: list) -> float:
        """Retourne la plus grande baisse (en EUR) du PnL cumulé."""
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for pnl in daily_pnl:
            cumulative += pnl
            peak = max(peak, cumulative)
            max_dd = max(max_dd, peak - cumulative)
        return max_dd
