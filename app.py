from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session and flash messages

# Database connection function
def get_db_connection():
    conn = sqlite3.connect('rental_app.db')
    conn.row_factory = sqlite3.Row
    return conn

# Hash password function
def hash_password(password):
    sha = hashlib.sha512()
    sha.update(password.encode('utf-8'))
    return sha.hexdigest()

# Home Route
@app.route('/')
def index():
    return render_template('index.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO user (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
            flash('Registration successful! You can log in now.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another username.')
        finally:
            conn.close()
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = hash_password(request.form['password'])
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM user WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            flash('Login successful.')
            return redirect(url_for('list_cars'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

# Add Car Route (Accessible only if logged in)
@app.route('/add_cars', methods=['GET', 'POST'])
def add_car():
    if 'user_id' not in session:
        flash('Please log in to add a car.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        car_id = request.form['car_id']
        car_type = request.form['car_type']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO cars (car_id, car_type) VALUES (?, ?)', (car_id, car_type))
            conn.commit()
            flash('Car added successfully.')
            return redirect(url_for('list_cars'))
        except sqlite3.IntegrityError:
            flash('Car ID already exists. Please choose another ID.')
        finally:
            conn.close()
    return render_template('add_cars.html')

# List Cars Route
@app.route('/list_cars')
def list_cars():
    if 'user_id' not in session:
        flash('Please log in to view the cars.')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cars = conn.execute('SELECT * FROM cars').fetchall()
    conn.close()
    return render_template('cars.html', cars=cars)

# Rent Car Route
@app.route('/rent_cars', methods=['GET', 'POST'])
def rent_car():
    if 'user_id' not in session:
        flash('Please log in to rent a car.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        car_id = request.form['car_id']
        rental_days = int(request.form['rental_days'])
        conn = get_db_connection()
        car = conn.execute('SELECT * FROM cars WHERE car_id = ?', (car_id,)).fetchone()

        if car and car['is_available'] == 1:
            start_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            end_date = (datetime.now() + timedelta(days=rental_days)).strftime('%Y-%m-%d %H:%M:%S')
            conn.execute('INSERT INTO rentals (user_id, car_id, start_date, end_date) VALUES (?, ?, ?, ?)', 
                         (session['user_id'], car['id'], start_date, end_date))
            conn.execute('UPDATE cars SET is_available = 0 WHERE car_id = ?', (car_id,))
            conn.commit()
            flash('Car rented successfully!')
            conn.close()
            return redirect(url_for('list_cars'))
        else:
            flash('Car is not available.')
            conn.close()
    return render_template('rent_cars.html')

# Return Car Route
@app.route('/return_cars', methods=['GET', 'POST'])
def return_car():
    if 'user_id' not in session:
        flash('Please log in to return a car.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        rental_id = request.form['rental_id']
        conn = get_db_connection()
        rental = conn.execute('SELECT * FROM rentals WHERE id = ? AND user_id = ?', (rental_id, session['user_id'])).fetchone()

        if rental:
            conn.execute('DELETE FROM rentals WHERE id = ?', (rental_id,))
            conn.execute('UPDATE cars SET is_available = 1 WHERE id = ?', (rental['car_id'],))
            conn.commit()
            flash('Car returned successfully!')
        else:
            flash('Invalid rental ID.')
        conn.close()

    return render_template('return_cars.html')

if __name__ == '__main__':
    app.run(debug=True)
