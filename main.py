import json
import requests
from flask import Flask, request, session, render_template, redirect, url_for, jsonify
from format_room_data import format_room_data
from tool import RESERVATION_APPOINTMENT_TOOL

app = Flask(__name__)
app.secret_key = 'your_secret_key'


API = "sub-sk-f9e2d088-d640-433f-9030-4f319c5f467c-a90fe6fa-004f-4dad-abcf-d75016d6d0d2"
BASE_URL = "https://api.bland.ai/v1/calls"

@app.route('/', methods=["POST", "GET"])
def index():
    message = session.pop('message', None)
    if request.method == 'POST':
        api_url = "https://f74f-121-52-154-72.ngrok-free.app/api/reservation_inquire"
        response_data = format_room_data(api_url)

        payload = {
            "phone_number": request.form['phone_number'],
            "task": request.form['task'],
            "voice": "13843c96-ab9e-4938-baf3-ad53fcee541d",
            "model": "enhanced",
            "transfer_phone_number": "+923463952555",
            "language": "en",
            "max_duration": 5, 
            "tools": [RESERVATION_APPOINTMENT_TOOL],
            "dynamic_data": [
                {
                    "url": api_url,
                    "response_data": response_data
                }
            ],
        }
        headers = {
            "authorization": API,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(BASE_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            session['message'] = {
                "status": data.get("status"),
                "call_id": data.get("call_id"),
                "message": data.get("message"),
            }

            # Extract call_id and redirect to call_data route
            call_id = data.get("call_id")
            return redirect(url_for('call_data', call_id=call_id))

        except requests.exceptions.RequestException as e:
            session['message'] = {"error": str(e)}

        return redirect(url_for('index'))

    return render_template('index.html', message=message)

@app.route('/call_data/<call_id>', methods=['GET'])
def call_data(call_id):
    # Define the Bland.ai URL with the call_id
    url = f"https://api.bland.ai/v1/calls/{call_id}"
    
    headers = {
        "authorization": API
    }
    
    try:
        # Fetch call data from Bland.ai
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Extract 'to' and 'from' fields
        call_info = {
            "to": data.get("to"),
            "from": data.get("from"),
            "status": data.get("status"),
            "duration": data.get("duration")
        }

        # Post call data to the external appointment booking API
        appointment_url = "https://f74f-121-52-154-72.ngrok-free.app/save_call_data"
        appointment_response = requests.post(appointment_url, json=call_info)
        appointment_response.raise_for_status()

        return jsonify({"success": "Call data posted successfully", "call_info": call_info})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reservations', methods=['GET'])
def show_reservations():
    try:
        # Fetch reservations from the external API
        response = requests.get('https://66da9d23f47a05d55be54f7a.mockapi.io/reservation')
        
        if response.status_code == 200:
            reservations = response.json()  # Parse the response to get the reservation data
        else:
            return jsonify({"error": "Failed to fetch reservations from API"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Render reservations in the HTML template
    return render_template('reservations.html', reservations=reservations)

if __name__ == '__main__':
    app.run(port=5000)
