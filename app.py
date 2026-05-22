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
    
    df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%m-%Y')
    current_month = datetime.now().month
    monthly_collection = df[(df['DATE'].dt.month == current_month) & 
                           (df['TYPE'].str.lower().isin(['collection', 'kuri']))]['AMOUNT'].sum()

    # --- UPDATED DASHBOARD HTML ---
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { margin: 0; padding: 0; font-family: sans-serif; }
            .header-container { width: 100%; display: block; }
            .header-logo { width: 100%; height: auto; display: block; }
            .dashboard-container { padding: 20px; }
        </style>
    </head>
    <body>
        <div class="header-container">
            <img src="{{ url_for('static', filename='Ffe.png') }}" class="header-logo" alt="FFE Fund Logo">
        </div>

        <div class="dashboard-container">
            <h1 style="color: #2c3e50;">FFE Fund Dashboard</h1>
            <div style="font-size: 20px;">
                <p><b>Total Collected:</b> {{ total_collected }}</p>
                <p><b>This Month's Collection:</b> {{ monthly_collection }}</p>
                <p><b>Total Given to Charity:</b> {{ total_given }}</p>
                <p style="font-size: 1.2em; color: green;"><b>Current Balance:</b> {{ balance }}</p>
            </div>
            <hr>
            <h3>Recent Transactions</h3>
            <table border="1" style="width:100%; text-align: left;">
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
