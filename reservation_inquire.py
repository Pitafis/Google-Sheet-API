from flask import Flask, jsonify, request
import json
import os
import requests
from pyngrok import ngrok
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd

port_no = 5004

app = Flask(__name__)

# Set your ngrok auth token and establish a public URL
ngrok.set_auth_token("2lETlKZx1bORfyNwAr2AEym1opN_3vmdTzYSn1eKYrGPNoiob")
public_url = ngrok.connect(port_no)

DATA_FILE = 'hotel_data.json'
APPOINTMENTS_FILE = 'reservations.json' 

# Load room data from the JSON file
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r') as file:
            ROOMS = json.load(file)
    except json.JSONDecodeError:
        print("Error: The hotel_data.json file is not properly formatted.")
        ROOMS = []
else:
    print(f"Error: {DATA_FILE} not found.")
    ROOMS = []

@app.route('/api/reservation_inquire', methods=['GET'])
def inquire_room():
    room_type = request.args.get("room_type")

    if room_type:
        room_data = next((room for room in ROOMS if room['room_type'].lower() == room_type.lower()), None)
        if room_data:
            return jsonify({
                "room_type": room_data.get("room_type", "N/A"),
                "price_per_night": room_data.get("price_per_night", "N/A"),
                "availability": room_data.get("availability", False),
                "max_occupancy": room_data.get("max_occupancy", "N/A"),
                "success": True
            }), 200
        else:
            return jsonify({
                "error": f"Room type '{room_type}' not found",
                "success": False
            }), 404
    else:
        return jsonify({"rooms": ROOMS, "success": True}), 200

# @app.route('/api/appointment', methods=['POST'])
# def book_appointment():
#     try:
#         data = request.json
#         required_fields = ['name', 'email', 'date', 'time', 'guests', 'room_type']
#         missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
#         if missing_fields:
#             return jsonify({"success": False, "message": f"Missing fields: {', '.join(missing_fields)}"}), 400

#         # Send POST request to the external API
#         response = requests.post("https://66da9d23f47a05d55be54f7a.mockapi.io/reservation", json=data)
        
#         if response.status_code == 201:
#             return jsonify({"success": True, "message": "Appointment booked successfully!", "data": response.json()}), 201
#         else:
#             return jsonify({"success": False, "message": "Failed to book appointment with external API.", "error": response.text}), 500
    
#     except Exception as e:
#         return jsonify({"success": False, "message": str(e)}), 500

def save_call_to_google_sheet(call_data):
    # Ensure call_data is a dictionary
    if not isinstance(call_data, dict):
        return {"status": "error", "message": "Invalid data format: expected a dictionary."}

    # Create a row for Google Sheet with only 'to' and 'from'
    row = [
        call_data.get('to', 'N/A'),  # Handle missing 'to'
        call_data.get('from', 'N/A')  # Handle missing 'from'
    ]

    # Convert row into a DataFrame for Google Sheets
    df = pd.DataFrame([row], columns=['to', 'from'])

    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    # Authenticate using service account
    creds = Credentials.from_service_account_file('client_secret.json', scopes=scope)
    client = gspread.authorize(creds)

    try:
        # Try to open an existing Google Sheet
        spreadsheet = client.open('Test Cold Calling Output')
        sheet = spreadsheet.sheet1

    except gspread.exceptions.SpreadsheetNotFound:
        # If sheet is not found, create a new one
        try:
            spreadsheet = client.create('Test Cold Calling Output')
            spreadsheet.share('daniyalpitafi21@gmail.com', perm_type='user', role='writer')
            sheet = spreadsheet.sheet1
            sheet.append_row(['to', 'from'])  # Add headers for 'to' and 'from'

        except Exception as e:
            return {"status": "error", "message": f"Failed to create a new spreadsheet: {e}"}

    try:
        # Append the data to the Google Sheet
        sheet.append_row(row)

        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
        return {"status": "success", "spreadsheet_url": spreadsheet_url}

    except Exception as e:
        return {"status": "error", "message": f"An error occurred: {e}"}

@app.route('/save_call_data', methods=['POST'])
def save_call_data():
    # Get call data from the request body
    call_data = request.json

    # Save the 'to' and 'from' data to Google Sheets using the new function
    result = save_call_to_google_sheet(call_data)

    # Return the result (success or error message)
    return jsonify(result)

def save_to_google_sheet(analyzed_data):
    # Ensure analyzed_data is a dictionary
    if not isinstance(analyzed_data, dict):
        return {"status": "error", "message": "Invalid data format: expected a dictionary."}

    # Extract the data for the remaining columns (starting from column 3)
    row_data = [
        analyzed_data.get('name', 'N/A'),      # Full Name
        analyzed_data.get('email', 'N/A'),     # Email
        analyzed_data.get('date', 'N/A'),      # Reservation Date
        analyzed_data.get('time', 'N/A'),      # Reservation Time
        analyzed_data.get('guests', 'N/A'),    # Number of Guests
        analyzed_data.get('room_type', 'N/A')  # Room Type
    ]

    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

    # Authenticate using service account
    creds = Credentials.from_service_account_file('client_secret.json', scopes=scope)
    client = gspread.authorize(creds)

    try:
        # Try to open an existing Google Sheet
        spreadsheet = client.open('Test Cold Calling Output')
        sheet = spreadsheet.sheet1

        # Find the last row that was appended by 'save_call_to_google_sheet'
        last_row_index = len(sheet.get_all_values())  # Total number of rows

        if last_row_index < 2:
            return {"status": "error", "message": "No previous data to update. Make sure 'to' and 'from' are saved first."}

        # Update the last row (for 'name', 'email', etc.), starting from column 3
        for col_index, value in enumerate(row_data, start=3):
            sheet.update_cell(last_row_index, col_index, value)

        # Provide the spreadsheet URL
        spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
        return {"status": "success", "spreadsheet_url": spreadsheet_url}

    except Exception as e:
        return {"status": "error", "message": f"An error occurred: {e}"}


@app.route('/api/appointment', methods=['POST'])
def book_appointment():
    try:
        data = request.json
        
        # Extract required fields
        name = data.get('name')
        email = data.get('email')
        date = data.get('date')
        time = data.get('time')
        guests = data.get('guests')
        room_type = data.get('room_type')

        # Save data to Google Sheets
        sheet_data = {
            "name": name,
            "email": email,
            "date": date,
            "time": time,
            "guests": guests,
            "room_type": room_type
        }

        sheet_result = save_to_google_sheet(sheet_data)
        if sheet_result.get("status") != "success":
            return jsonify(sheet_result), 400
        
        return jsonify({
            "status": "success",
            "spreadsheet_url": sheet_result.get('spreadsheet_url'),
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print(f"Public URL: {public_url}")
    app.run(port=port_no)
