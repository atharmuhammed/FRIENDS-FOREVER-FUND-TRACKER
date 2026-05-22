import os
import json
import gspread
import pandas as pd
from flask import Flask, render_template_string
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

    # Open the 'Data' tab in your sheet
    sheet = client.open('FFE FUND').worksheet('Data')
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    # Calculations
    # 1. Total Collected (Collection + Kuri)
    total_collected = df[df['TYPE'].str.lower().isin(['collection', 'kuri'])]['AMOUNT'].sum()
    
    # 2. Total Given to Charity
    total_given = df[df['TYPE'].str.lower() == 'fund given']['AMOUNT'].sum()
    
    # 3. Balance
    balance = total_collected - total_given
    
    # 4. Current Month Collection
    df['DATE'] = pd.to_datetime(df['DATE'], format='%d-%m-%Y')
    current_month = datetime.now().month
    monthly_collection = df[(df['DATE'].dt.month == current_month) & 
                           (df['TYPE'].str.lower().isin(['collection', 'kuri']))]['AMOUNT'].sum()

    # Dashboard HTML
    html_template = '''
    <h1>FFE Fund Dashboard</h1>
    <div style="font-size: 20px;">
        <p><b>Total Collected:</b> {{ total_collected }}</p>
        <p><b>This Month's Collection:</b> {{ monthly_collection }}</p>
        <p><b>Total Given to Charity:</b> {{ total_given }}</p>
        <p><b>Current Balance:</b> {{ balance }}</p>
    </div>
    <hr>
    <h3>Recent Transactions</h3>
    <pre>{{ data }}</pre>
    '''
    
    return render_template_string(html_template, 
                                  total_collected=total_collected, 
                                  monthly_collection=monthly_collection, 
                                  total_given=total_given, 
                                  balance=balance,
                                  data=data)

if __name__ == '__main__':
    app.run()
