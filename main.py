import pandas as pd
from src.data_processing import run_data_pipeline
import src.statistical_tests as stat_tests
import src.strategy_simulator as simulator


pd.set_option('display.max_rows', None)    
pd.set_option('display.max_columns', None)  
pd.set_option('display.width', 1000)

if __name__ == "__main__":
    
    
    panel_dataframes = run_data_pipeline()
    
    previous_formation_rules = None
    
    all_simulation_results = [] 

    for panel_name, panel_df in panel_dataframes.items():
        print(f"\n--- Processing {panel_name} ---")
        
        
        if previous_formation_rules is not None:
            print(f"Simulating trades in {panel_name} using rules from the previous formation period...")
            
            
            simulation_summary = simulator.run_backtest(
                current_panel_df=panel_df, 
                panel_name=panel_name, 
                trading_rules=previous_formation_rules
            )
            
            all_simulation_results.append(simulation_summary)
            
        else:
            print(f"Skipping trading for {panel_name}. No prior formation data available.")

        print(f"Calculating statistical cointegration rules on {panel_name} to use in the NEXT period...")
        
        current_formation_rules = stat_tests.get_cointegrated_pairs(panel_df)
        previous_formation_rules = current_formation_rules


    print("\n--- Backtest Complete ---")
    
    
    if all_simulation_results:
        
        final_results_df = pd.concat(all_simulation_results, ignore_index=True)

        print("\nFinal Out-of-Sample Performance Summary:")
        print(final_results_df)
    else:
        print("\nNo trades were executed during the simulation.")