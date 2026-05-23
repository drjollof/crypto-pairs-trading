import pandas as pd
from itertools import combinations
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

def calculate_ols_metrics(panel_df: pd.DataFrame, independent_x: str, independent_y: str) -> dict:
    """
    Estimates the optimal hedge ratio between two assets using Ordinary Least Squares.
    
    Evaluates the mean prices of both assets and automatically assigns the 
    higher-priced asset as the independent variable (x) to normalize the 
    dollar-value difference.
    
    Args:
        panel_df (pd.DataFrame): The price data for the historical formation period.
        independent_x (str): The ticker symbol for the first asset.
        independent_y (str): The ticker symbol for the second asset.
        
    Returns:
        dict: A dictionary containing the designated dependent asset ('y'), 
        independent asset ('x'), the calculated beta coefficient ('beta'), 
        and the resulting spread series ('residuals').
    """
    coin1_mean = panel_df[independent_x].mean()
    coin2_mean = panel_df[independent_y].mean()

    if coin1_mean > coin2_mean:
         highest = independent_x
         lowest = independent_y
    else:
        highest = independent_y
        lowest = independent_x 

    x = panel_df[highest]
    y = panel_df[lowest]

    x = sm.add_constant(x)

    model = sm.OLS(y, x).fit()
    coef = model.params[highest]
    residuals = pd.Series(model.resid)

    return {
        'y': lowest, 
        'x': highest,
        'beta': coef,
        'residuals': residuals
    }

def run_stationary_check(residual: pd.Series, pair_name: str) -> bool:
    """
    Validates the mean-reverting property of a spread using the Augmented Dickey-Fuller test.
    
    Evaluates the residual spread against the null hypothesis of a unit root. A 
    resulting p-value strictly below 0.05 indicates statistical cointegration. 
    Prints the formatted test result to the terminal.
    
    Args:
        residual (pd.Series): The residual spread calculated from the OLS regression.
        pair_name (str): The raw string identifier for the asset pair.
        
    Returns:
        bool: True if the spread is stationary (cointegrated), False otherwise.
    """
    adf = adfuller(residual)
    p_value = adf[1]

    pair_name = "/".join([part for part in pair_name.split('/') if part != 'USDT'])

    if p_value < 0.05:
        print(f'    [PASS] {pair_name}: Stationary test passed (p-value: {p_value:.4f}). Cointegrated.')
        return True
    else:
        print(f'    [FAIL] {pair_name}: Stationary test failed (p-value: {p_value:.4f}). Not cointegrated.')
        return False

def get_cointegrated_pairs(panel_df: pd.DataFrame) -> dict:
    """
    Iterates through all possible asset combinations to identify tradable relationships.
    
    Generates pairs from the panel columns, applies OLS regression, and runs ADF 
    stationarity testing on every combination during the formation panel. Discards 
    non-stationary pairs and packages the valid parameters into a dictionary to be 
    passed forward to the out-of-sample trading simulator.
    
    Args:
        panel_df (pd.DataFrame): The price data for the historical formation period.
        
    Returns:
        dict: A nested dictionary mapping cointegrated pairs to their specific 
        independent/dependent variables, historical beta ratios, and standard 
        deviation thresholds.
    """
    trading_rules = {}
    columns = list(panel_df.columns)
    pairs = list(combinations(columns, 2))

    for pair in pairs:
        coin1 = pair[0]
        coin2 = pair[1]
        pair_name = f"{coin1}/{coin2}"
        
        ols_result = calculate_ols_metrics(panel_df, coin1, coin2)
        
        is_stationary = run_stationary_check(ols_result['residuals'], pair_name)
        
        if is_stationary:
            standard_deviation = ols_result['residuals'].std()

            trading_rules[pair] = {
                'independent_x': ols_result['x'],
                'dependent_y': ols_result['y'],
                'beta_hedge_ratio': ols_result['beta'],
                'std_dev' : standard_deviation
            }
            
    return trading_rules