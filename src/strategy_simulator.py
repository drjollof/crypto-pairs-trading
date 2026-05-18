import pandas as pd
import matplotlib.pyplot as plt

def calculate_series_spread(panel_df, independent_x, dependent_y, beta_hedge_ratio):
    spread = panel_df[dependent_y] - (panel_df[independent_x] * beta_hedge_ratio) 
    panel_df['spread'] = spread
    return panel_df

def simulate_trading_floor(panel_df, std_dev_trigger):
    in_position = False
    position_type = None
    entry_spread = 0.0
    cumulative_profit = 0.0
    
    # track the daily equity curve
    daily_equity = []
    final_date = panel_df.index[-1]

    for date, row in panel_df.iterrows():
        current_spread = row['spread']
        
        # Calculate the unrealized profit for the chart
        floating_profit = 0.0
        if in_position:
            if position_type == 'short_spread':
                floating_profit = entry_spread - current_spread
            elif position_type == 'long_spread':
                floating_profit = current_spread - entry_spread
                
        daily_equity.append(cumulative_profit + floating_profit)

        # opening a position
        if not in_position:
            if current_spread > std_dev_trigger:
                in_position = True
                position_type = 'short_spread'
                entry_spread = current_spread
                
            elif current_spread < -std_dev_trigger:
                in_position = True
                position_type = 'long_spread'
                entry_spread = current_spread

        # closing an active position
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

def calculate_baseline_portfolio(panel_df, independent_x, dependent_y, initial_capital=10000):
    start_price_x = panel_df[independent_x].iloc[0]
    start_price_y = panel_df[dependent_y].iloc[0]
    
    shares_x = (initial_capital / 2) / start_price_x
    shares_y = (initial_capital / 2) / start_price_y
    
    # track the passive baseline curve
    daily_baseline_profit = []
    
    for date, row in panel_df.iterrows():
        current_value = (shares_x * row[independent_x]) + (shares_y * row[dependent_y])
        daily_baseline_profit.append(current_value - initial_capital) 

    # Save the history to the dataframe and grab the final day's value
    panel_df['baseline_profit'] = daily_baseline_profit
    passive_profit = daily_baseline_profit[-1]
    
    return passive_profit, panel_df


def plot_pair_results(panel_df, panel_name, pair_name, std_dev):
    
    plt.style.use('default') 
    
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), facecolor='#ffffff')
    
    # Plot the main spread 
    ax1.plot(panel_df.index, panel_df['spread'], color='#1f77b4', linewidth=1.5, label='Daily Spread')
    
    # Add the threshold
    ax1.axhline(0, color='#333333', linestyle='--', alpha=0.7, label='Mean (0)')
    ax1.axhline(std_dev, color='#d62728', linestyle='--', alpha=0.6, label='+1 Std Dev')
    ax1.axhline(-std_dev, color='#2ca02c', linestyle='--', alpha=0.6, label='-1 Std Dev')
    
    # Add background shading to highlight the exact days the algorithm triggers a trade
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
    
    ax2.set_title('Cumulative Return Comparison', fontsize=14, fontweight='bold', pad=15)
    
    
    plt.tight_layout()
    plt.show()

def run_trading_simulation(panels, trading_rules):
    simulation_results = []

    for key, value in trading_rules.items():
        for k, v in value.items():
            panel_df = panels[key].copy() 
            x = v['independent_x']
            y = v['dependent_y']
            beta = v['beta_hedge_ratio']
            std = v['std_dev']

            spread_panel_df = calculate_series_spread(panel_df, x, y, beta)
            
        
            cumulative_profit, spread_panel_df = simulate_trading_floor(spread_panel_df, std)
            passive_profit, spread_panel_df = calculate_baseline_portfolio(spread_panel_df, x, y)
            
            pair_string = f"{x.split('/')[0]} / {y.split('/')[0]}"
            
            result_data = {
                'Panel': key.upper(),
                'Pair (X/Y)': pair_string,
                'Beta Ratio': round(beta, 4),
                'Std Dev Trigger': round(std, 2),
                'Strategy Profit': round(cumulative_profit, 2),
                'Baseline Profit': round(passive_profit, 2),
                'Net Outperformance': round(cumulative_profit - passive_profit, 2)
            }
            
            simulation_results.append(result_data)
            
            plot_pair_results(spread_panel_df, key, pair_string, std)
            
    results_df = pd.DataFrame(simulation_results)
    return results_df