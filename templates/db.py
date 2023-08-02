from flask import Flask, render_template, request, redirect, url_for, session
from cassandra.cluster import Cluster
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = '<secret_key>'

cluster = Cluster(['<cassandra_host>'], port=<cassandra_port>)
session_db = cluster.connect('<keyspace_name>')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if user already exists
        result = session_db.execute(
            "SELECT * FROM users WHERE username = %s", (username,))
        if result.one() is not None:
            return render_template('signup.html', error='User already exists')

        # Hash password and store user data in the database
        hashed_password = generate_password_hash(password)
        session_db.execute(
            """
            INSERT INTO users (username, email, password)
            VALUES (%s, %s, %s)
            """,
            (username, email, hashed_password)
        )

        # Set session variables and redirect to the homepage
        session['username'] = username
        session['logged_in'] = True
        return redirect(url_for('home'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Retrieve user data from the database
        result = session_db.execute(
            "SELECT * FROM users WHERE username = %s", (username,))
        user = result.one()

        # Check if user exists and password is correct
        if user is None or not check_password_hash(user.password, password):
            return render_template('login.html', error='Invalid credentials')

        # Set session variables and redirect to the homepage
        session['username'] = user.username
        session['logged_in'] = True
        return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear session variables and redirect to the homepage
    session.clear()
    return redirect(url_for('home'))

@app.route('/')
def home():
    if 'logged_in' in session and session['logged_in']:
        return render_template('home.html', username=session['username'])
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
