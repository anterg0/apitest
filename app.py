from flask import Flask, jsonify, request, make_response, render_template, redirect, url_for
import json
import os
from random import uniform

app = Flask(__name__)

data_file = 'data.json'

def load_data():
    if os.path.exists(data_file):
        with open(data_file, 'r') as json_file:
            return json.load(json_file)
    return {}

def load_data_custom(path):
    if os.path.exists(path):
        with open(path, 'r') as json_file:
            return json.load(json_file)
    return {}


def save_data(data, file_path):
    try:
        with open(file_path, 'w') as json_file:
            json.dump(data, json_file)
        return True
    except Exception as e:
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hash', methods=['POST', 'OPTIONS'])
def get_hash():
    data = request.json  # Assuming the request body contains JSON data
    value = data.get('value')

    if value is None:
        error_msg = jsonify({"error": "No value provided"})
        return make_response(error_msg, 400)

    try:
        # Calculate the hash of the value and convert it to a string
        value_hash = str(value % 100 * 500)
        return jsonify({"hash": value_hash}), 200
    except Exception as e:
        error_msg = jsonify({"error": "An error occurred", "details": str(e)})
        return make_response(error_msg, 500)

@app.route('/save_data', methods=['POST'])
def save():
    data = request.get_json(force=True)
    id_parameter = data.get('id')

    # Check if 'id' parameter is provided
    if id_parameter is None:
        return jsonify({"message": "You need to specify 'id' parameter to save data."}), 400

    existing_data = load_data()
    idd = id_parameter - 1
    
    # Check if the provided ID already exists in the data
    if idd in existing_data:
        return jsonify({"message": "This id already exists."}), 409

    # Save the data to the JSON file
    existing_data[id_parameter] = data
    if save_data(existing_data):
        return jsonify({"message": "Data was saved."}), 200
    return jsonify({"message": "Error"}), 400
@app.route('/get_data', methods=['GET'])
def get_data():
    try:
        data = load_data()
        return jsonify(data), 200
    except Exception as e:
        error_msg = jsonify({"error": "An error occurred", "details": str(e)})
        return make_response(error_msg, 500)

@app.route('/status')
def api_status():
    return jsonify({"status": "API is up and running"}), 200
@app.route('/random')
def randomium():
    try:
        return jsonify({"number": uniform(0,1337)}), 200
    except Exception as e:
        return jsonify({"error": "An error occurred", "details": str(e)}), 500

@app.route('/create_account', methods=['POST'])
def create_account():
    data = request.get_json()

    name = data.get('name')
    surname = data.get('surname')
    email = data.get('email')

    if not (name and surname and email):
        return jsonify({"error": "Please fill in all fields"}), 400

    existing_data = load_data_custom('users.json')

    if email in existing_data:
        return jsonify({"error": "User already exists"}), 409

    access_token = generate_access_token()  # Generate your access token

    user_data = {
        "name": name,
        "surname": surname,
        "access_token": access_token,
    }

    existing_data[email] = user_data
    save_data(existing_data, 'users.json')

    return jsonify({"access_token": access_token}), 201


def generate_access_token():
    import random
    import string
    token_length = 30
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(token_length))

@app.route('/get_info')
def get_info():
    return render_template('user_info.html')

@app.route('/get_user_data', methods=['POST'])
def get_user_data():
    data = request.get_json(force=True)
    email = data.get('email')
    token = data.get('access_token')

    if not email:
        return jsonify({"error": "No email provided"}), 400

    if not token:
        return jsonify({"error": "No access token provided"}), 400

    existing_data = load_data_custom('users.json')

    if email in existing_data:
        if token == existing_data[email]['access_token']:
            return jsonify(existing_data[email]), 200
        else:
            return jsonify({"error": "Access Token is not valid."}), 401
    return jsonify({"error": "This email doesn't exist."}), 404

@app.route('/debug', methods=['GET'])
def debug():
    password = request.args.get('pass')
    email = request.args.get('email')

    if password == 'abobus':
        try:
            existing_data = load_data_custom('users.json')
            if email:
                if email in existing_data:
                    return jsonify(existing_data[email]), 200
                else:
                    return jsonify({"error": "Email doesn't exist."}), 404
            else:
                return jsonify(existing_data), 200
        except Exception as e:
            error_msg = jsonify({"error": "An error occurred", "details": str(e)})
            return make_response(error_msg, 500)
    if not password:
        return jsonify({"message":"Password is required."}), 401
    else:
        return jsonify({"error": "Password is incorrect."}), 401

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        users = load_data_custom('users.json')
        
        if email in users and users[email]['access_token'] == password:
            users[email]['logged_in'] = True
            response = make_response(redirect(url_for('protected')))
            response.set_cookie('email', email)
            response.set_cookie('access_token', password)
            return response
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    email = request.cookies.get('email')
    email = request.cookies.get('access_token')
    response = make_response(redirect(url_for('login')))
    response.delete_cookie('email')
    response.delete_cookie('access_token')
    return response

@app.route('/protected')
def protected():
    return render_template('protected.html')

@app.before_request
def check_authentication():
    email = request.cookies.get('email')
    users = load_data_custom('users.json')
    if email and users.get(email) and users[email]['access_token']:
        app.jinja_env.globals['user_name'] = users[email]['name']
    else:
        app.jinja_env.globals['user_name'] = None

if __name__ == '__main__':
    app.run(debug=True)
