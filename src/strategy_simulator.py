import pandas as pd
import matplotlib.pyplot as plt

def calculate_series_spread(panel_df, independent_x: str, dependent_y : str, beta_hedge_ratio: float) -> pd.DataFrame:
    """
    Calculates the out-of-sample residual spread using a historical hedge ratio.
    
    Args:
        panel_df (pd.DataFrame): The unseen price data for the current trading panel.
        independent_x (str): The ticker symbol for the independent asset.
        dependent_y (str): The ticker symbol for the dependent asset.
        beta_hedge_ratio (float): The static hedge ratio locked in from the prior period.
        
    Returns:
        pd.DataFrame: The panel dataframe appended with a new 'spread' column.
    """

    spread = panel_df[dependent_y] - (panel_df[independent_x] * beta_hedge_ratio) 
    panel_df['spread'] = spread
    return panel_df



def simulate_trading_floor(panel_df, std_dev_trigger: float) -> tuple:
    """
    Simulates market-neutral trade execution based on standard deviation thresholds.
    
    Iterates through the daily spread. Opens a short position if the spread exceeds 
    the positive threshold, and a long position if it falls below the negative threshold. 
    Closes active positions when the spread crosses the zero mean.
    
    Args:
        panel_df (pd.DataFrame): The trading panel containing the calculated spread.
        std_dev_trigger (float): The static standard deviation locked in from the prior period.
        
    Returns:
        tuple: A tuple containing the cumulative unit profit (float) and the 
        updated dataframe tracking daily equity changes.
    """

    in_position = False
    position_type = None
    entry_spread = 0.0
    cumulative_profit = 0.0
    
    daily_equity = []
    final_date = panel_df.index[-1]

    for date, row in panel_df.iterrows():
        current_spread = row['spread']
        
        floating_profit = 0.0
        if in_position:
            if position_type == 'short_spread':
                floating_profit = entry_spread - current_spread
            elif position_type == 'long_spread':
                floating_profit = current_spread - entry_spread
                
        daily_equity.append(cumulative_profit + floating_profit)

        if not in_position:
            if current_spread > std_dev_trigger:
                in_position = True
                position_type = 'short_spread'
                entry_spread = current_spread
                
            elif current_spread < -std_dev_trigger:
                in_position = True
                position_type = 'long_spread'
                entry_spread = current_spread

        elif in_position:
            close_position = False
            
            if position_type == 'short_spread' and current_spread <= 0:
                trade_profit = entry_spread - current_spread
                close_position = True
                
            elif position_type == 'long_spread' and current_spread >= 0:
                trade_profit = current_spread - entry_spread
                close_position = True
                
            elif date == final_date:
                if position_type == 'short_spread':
                    trade_profit = entry_spread - current_spread
                else:
                    trade_profit = current_spread - entry_spread
                close_position = True

            if close_position:
                cumulative_profit += trade_profit
                in_position = False
                position_type = None
                entry_spread = 0.0

    panel_df['strategy_profit'] = daily_equity
    return cumulative_profit, panel_df



def calculate_baseline_portfolio(panel_df: pd.DataFrame, independent_x: str, dependent_y: str, initial_capital=10000) -> tuple:

    """
    Calculates the dollar performance of a passive buy-and-hold benchmark portfolio.
    
    Splits the initial capital equally between the two assets on the first day of 
    the trading panel and tracks the daily mark-to-market value.
    
    Args:
        panel_df (pd.DataFrame): The trading panel dataframe.
        independent_x (str): The ticker symbol for the first asset.
        dependent_y (str): The ticker symbol for the second asset.
        initial_capital (int): The starting balance for the benchmark.
        
    Returns:
        tuple: A tuple containing the final net profit (float) and the updated 
        dataframe tracking the daily baseline value.
    """

    start_price_x = panel_df[independent_x].iloc[0]
    start_price_y = panel_df[dependent_y].iloc[0]
    
    shares_x = (initial_capital / 2) / start_price_x
    shares_y = (initial_capital / 2) / start_price_y
    
    daily_baseline_profit = []
    
    for date, row in panel_df.iterrows():
        current_value = (shares_x * row[independent_x]) + (shares_y * row[dependent_y])
        daily_baseline_profit.append(current_value - initial_capital) 

    panel_df['baseline_profit'] = daily_baseline_profit
    passive_profit = daily_baseline_profit[-1]
    
    return passive_profit, panel_df


def plot_pair_results(panel_df: pd.DataFrame, panel_name: str, pair_name: str, std_dev: float):
    """
    Generates dual-axis charts for visual backtest validation.
    
    Plots the out-of-sample residual spread with historical execution thresholds 
    on the top axis, and compares cumulative strategy unit profit against the 
    baseline dollar portfolio on the bottom axis.
    
    Args:
        panel_df (pd.DataFrame): The trading panel containing all equity and spread histories.
        panel_name (str): The identifier for the current simulation window.
        pair_name (str): The formatted string of the traded asset pair.
        std_dev (float): The historical standard deviation used as the threshold.
    """


    plt.style.use('default') 
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), facecolor='#ffffff')
    
    ax1.plot(panel_df.index, panel_df['spread'], color='#1f77b4', linewidth=1.5, label='Daily Spread')
    
    ax1.axhline(0, color='#333333', linestyle='--', alpha=0.7, label='Mean (0)')
    ax1.axhline(std_dev, color='#d62728', linestyle='--', alpha=0.6, label='+1 Std Dev')
    ax1.axhline(-std_dev, color='#2ca02c', linestyle='--', alpha=0.6, label='-1 Std Dev')
    
    ax1.fill_between(panel_df.index, panel_df['spread'], std_dev, 
                     where=(panel_df['spread'] > std_dev), color='#d62728', alpha=0.1)
    ax1.fill_between(panel_df.index, panel_df['spread'], -std_dev, 
                     where=(panel_df['spread'] < -std_dev), color='#2ca02c', alpha=0.1)
    
    ax1.set_title(f'{panel_name.upper()} - {pair_name} Spread Analysis', fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylabel('Spread (Raw Units)', fontsize=11)
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc')
    
    color_strat = '#673ab7' 
    color_base = '#ff9800'  
    
    ax2.plot(panel_df.index, panel_df['strategy_profit'], color=color_strat, linewidth=2.5, label='Strategy Profit')
    ax2.set_ylabel('Strategy Profit (Units)', color=color_strat, fontsize=11, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=color_strat)
    ax2.grid(True, linestyle=':', alpha=0.6)
    
    ax2.fill_between(panel_df.index, panel_df['strategy_profit'], 0, color=color_strat, alpha=0.05)
    
    ax3 = ax2.twinx()
    ax3.plot(panel_df.index, panel_df['baseline_profit'], color=color_base, linewidth=1.5, alpha=0.8, label='Baseline Portfolio')
    ax3.set_ylabel('Baseline Value ($)', color=color_base, fontsize=11, fontweight='bold')
    ax3.tick_params(axis='y', labelcolor=color_base)
    
    ax3.grid(False) 
    
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    lines_3, labels_3 = ax3.get_legend_handles_labels()
    ax2.legend(lines_2 + lines_3, labels_2 + labels_3, loc='upper left', frameon=True, facecolor='white', edgecolor='#cccccc')
    
    ax2.set_title('Strategy Vs Baseline Performance', fontsize=14, fontweight='bold', pad=15)
    
    plt.tight_layout()
    plt.show()

def run_backtest(current_panel_df: pd.DataFrame, panel_name: str, trading_rules: dict) -> pd.DataFrame:
    """
    run the out-of-sample forward-walk simulation for a given trading panel.
    
    Receives the trained statistical rules from the previous six-month formation 
    period and applies them to the current panel. Computes the spread, 
    simulates trades, benchmarks performance, and outputs the final metrics.
    
    Args:
        current_panel_df (pd.DataFrame): The unseen price data for the trading period.
        panel_name (str): The string identifier of the current panel.
        trading_rules (dict): A nested dictionary containing the validated pairs, 
        historical hedge ratios, and standard deviation triggers from the formation period.
        
    Returns:
        pd.DataFrame: A summary dataframe containing the performance metrics for 
        all executed pairs during the panel.
    """

    simulation_results = []

    for pair_tuple, rules in trading_rules.items():
        panel_df = current_panel_df.copy() 
        x = rules['independent_x']
        y = rules['dependent_y']
        beta = rules['beta_hedge_ratio']
        std = rules['std_dev']

        spread_panel_df = calculate_series_spread(panel_df, x, y, beta)
        
        cumulative_profit, spread_panel_df = simulate_trading_floor(spread_panel_df, std)
        passive_profit, spread_panel_df = calculate_baseline_portfolio(spread_panel_df, x, y)
        
        pair_string = f"{x.split('/')[0]} / {y.split('/')[0]}"
        
        result_data = {
            'Panel': panel_name.upper(),
            'Pair (X/Y)': pair_string,
            'Beta Ratio': round(beta, 4),
            'Std Dev Trigger': round(std, 2),
            'Strategy Profit': round(cumulative_profit, 2),
            'Baseline PnL': round(passive_profit, 2),
            
        }
        
        simulation_results.append(result_data)
        
        plot_pair_results(spread_panel_df, panel_name, pair_string, std)
    
    if not simulation_results:
        return pd.DataFrame()
        
    results_df = pd.DataFrame(simulation_results)
    return results_df