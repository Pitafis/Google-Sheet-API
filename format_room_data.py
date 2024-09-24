import requests

def format_room_data(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Check for HTTP errors
        rooms = response.json()  # Parse the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return []

    # Format the data to fit into the 'dynamic_data' structure
    dynamic_data = []
    for room in rooms:
        # Ensure that 'room' is a dictionary before attempting to access its keys
        if isinstance(room, dict):
            room_type = room.get('room_type', 'Unknown')
            price_per_night = room.get('price_per_night', 'Unknown')
            availability = room.get('availability', 'Unknown')
            max_occupancy = room.get('max_occupancy', 'Unknown')

            # Each room gets entries for price, availability, and max occupancy in the dynamic_data list
            dynamic_data.append({
                "name": f"{room_type} Price",
                "data": f"{room_type}.price_per_night",
                "context": f"The price for a {room_type} room is ${{{{{room_type} Price}}}} per night."
            })
            dynamic_data.append({
                "name": f"{room_type} Availability",
                "data": f"{room_type}.availability",
                "context": f"The {room_type} room is ${{{{{room_type} Availability}}}} available."
            })
            dynamic_data.append({
                "name": f"{room_type} Max Occupancy",
                "data": f"{room_type}.max_occupancy",
                "context": f"The {room_type} room can accommodate up to ${{{{{room_type} Max Occupancy}}}} people."
            })
        else:
            print(f"Unexpected data format: {room}")
    return dynamic_data

# Test output (You can remove this when integrating)
if __name__ == "__main__":
    api_url = "https://8bea-121-52-154-73.ngrok-free.app/api/reservation_inquire"  # Modify with your actual API URL if needed
    data = format_room_data(api_url)
    print(data)
