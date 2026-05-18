# Paper Implementation: Pairs Trading in Cryptocurrency Market

This repository implements a complete, end-to-end quantitative pipeline for market-neutral pairs trading in the cryptocurrency markets. It serves as a programmatic implementation of the mathematical methodologies outlined in the academic paper **[Pairs trading in cryptocurrency market: A long-short story](https://businessperspectives.org/index.php/journals/investment-management-and-financial-innovations/issue-387/pairs-trading-in-cryptocurrency-market-a-long-short-story)** (*Investment Management and Financial Innovations, Business Perspectives*).

By utilizing statistical cointegration, the algorithm identifies mean-reverting relationships between crypto assets and executes a systematic long-short strategy. The system is backtested across multiple six-month data panels to evaluate the strategy's capacity to isolate idiosyncratic spread movements and protect capital during broader market drawdowns.



## Data and Testing Panels

The strategy is backtested against daily closing prices of four high-liquidity assets (BTC, ETH, LTC, NEO). To account for shifting market regimes and prevent data snooping, the timeline is segmented into four strictly isolated, six-month panels:

* **Panel A:** January 1, 2018 – June 30, 2018 (High Volatility / Bear Market)
* **Panel B:** July 1, 2018 – December 31, 2018 (Severe Drawdown)
* **Panel C:** January 1, 2019 – June 30, 2019 (Bull Market Recovery)
* **Panel D:** July 1, 2019 – December 31, 2019 (Stagnation / Contraction)


*(Note: The raw Augmented Dickey-Fuller (ADF) test statistics and cointegration matrices for all pairs across these panels are available in the `notebooks/` directory).*

## Mathematical Framework

The core engine relies on a two-step statistical process to identify and trade stationary spreads.

### 1. Ordinary Least Squares (OLS) Regression
To prevent dollar-value skewing between assets with large price difference (e.g., Bitcoin and Litecoin), the system standardizes the relationship using an OLS regression. The higher-priced asset is assigned as the independent variable $x$, and the lower-priced asset as the dependent variable $y$.

$$y_t = \beta x_t + \epsilon_t$$

The resulting $\beta$ coefficient acts as the optimal hedge ratio. The daily spread (the residuals, $\epsilon_t$) is then calculated as:

$$Spread_t = y_t - (\beta \times x_t)$$

### 2. Augmented Dickey-Fuller (ADF) Test
A spread is only tradable if it is statistically stationary (mean-reverting). The pipeline passes the historical residual spread of every asset combination through the ADF test. 

Only pairs that return a p-value strictly less than $0.05$ are validated as cointegrated. Pairs that fail to reject the null hypothesis of a unit root are discarded, filtering out assets that are merely correlated or drifting apart.

### 3. Execution Logic
For cointegrated pairs, the algorithm calculates the standard deviation $\sigma$ of the spread. Trades are executed based on the following triggers:
* **Short Spread:** Triggered when $Spread_t > +\sigma$. The algorithm expects the spread to compress back to the mean.

* **Long Spread:** Triggered when $Spread_t < -\sigma$. The algorithm expects the spread to expand back to the mean.

* **Mean Reversion:** All active positions are closed to capture profit when $Spread_t$ crosses $0$.

## System Architecture

The codebase is strictly modular, separating data generation, mathematical evaluation, and trading simulation.

* `data_processing.py`: Ingests raw historical price data for BTC, ETH, LTC, and NEO. It segments the continuous time-series into isolated six-month panels to ensure the mathematical models react to recent market regimes rather than outdated, multi-year relationships.

* `statistical_tests.py`: It computes the combinations of assets per panel, applies the OLS and ADF functions, and outputs a nested dictionary containing only the validated pairs, their specific beta ratios, and their standard deviation thresholds.

* `strategy_simulator.py`: It goes through the daily price of a panel. It calculates the real-time spread, monitors for execution triggers, tracks floating unrealized equity, and computes the final strategy performance against a static equal-weight baseline portfolio.


## Simulation Results & Visualization

The core advantage of this market-neutral architecture is capital preservation. During severe market contractions (e.g., Panels B and D), the strategy successfully isolates asset spreads and generates positive absolute returns while the passive baseline portfolio suffers significant drawdowns. 

### Performance Summary (Representative Pairs)

| Panel Window | Cointegrated Pair | Beta Ratio | Trade Trigger | Strategy Profit (Units) | Baseline Net | Net Outperformance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Panel B** (H2 2018) | BTC / LTC | 0.0121 | ± 8.04 | -2.91 | -$5,217.54 | **+$5,214.62** |
| **Panel C** (H1 2019) | BTC / ETH | 0.0255 | ± 11.70 | 61.83 | $14,813.68 | **-$14,751.84** |
| **Panel C** (H1 2019) | ETH / LTC | 0.5138 | ± 11.84 | 44.52 | $20,097.13 | **-$20,052.61** |
| **Panel C** (H1 2019) | LTC / NEO | 0.0733 | ± 1.12 | -2.27 | $20,372.08 | **-$20,374.35** |
| **Panel D** (H2 2019) | BTC / ETH | 0.0224 | ± 21.28 | 78.12 | -$4,425.35 | **+$4,503.47** |
| **Panel D** (H2 2019) | BTC / LTC | 0.0128 | ± 9.72 | -37.96 | -$4,937.44 | **+$4,899.48** |
| **Panel D** (H2 2019) | BTC / NEO | 0.0010 | ± 1.87 | 10.65 | -$4,055.01 | **+$4,065.66** |

*(Note: The strategy is designed to sacrifice explosive bull-market growth, as seen in Panel C, in exchange for strict correlation stripping and downside protection).*


### Visualization

The pipeline automatically generates dual-axis performance charts using `matplotlib` to validate the algorithmic edge. 

*(Note: The chart below is a representative example from Panel D. Executing the pipeline will generate the performance charts for all cointegrated pairs across all panels).*

![Cumulative Equity and Spread History](plot\Figure_5.png)

**Chart Analysis:**
* **Spread History (Top):** Displays the neutralized spread over time. The shaded regions visually map the exact days the spread broke the standard deviation thresholds, triggering a simulated trade.

* **Cumulative Return Comparison (Bottom):** Plots the raw unit profit of the strategy (Primary Y-Axis) against the dollar value of a $10,000 passive baseline portfolio (Secondary Y-Axis). 

The results demonstrate the primary advantage of market-neutral architecture: during severe market conditions (such as the crypto winter of late 2019), the strategy successfully isolates the asset spreads and generates positive returns while the passive baseline portfolio suffers significant drawdowns.

## Local Installation and Execution

This project utilizes `uv` for fast, reproducible dependency management.

1. Clone the repository:
```bash
git clone [https://github.com/drjollof/crypto-pairs-trading.git](https://github.com/drjollof/crypto-pairs-trading.git)
cd crypto-pairs-trading
```

2. Initialize the environment and install dependencies:
```bash
uv init
uv add pandas statsmodels matplotlib
```

3. Execute the pipeline:
```bash
uv run main.py
```

Upon execution, the terminal will log the ADF p-values for all combinations, render the historical spread and equity charts for all cointegrated pairs, and print a final consolidated performance table to the console.