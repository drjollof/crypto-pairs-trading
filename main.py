import pandas as pd
from src.data_processing import run_data_pipeline
from src.statistical_tests import run_math_pipeline
from src.strategy_simulator import run_trading_simulation



pd.set_option('display.max_rows', None)    
pd.set_option('display.max_columns', None)  
pd.set_option('display.width', 1000)


if __name__ == "__main__":
    
    panel_dataframes = run_data_pipeline()
    trading_rules = run_math_pipeline(panel_dataframes)
    final_results = run_trading_simulation(panel_dataframes, trading_rules)
    
    print(final_results)