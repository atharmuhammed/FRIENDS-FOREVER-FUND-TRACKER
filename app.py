import os
import json
import gspread
import pandas as pd
from flask import Flask, render_template_string, url_for
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    # Load credentials from environment variable
    json_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    creds_dict = json.loads(json_creds)

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Connect to the 'Data' tab
    sheet = client.open('FFE FUND').worksheet('Data')
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # --- CALCULATIONS ---
    df['AMOUNT'] = pd.to_numeric(df['AMOUNT'], errors='coerce').fillna(0)
    
    total_collected = df[df['TYPE'].str.lower().isin(['collection', 'kuri'])]['AMOUNT'].sum()
    total_given = df[df['TYPE'].str.lower() == 'fund given']['AMOUNT'].sum()
    balance = total_collected - total_given
    
    df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%m-%Y', errors='coerce')
    current_month = datetime.now().month
    monthly_collection = df[(df['DATE'].dt.month == current_month) & 
                           (df['TYPE'].str.lower().isin(['collection', 'kuri']))]['AMOUNT'].sum()

    # --- UPDATED DASHBOARD HTML WITH BOXES ---
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { margin: 0; padding: 0; font-family: sans-serif; background-color: #f4f7f6; }
            .header-container { width: 100%; display: block; text-align: center; background: white; }
            .header-logo { width: 100%; height: auto; display: block; }
            .dashboard-container { padding: 20px; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 25px; }
            .dashboard-box { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
            .dashboard-box h4 { margin: 0 0 8px 0; color: #7f8c8d; font-size: 0.8em; text-transform: uppercase; }
            .dashboard-box p { margin: 0; font-size: 1.2em; font-weight: bold; color: #2c3e50; }
            .balance-box { border-bottom: 4px solid #27ae60; }
            table { width: 100%; border-collapse: collapse; background: white; margin-top: 10px; }
            th, td { padding: 10px; border: 1px solid #ddd; text-align: left; font-size: 0.9em; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <div class="header-container">
            <img src="{{ url_for('static', filename='Ffe.png') }}" class="header-logo" alt="FFE Fund Logo">
        </div>

        <div class="dashboard-container">
            <h2 style="color: #2c3e50;">Overview</h2>
            
            <div class="stats-grid">
                <div class="dashboard-box"><h4>Total Collected</h4><p>{{ total_collected }}</p></div>
                <div class="dashboard-box"><h4>Monthly</h4><p>{{ monthly_collection }}</p></div>
                <div class="dashboard-box"><h4>Total Given</h4><p>{{ total_given }}</p></div>
                <div class="dashboard-box balance-box"><h4>Balance</h4><p style="color: #27ae60;">{{ balance }}</p></div>
            </div>

            <h3>Recent Transactions</h3>
            <table>
                <tr><th>Date</th><th>Name</th><th>Amount</th><th>Type</th><th>Reason</th></tr>
                {% for row in data %}
                <tr>
                    <td>{{ row['DATE'] }}</td>
                    <td>{{ row['NAMES'] }}</td>
                    <td>{{ row['AMOUNT'] }}</td>
                    <td>{{ row['TYPE'] }}</td>
                    <td>{{ row['REASON'] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(html_template, 
                                  total_collected=total_collected, 
                                  monthly_collection=monthly_collection, 
                                  total_given=total_given, 
                                  balance=balance,
                                  data=data)

if __name__ == '__main__':
    app.run()
