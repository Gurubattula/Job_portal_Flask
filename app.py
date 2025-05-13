import os
from flask import Flask, render_template, request, redirect, url_for, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from db import create_connection, close_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads/resumes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Routes

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password)

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, role)
        )
        connection.commit()
        close_connection(connection)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, password, role FROM users WHERE name = %s", (name,))
        user = cursor.fetchone()
        close_connection(connection)

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id:
        return redirect(url_for('login'))

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    if role == 'recruiter':
        cursor.execute("SELECT * FROM jobs WHERE recruiter_id = %s", (user_id,))
        jobs = cursor.fetchall()
    else:
        cursor.execute("""
            SELECT j.* FROM jobs j
            JOIN applications a ON j.id = a.job_id
            WHERE a.user_id = %s
        """, (user_id,))
        jobs = cursor.fetchall()

    close_connection(connection)
    return render_template('dashboard.html', user=user, jobs=jobs)

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if session.get('role') != 'recruiter':
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        recruiter_id = session['user_id']

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO jobs (title, description, location, recruiter_id) VALUES (%s, %s, %s, %s)",
            (title, description, location, recruiter_id)
        )
        connection.commit()
        close_connection(connection)
        return redirect(url_for('dashboard'))

    return render_template('post_job.html')

@app.route('/jobs')
def jobs():
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT j.*, u.name 
        FROM jobs j 
        JOIN users u ON j.recruiter_id = u.id
    """)
    jobs = cursor.fetchall()
    close_connection(connection)
    return render_template('jobs.html', jobs=jobs)

@app.route('/apply/<int:job_id>', methods=['POST'])
def apply_job(job_id):
    user_id = session.get('user_id')
    resume = request.files['resume']

    if resume and user_id:
        path = os.path.join(UPLOAD_FOLDER, resume.filename)
        resume.save(path)

        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO applications (user_id, job_id, resume) VALUES (%s, %s, %s)",
            (user_id, job_id, path)
        )
        connection.commit()
        close_connection(connection)
    return redirect(url_for('dashboard'))

@app.route('/view_applications/<int:job_id>')
def view_applications(job_id):
    if session.get('role') != 'recruiter':
        return redirect(url_for('login'))

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT a.id, u.name, a.resume, a.applied_at 
        FROM applications a 
        JOIN users u ON a.user_id = u.id 
        WHERE a.job_id = %s
    """, (job_id,))
    applications = cursor.fetchall()
    close_connection(connection)
    return render_template('applications.html', applications=applications)

@app.route('/download_resume/<path:filename>')
def download_resume(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
