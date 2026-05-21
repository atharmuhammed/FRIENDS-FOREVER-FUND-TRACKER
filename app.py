import os
import json
import gspread
from flask import Flask, render_template_string
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

@app.route('/')
def home():
    # This uses the secret key we will put on Render
    json_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    creds_dict = json.loads(json_creds)

    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Make sure this name matches your actual Google Sheet name
    sheet = client.open('FRIENDS-FOREVER-COLLECTION').sheet1
    data = sheet.get_all_records()

    return render_template_string('<h1>Fund Tracker</h1><pre>{{ data }}</pre>', data=data)

if __name__ == '__main__':
    app.run()
