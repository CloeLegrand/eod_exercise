WIDTH = 95  # 95 était écrit dans print_report

class EodReport:
    """Construit le texte du rapport de fin de journée."""

    def __init__(self, portfolio, prices, fx, risk):
        """Reçoit les objets dont le rapport a besoin pour se remplir."""
        self.portfolio = portfolio
        self.prices = prices
        self.fx = fx
        self.risk = risk

    def render(self) -> str:
        """Construit le rapport complet et le retourne sous forme de texte.
        Rien n'est affiché ici : c'est à l'appelant de faire print().
        """
        lines = []
        lines.append("=" * WIDTH)
        lines.append(f"EOD REPORT - as of {self.prices.as_of():%Y-%m-%d}")
        lines.append("=" * WIDTH)
        lines.append(
            f"{'Ticker':<10}{'Qty':>10}{'Avg px':>10}{'Last px':>10}"
            f"{'Exposure (EUR)':>19}{'Unreal. (EUR)':>18}{'Real. (EUR)':>18}"
        )

        total_exposure = total_unrealized = total_realized = 0.0
        for ticker, pos in self.portfolio.positions.items():
            ccy = pos.instrument.ccy
            last = self.prices.last_price(ticker)
            exposure = self.fx.to_eur(pos.exposure(last), ccy)
            unrealized = self.fx.to_eur(pos.unrealized_pnl(last), ccy)
            realized = self.fx.to_eur(pos.realized_pnl, ccy)

            total_exposure += exposure
            total_unrealized += unrealized
            total_realized += realized
            lines.append(
                f"{ticker:<10}{pos.qty:>10,.0f}{pos.avg_price:>10.2f}{last:>10.2f}"
                f"{exposure:>19,.2f}{unrealized:>18,.2f}{realized:>18,.2f}"
            )

        lines.append("-" * WIDTH)
        lines.append(
            f"{'TOTAL':<40}{total_exposure:>19,.2f}"
            f"{total_unrealized:>18,.2f}{total_realized:>18,.2f}"
        )
        lines.append("")
        lines.append(f"{'Ticker':<10}{'Ann. vol':>12}{'Max DD':>12}")
        for ticker in self.portfolio.positions:
            vol = self.risk.compute_volatility(ticker)
            max_dd = self.risk.compute_max_drawdown(ticker)
            lines.append(f"{ticker:<10}{vol:>12.2%}{max_dd:>12.2%}")

        daily_pnl = self.risk.compute_portfolio_daily_pnl()
        lines.append("")
        lines.append(f"Portfolio annualised PnL vol (EUR): {self.risk.pnl_volatility(daily_pnl):,.2f}")
        lines.append(f"Portfolio PnL max drawdown (EUR):   {self.risk.pnl_max_drawdown(daily_pnl):,.2f}")
        return "\n".join(lines)
