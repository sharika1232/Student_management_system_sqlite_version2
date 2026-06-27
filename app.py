from flask import Flask, render_template, request, redirect, flash, session, url_for
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"


# ========================
# DATABASE CONNECTION
# ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR,"student.db")
def get_db():
    conn=sqlite3.connect("student.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        stu_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        course TEXT,
        mobile TEXT
    )
    """)

    db.commit()
    cursor.close()
    db.close()

create_tables()

@app.route('/')
def home():
    return redirect('/admin-login')


@app.route('/admin-register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect('/admin-register')

        hashed_password = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()

        try:
            cursor.execute("""
                INSERT INTO admin (username, email, password)
                VALUES (?,?,?)
            """, (username, email, hashed_password))

            db.commit()
            flash("Admin registered successfully!")
            return redirect('/admin-login')

        except sqlite3.IntegrityError as e:
            print("Database Error:", e)   # Terminal lo actual error chupisthundi
            flash(f"Database Error: {e}")
            return redirect('/admin-register')

        finally:
            cursor.close()
            db.close()

    return render_template("admin_register.html")

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE email=?",
            (email,)
        )

        admin = cursor.fetchone()

        cursor.close()
        db.close()

        if admin and check_password_hash(admin["password"], password):
            session['admin_id'] = admin["id"]
            session['admin_username'] = admin["username"]
            return redirect('/dashboard')
        else:
            flash("Invalid email or password!")
            return redirect('/admin-login')

    return render_template("admin_login.html")


@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect('/admin-login')

    return render_template("dashboard.html", username=session['admin_username'])


@app.route('/add-student', methods=['GET', 'POST'])
def add_student():
    if 'admin_id' not in session:
        return redirect('/admin-login')

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']
        mobile = request.form['mobile']

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO students (name, email, course, mobile)
            VALUES (?, ?, ?, ?)
        """, (name, email, course, mobile))

        db.commit()
        cursor.close()
        db.close()

        flash("Student added successfully!")
        return redirect(url_for('view_students'))

    return render_template("add_student.html")


@app.route('/view_students')
def view_students():
    if 'admin_id' not in session:
        return redirect('/admin-login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT stu_id AS id, name, email, course, mobile FROM students")
    students = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("view_students.html", students=students)


@app.route('/view_student/<int:id>')
def view_student(id):
    if 'admin_id' not in session:
        return redirect('/admin-login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT stu_id AS id, name, email, course, mobile
        FROM students
        WHERE stu_id = ?
    """, (id,))

    student = cursor.fetchone()

    cursor.close()
    db.close()

    if not student:
        flash("Student not found!")
        return redirect(url_for('view_students'))

    return render_template("view_student.html", student=student)


@app.route('/update_student/<int:id>', methods=['GET', 'POST'])
def update_student(id):
    if 'admin_id' not in session:
        return redirect('/admin-login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT stu_id AS id, name, email, course, mobile FROM students WHERE stu_id=?",
        (id,)
    )

    student = cursor.fetchone()

    if not student:
        cursor.close()
        db.close()
        flash("Student not found!")
        return redirect(url_for('view_students'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']
        mobile = request.form['mobile']

        cursor2 = db.cursor()

        cursor2.execute("""
            UPDATE students
            SET name=?,
                email=?,
                course=?,
                mobile=?
            WHERE stu_id=?
        """, (name, email, course, mobile, id))

        db.commit()

        cursor2.close()
        cursor.close()
        db.close()

        flash("Student updated successfully!")
        return redirect(url_for('view_students'))

    cursor.close()
    db.close()

    return render_template("update_student.html", student=student)

@app.route('/delete_student/<int:id>')
def delete_student(id):
    if 'admin_id' not in session:
        return redirect('/admin-login')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM students WHERE stu_id=?", (id,))

    db.commit()
    cursor.close()
    db.close()

    flash("Student deleted successfully!")
    return redirect(url_for('view_students'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM admin WHERE email=?", (email,))
        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user:
            session['reset_email'] = email
            return redirect('/reset-password')
        else:
            flash("Email not found!")
            return redirect('/forgot-password')

    return render_template("forgot_password.html")


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        return redirect('/forgot-password')

    if request.method == 'POST':
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash("Passwords do not match!")
            return redirect('/reset-password')

        hashed = generate_password_hash(password)

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            UPDATE admin
            SET password=?
            WHERE email=?
        """, (hashed, session['reset_email']))

        db.commit()
        cursor.close()
        db.close()

        session.pop('reset_email', None)

        flash("Password updated successfully!")
        return redirect('/admin-login')

    return render_template("reset_password.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin-login')

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)