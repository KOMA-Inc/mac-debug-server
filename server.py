import sys
import logging
import socket
from flask import Flask, request, jsonify
from prettytable import PrettyTable
from datetime import datetime
import threading
from tzlocal import get_localzone
import base64
import json
from textwrap import fill

# Disable the logging of HTTP requests
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Flask(__name__)

# Define a lock for thread-safe printing
print_lock = threading.Lock()

response = {
    "success": True,
    "data": ""
}

def server_date():
    date = formatted_date(datetime.now().timestamp())
    return date

def formatted_date(timestamp):
    # Convert the timestamp to a datetime object
    local_timezone = get_localzone()
    date = datetime.fromtimestamp(timestamp, tz=local_timezone)
    # Convert the localized datetime object to the desired format
    formatted_dt = date.strftime('%H:%M:%S %d.%m.%Y')
    return formatted_dt

# Function to print text in color
def colored_string(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m'
    }
    end_color = '\033[0m'
    return f"\033[1m{colors.get(color, '')}{text}{end_color}"

def colored_http_method(method):
    str = bold_text("[")
    if method == 'GET':
        str += colored_string(method, 'blue')
    elif method == "POST":
        str += colored_string(method, 'green')
    elif method == "DELETE":
        str += colored_string(method, 'red')
    else:
        str += bold_text(method)
    str += bold_text("]")
    return str

def colored_status_code(status_code):
    code = str(status_code)
    if status_code < 200:
        return code
    elif status_code < 300:
        return colored_string(code, 'green')
    elif status_code < 400:
        return code
    else:
        return colored_string(code, 'red')

def bold_text(text):
    return f"\033[1m{text}\033[0m"

# Common function to log and return response
def log_and_return(event_name, value, text, color):
    with print_lock:
        print(colored_string(text, color))
        print(bold_text("Event name:"), event_name)
        print(bold_text("Value:"), value)
        print()
    return jsonify(response)

# Endpoint to increment value
@app.route('/log/analytics/increment-property', methods=['POST'])
def increment():
    data = request.json
    event_name = data.get('event_name')
    value = data.get('value')

    return log_and_return(event_name, value, "Incremented user property", "green")

# Endpoint to set int property
@app.route('/log/analytics/set-int-property', methods=['POST'])
def set_int_property():
    data = request.json
    event_name = data.get('event_name')
    value = data.get('value')

    return log_and_return(event_name, value, "Set user property", "blue")

# Endpoint to set string property
@app.route('/log/analytics/set-string-property', methods=['POST'])
def set_string_property():
    data = request.json
    event_name = data.get('event_name')
    value = data.get('value')

    return log_and_return(event_name, value, "Set user property", "blue")
    
@app.route('/log/analytics/send-event', methods=['POST'])
def log_analytics():
    data = request.json
    event_name = data.get('event_name')
    event_properties = data.get('event_properties', {})
    timestamp = data.get('date')

    with print_lock:
        print(colored_string("Analytics event received", "yellow"))
        print(bold_text("Event name:"), event_name)
        print(bold_text("Client date:"), formatted_date(timestamp))
        print(bold_text("Server date:"), server_date())
        # Display event parameters in a table if present
        if event_properties:
            table = PrettyTable(["Parameter", "Value"])
            table.align["Value"] = "l"
            for key, value in event_properties.items():
                table.add_row([key, value])
            print(bold_text("Event properties:"))
            print(table)

        print()

    return jsonify(response)

@app.route('/log/server/request', methods=['POST'])
def log_server_request():
    data = request.json
    endpoint = data.get('endpoint')
    http_method = data.get('http_method')
    http_headers = data.get('http_headers', {})
    request_id = data.get('id')
    encoded_body = data.get('body')
    timestamp = data.get('date')

    with print_lock:
        print()
        print(colored_string("📤 REQUEST", "yellow"))
        print(f"{colored_http_method(http_method)} {endpoint}")
        print(bold_text("Client date:"), formatted_date(timestamp))
        print(bold_text("Server date:"), server_date())
        print(f"{bold_text('ID:')} {request_id}")

        # Print HTTP headers in a table
        if http_headers:
            headers_table = PrettyTable(["Header", "Value"])
            for key, value in http_headers.items():
                headers_table.add_row([key, value])
            print(f"{bold_text('HTTP Headers:')}")
            print(headers_table)

        # Decode and print request body as formatted JSON if it's JSON, otherwise print decoded string
        if encoded_body:
            try:
                decoded_body = base64.b64decode(encoded_body).decode('utf-8')
                # Try to load body as JSON
                body_json = json.loads(decoded_body)
                # If successful, pretty-print as JSON
                pretty_body = json.dumps(body_json, indent=4)
                print(f"{bold_text('Body:')}")
                print(pretty_body)
            except json.JSONDecodeError:
                # If body is not JSON, print decoded string
                print(f"{bold_text('Body:')}")
                print(decoded_body)
            except Exception as e:
                print("Error decoding or parsing body:", e)

        print()
        print("-----------------------------------------------------------------------------")

    return jsonify(response)

@app.route('/log/server/response', methods=['POST'])
def log_server_response():
    data = request.json
    status_code = data.get('status_code')
    endpoint = data.get('endpoint')
    http_method = data.get('http_method')
    http_headers = data.get('http_headers', {})
    request_id = data.get('id')
    encoded_body = data.get('body')
    timestamp = data.get('date')
    error = data.get('error')

    with print_lock:
        print()
        if status_code:
            print(colored_string("📥 RESPONSE", "yellow"), colored_status_code(status_code))
        else:
            print(colored_string("📥 RESPONSE", "yellow"))
        print(f"{colored_http_method(http_method)} {endpoint}")    
        print(bold_text("Client date:"), formatted_date(timestamp))
        print(bold_text("Server date:"), server_date())
        if error:
            print("‼️ ", colored_string("Error: ", "red"), error)
        print(f"{bold_text('ID:')} {request_id}")

        # Print HTTP headers in a table
        if http_headers:
            headers_table = PrettyTable(["Header", "Value"])
            for key, value in http_headers.items():
                headers_table.add_row([key, fill(value, width=50)])
            print(f"{bold_text('HTTP Headers:')}")
            print(headers_table)

        # Decode and print request body as formatted JSON if it's JSON, otherwise print decoded string
        if encoded_body:
            try:
                decoded_body = base64.b64decode(encoded_body).decode('utf-8')
                # Try to load body as JSON
                body_json = json.loads(decoded_body)
                # If successful, pretty-print as JSON
                pretty_body = json.dumps(body_json, indent=4)
                print(f"{bold_text('Body:')}")
                print(pretty_body)
            except json.JSONDecodeError:
                # If body is not JSON, print decoded string
                print(f"{bold_text('Body:')}")
                print(decoded_body)
            except Exception as e:
                print("Error decoding or parsing body:", e)

        print()
        print("-----------------------------------------------------------------------------")

    return jsonify(response)

def get_ip_address():
    try:
        # Get the IP address of the host machine
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        print("Failed to retrieve IP address:", e)
        return "127.0.0.1"

def run_server(port):
    app.logger.disabled = True  # Disable Flask's default logger
    server_address = (get_ip_address(), port)
    ip_address = bold_text(server_address[0])  # Make IP address bold
    print(f"Server running on http://{ip_address}:{port}")
    app.run(host=server_address[0], port=port, debug=False)

if __name__ == '__main__':
    if len(sys.argv) == 2:
        port = int(sys.argv[1])
        run_server(port)
    else:
        print("Usage: python3 server.py <port>")
