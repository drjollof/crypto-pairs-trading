import pandas as pd
from itertools import combinations
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller




def calculate_ols_metrics(panel_df, coin1, coin2):
    coin1_mean = panel_df[coin1].mean()
    coin2_mean = panel_df[coin2].mean()

    if coin1_mean > coin2_mean:
         highest = coin1
         lowest = coin2

    else:
        highest = coin2
        lowest = coin1 


    x = panel_df[highest]
    y = panel_df[lowest]

    x = sm.add_constant(x)


    model = sm.OLS(y, x).fit()
    coef = model.params[highest]
    residuals = pd.Series(model.resid)


    return {'y': lowest, 
            'x': highest,
            'beta': coef,
            'residuals': residuals}


def run_statationary_check(residual):

    adf = adfuller(residual)
    p_value = adf[1]

    if p_value < 0.05:
        print(f'The stationary test is passed at p-value: {p_value:.4f}.. the coin pair is cointegrated...')

        return True
    
    else:
        print(f'The stationary test is failed at {p_value:.4f} ... the coin pair is not cointgrated..')
        
        return False






def run_math_pipeline(panels):
     trading_rules = {}
     for key, value in panels.items():
        columns = list(value.columns)
        pairs = list(combinations(columns, 2))

        for pair in pairs:
            coin1 = pair[0]
            coin2 = pair[1]

            ols_result = calculate_ols_metrics(value, coin1, coin2)
            is_stationary = run_statationary_check(ols_result['residuals'])

            if is_stationary:
                standard_deviation = ols_result['residuals'].std()

                data = {
                    'independent_x': ols_result['x'],
                    'dependent_y': ols_result['y'],
                    'beta_hedge_ratio': ols_result['beta'],
                    'std_dev' : standard_deviation
                    }
                            
                trading_rules[pair] = data

                            
            trading_rules[pair][key]
                
     return trading_rules
          
     