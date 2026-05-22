import os
import json
import gspread
import pandas as pd
from flask import Flask, render_template_string, request, url_for
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# Helper to get the Gspread client
def get_gspread_client():
    json_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    creds_dict = json.loads(json_creds)
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

@app.route('/', methods=['GET', 'POST'])
def home():
    client = get_gspread_client()
    
    # 1. Fetch Transactions for Dashboard
    sheet = client.open('FFE FUND').worksheet('Data')
    data = sheet.get_all_records()
    
    display_data = []
    for row in data:
        new_row = row.copy()
        if str(row.get('TYPE', '')).strip().lower() == 'collection':
            new_row['AMOUNT'] = "<b>PAID</b>"
        display_data.append(new_row)

    df = pd.DataFrame(data)
    df['AMOUNT'] = pd.to_numeric(df['AMOUNT'], errors='coerce').fillna(0)
    total_collected = df[df['TYPE'].str.lower().str.strip().isin(['collection', 'kuri'])]['AMOUNT'].sum()
    total_given = df[df['TYPE'].str.lower().str.strip() == 'fund given']['AMOUNT'].sum()
    balance = total_collected - total_given
    
    # 2. Fetch Member Dropdown Data
    member_sheet = client.open('FFE FUND').worksheet('Member_Data')
    member_df = pd.DataFrame(member_sheet.get_all_records())
    member_names = member_df['NAME'].dropna().unique().tolist()

    selected_member = request.form.get('member_name')
    member_details = None
    if selected_member:
        filtered = member_df[member_df['NAME'] == selected_member]
        if not filtered.empty:
            member_details = filtered.iloc[0].to_dict()

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
            .card { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            table { width: 100%; border-collapse: collapse; background: white; margin-top: 10px; }
            th, td { padding: 10px; border: 1px solid #ddd; text-align: left; font-size: 0.9em; }
            th { background-color: #f2f2f2; }
            select { padding: 10px; width: 100%; border-radius: 5px; }
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
                <div class="dashboard-box"><h4>Total Given</h4><p>{{ total_given }}</p></div>
                <div class="dashboard-box balance-box"><h4>Balance</h4><p style="color: #27ae60;">{{ balance }}</p></div>
            </div>

            <div class="card">
                <h3>Member Search</h3>
                <form method="POST">
                    <select name="member_name" onchange="this.form.submit()">
                        <option value="">-- Select Member --</option>
                        {% for name in member_names %}
                        <option value="{{ name }}" {% if name == selected_member %}selected{% endif %}>{{ name }}</option>
                        {% endfor %}
                    </select>
                </form>
            </div>

            {% if member_details %}
            <div class="card">
                <h3>Status for: {{ selected_member }}</h3>
                <table>
                    {% for month, status in member_details.items() if month != 'NAME' %}
                    <tr>
                        <th>{{ month }}</th>
                        <td style="{{ 'color: red; font-weight: bold;' if 'NOT' in (status|string).upper() else '' }}">{{ status }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
            {% endif %}

            <h3>Recent Transactions</h3>
            <table>
                <tr><th>Date</th><th>Name</th><th>Amount</th><th>Type</th><th>Reason</th></tr>
                {% for row in display_data %}
                <tr>
                    <td>{{ row['DATE'] }}</td>
                    <td>{{ row['NAMES'] }}</td>
                    <td>{{ row['AMOUNT'] | safe }}</td>
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
                                  total_given=total_given, 
                                  balance=balance,
                                  display_data=display_data,
                                  member_names=member_names,
                                  selected_member=selected_member,
                                  member_details=member_details)

if __name__ == '__main__':
    app.run()
