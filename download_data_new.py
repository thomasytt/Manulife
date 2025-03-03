import pandas as pd
import os
import yfinance as yf

# URL of the CSV data
url = "https://raw.githubusercontent.com/thomasytt/Manulife/main/csv%20data%20for%20DS.csv"

# Directory to save the CSV files
save_directory_manulife = "data/"
save_directory_etfs = "data/etfs"

# Create the directory if it doesn't exist
if not os.path.exists(save_directory_manulife):
    os.makedirs(save_directory_manulife)

# Load the CSV data into a pandas DataFrame
df = pd.read_csv(url)

# Convert the date column to datetime format
df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

# Save the daily data to a CSV file
daily_file_path = os.path.join(save_directory_manulife, 'manulife_data_daily.csv')
df.to_csv(daily_file_path, index=False, date_format='%Y-%m-%d')

# Resample the data to weekly, using the last available data of each week (Friday)
df.set_index('Date', inplace=True)
weekly_df = df.resample('W-FRI').last().reset_index()

# Save the weekly data to a CSV file
weekly_file_path = os.path.join(save_directory_manulife, 'manulife_data_weekly.csv')
weekly_df.to_csv(weekly_file_path, index=False, date_format='%Y-%m-%d')

# List of ETF tickers
etf_tickers = ['EWH', 'SPY', 'EPP', 'EZU', 'EWJ', 'MCHI', 'XLV', 'VIX']

# Function to download and save ETF data
def save_etf_data(ticker):
    etf = yf.Ticker(ticker)
    etf_df = etf.history(period="max")
    etf_df.reset_index(inplace=True)
    etf_df['Date'] = pd.to_datetime(etf_df['Date'], format='%Y-%m-%d')
    
    # Save daily data
    daily_file_path = os.path.join(save_directory_etfs, f'{ticker}_daily.csv')
    etf_df.to_csv(daily_file_path, index=False, date_format='%Y-%m-%d')
    
    # Resample to weekly data
    etf_df.set_index('Date', inplace=True)
    weekly_etf_df = etf_df.resample('W-FRI').last().reset_index()
    
    # Save weekly data
    weekly_file_path = os.path.join(save_directory_etfs, f'{ticker}_weekly.csv')
    weekly_etf_df.to_csv(weekly_file_path, index=False, date_format='%Y-%m-%d')

# Download and save data for each ETF
for ticker in etf_tickers:
    save_etf_data(ticker)

print("Data saved successfully!")
