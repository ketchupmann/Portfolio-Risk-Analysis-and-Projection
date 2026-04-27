import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from eodhd import APIClient

class Asset:
    def __init__(self, ticker):
        self.ticker = ticker.upper()
        self.api_key = os.environ.get("EODHD_API_KEY")

        self.client = APIClient(self.api_key)
    
        self.historical_data = None
        self.mean_return = None
        self.volatility = None
        
   
    def fetch_data(self, years_back, period='d'):
        """
        Fetches historical daily data and isolates the Adjusted Close price.
        """
        end_date_obj = pd.Timestamp.now(tz='US/Eastern')
    
        start_date_obj = end_date_obj - pd.DateOffset(years=years_back)
        end_date = end_date_obj.strftime('%Y-%m-%d')
        start_date = start_date_obj.strftime('%Y-%m-%d')

        try:
            eod_data = self.client.get_eod_historical_stock_market_data(symbol=self.ticker, period=period, from_date=start_date, to_date=end_date)
            df = pd.DataFrame(eod_data)
            
            # only care about the adjusted close for risk modeling
            df = df[['adjusted_close']].copy()
            df.rename(columns={'adjusted_close': 'Close'}, inplace=True)
            
            self.historical_data = df
            self.calculate_metrics()
            
            return self.historical_data
        except Exception as e:
            print(f"Error fetching data for {self.ticker}: {e}")
            return None
    
    def calculate_metrics(self):
        if self.historical_data is not None and not self.historical_data.empty:
            self.historical_data['Returns'] = np.log(self.historical_data['Close'] / self.historical_data['Close'].shift(1))

            self.historical_data.dropna(inplace=True)
            self.mean_return = self.historical_data['Returns'].mean()
            self.volatility = self.historical_data['Returns'].std()

