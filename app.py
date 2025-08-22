
from flask import Flask, request, jsonify, render_template, send_from_directory, session, redirect, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re

app = Flask(__name__, static_folder='static')
app.secret_key = 'your_secret_key_here'  # Change this to a strong random value in production

@app.route('/')
def home():
	# Redirect root to cars page - this will be your main entry point
	return redirect(url_for('cars_page'))

@app.route('/login', methods=['GET'])
def login_page():
	# If user is already logged in, redirect to cars
	if session.get('logged_in'):
		return redirect(url_for('cars_page'))
	return render_template('login.html')

@app.route('/cars', methods=['GET'])
def cars_page():
	# Check if user is logged in
	if not session.get('logged_in'):
		# Redirect to login page if not authenticated
		return redirect(url_for('login_page'))
	
	# User is authenticated, serve cars.html
	return send_from_directory(os.path.dirname(__file__), 'cars.html')

# Serve static files (CSS, JS)
@app.route('/static/<path:filename>')
def static_files(filename):
	return send_from_directory('static', filename)

# Serve CSS files from root directory for login.html
@app.route('/<filename>')
def serve_files(filename):
	if filename.endswith('.css') or filename.endswith('.js'):
		return send_from_directory(os.path.dirname(__file__), filename)
	return '', 404

def get_db_connection():
	try:
		conn = sqlite3.connect('URdb.sqlite')
		conn.row_factory = sqlite3.Row
		return conn
	except Exception as e:
		print(f"Database connection error: {e}")
		return None

# Registration endpoint
@app.route('/register', methods=['POST'])
def register():
	try:
		data = request.get_json()
		if not data:
			return jsonify({'status': 'error', 'message': 'No data received.'}), 400
			
		username = data.get('UserName')
		mail = data.get('mail')
		password = data.get('Password')
		
		print(f"Registration attempt - Username: {username}, Email: {mail}")  # Debug log
		
		if not username or not mail or not password:
			return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400
			
		# Email format validation
		email_regex = r'^\S+@\S+\.\S+$'
		if not re.match(email_regex, mail):
			return jsonify({'status': 'error', 'message': 'Invalid email format.'}), 400
			
		# Password strength validation (min 6 chars, at least 1 digit, 1 letter)
		if len(password) < 6 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
			return jsonify({'status': 'error', 'message': 'Password must be at least 6 characters long and contain both letters and numbers.'}), 400
			
		hashed_password = generate_password_hash(password)
		conn = get_db_connection()
		
		if not conn:
			return jsonify({'status': 'error', 'message': 'Database connection failed.'}), 500
			
		try:
			cursor = conn.cursor()
			# Check if user already exists
			cursor.execute('SELECT * FROM users WHERE mail = ?', (mail,))
			if cursor.fetchone():
				conn.close()
				return jsonify({'status': 'error', 'message': 'User already exists.'}), 409
				
			# Insert new user
			cursor.execute('INSERT INTO users (UserName, mail, Password) VALUES (?, ?, ?)', (username, mail, hashed_password))
			conn.commit()
			conn.close()
			
			print(f"User {username} registered successfully")  # Debug log
			return jsonify({'status': 'success', 'message': 'User registered successfully.'}), 201
			
		except Exception as e:
			print(f"Database error during registration: {e}")  # Debug log
			if conn:
				conn.close()
			return jsonify({'status': 'error', 'message': 'Database error: ' + str(e)}), 500
			
	except Exception as e:
		print(f"Unexpected error during registration: {e}")  # Debug log
		return jsonify({'status': 'error', 'message': 'Server error: ' + str(e)}), 500

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
	try:
		data = request.get_json()
		if not data:
			return jsonify({'status': 'error', 'message': 'No data received.'}), 400
			
		mail = data.get('mail')
		password = data.get('Password')
		
		print(f"Login attempt - Email: {mail}")  # Debug log
		
		if not mail or not password:
			return jsonify({'status': 'error', 'message': 'All fields are required.'}), 400
			
		conn = get_db_connection()
		if not conn:
			return jsonify({'status': 'error', 'message': 'Database connection failed.'}), 500
			
		try:
			cursor = conn.cursor()
			cursor.execute('SELECT * FROM users WHERE mail = ?', (mail,))
			user = cursor.fetchone()
			conn.close()
			
			if user and check_password_hash(user['Password'], password):
				session['logged_in'] = True
				session['user'] = {'UserName': user['UserName'], 'mail': user['mail']}
				
				print(f"User {user['UserName']} logged in successfully")  # Debug log
				return jsonify({
					'status': 'success', 
					'message': 'Login successful.', 
					'UserName': user['UserName'], 
					'mail': user['mail'], 
					'redirect': '/cars'
				}), 200
			else:
				print(f"Login failed for email: {mail}")  # Debug log
				return jsonify({'status': 'error', 'message': 'Invalid credentials.'}), 401
				
		except Exception as e:
			print(f"Database error during login: {e}")  # Debug log
			if conn:
				conn.close()
			return jsonify({'status': 'error', 'message': 'Database error: ' + str(e)}), 500
			
	except Exception as e:
		print(f"Unexpected error during login: {e}")  # Debug log
		return jsonify({'status': 'error', 'message': 'Server error: ' + str(e)}), 500

# Logout endpoint
@app.route('/logout')
def logout():
	session.clear()
	return redirect(url_for('login_page'))

# Check session endpoint
@app.route('/check-session')
def check_session():
	if session.get('logged_in'):
		return jsonify({
			'logged_in': True,
			'user': session.get('user', {})
		})
	else:
		return jsonify({
			'logged_in': False,
			'user': None
		})

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=5000)
