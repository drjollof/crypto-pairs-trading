import os
import ccxt
import pandas as pd


start_date = '2018-01-01T00:00:00Z'
end_date = '2019-12-31T00:00:00Z'
symbols = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'NEO/USDT']
timeframe = '1d'
DATA_PATH = 'data/'


def load_full_csv() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH + 'close_price_data.csv', index_col= 0)

    return df


def fetch_raw_data(start_date, end_date, symbols, timeframe):

    try: 

        exchange = ccxt.binance()
        start_ts = exchange.parse8601(start_date)
        end_ts = exchange.parse8601(end_date)
        close_dict = {}

        for symbol in symbols:
            all_data = exchange.fetch_ohlcv(symbol, timeframe, since=start_ts, limit=1000)
            temp_close_dict = {c[0]: c[4] for c in all_data if c[0] <= end_ts}
            close_dict[symbol] = temp_close_dict
        
        df = pd.DataFrame(close_dict)
        df.index = pd.to_datetime(df.index, unit='ms')
        df.index.name = 'date'
        df.to_csv(DATA_PATH + 'close_price_data.csv', index=True)
        print(f'{len(df)} close price data successfully fetched for all coins..')


    except Exception as err:
        print(f"Could not fetch data from API: {err}")
    
    


def split_into_panels(df: pd.DataFrame):
    date_ranges = {
        'panel_a': ('2018-01-01', '2018-06-30'),
        'panel_b': ('2018-07-01', '2018-12-31'),
        'panel_c': ('2019-01-01', '2019-06-30'),
        'panel_d': ('2019-07-01', '2019-12-31')
    }

    for panel_name, (start_date, end_date) in date_ranges.items():
        panel_df = df.loc[start_date:end_date]
        
        file_path = f"{DATA_PATH}{panel_name}.csv"
        panel_df.to_csv(file_path)
        print(f"Saved {panel_name} with {len(panel_df)} rows.")



def read_panel_data() -> dict:
    panels = {}
    panel_names = ['panel_a', 'panel_b', 'panel_c', 'panel_d']
    
    for name in panel_names:
        file_path = f"{DATA_PATH}{name}.csv"
        panels[name] = pd.read_csv(file_path, index_col=0, parse_dates=True)
        
    return panels



def run_data_pipeline():
    raw_csv_path = DATA_PATH + 'close_price_data.csv'
    panel_a_path = DATA_PATH + 'rupanel_a.csv' 

    if not os.path.exists(raw_csv_path):
        print("Fetching data from API...")
        fetch_raw_data(start_date, end_date, symbols,timeframe) 
        
    if not os.path.exists(panel_a_path):
        print("Splitting master CSV into panels...")
        df = load_full_csv()
        split_into_panels(df)

    panels = read_panel_data()
    
    return panels