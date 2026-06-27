from flask import Flask, render_template, request, redirect, flash, session, url_for
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"


# ========================
# DATABASE CONNECTION
# ========================
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="student_management"
    )



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
                VALUES (%s, %s, %s)
            """, (username, email, hashed_password))

            db.commit()
            flash("Admin registered successfully!")
            return redirect('/admin-login')

        except mysql.connector.IntegrityError as e:
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
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM admin WHERE email=%s", (email,))
        admin = cursor.fetchone()

        cursor.close()
        db.close()

        if admin and check_password_hash(admin['password'], password):
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
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
            VALUES (%s, %s, %s, %s)
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
    cursor = db.cursor(dictionary=True)

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
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
SELECT stu_id AS id, name, email, course, mobile
FROM students
""")
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
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT stu_id AS id, name, email, course, mobile FROM students WHERE stu_id=%s", (id,))
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
            SET name=%s,
                email=%s,
                course=%s,
                mobile=%s
            WHERE stu_id=%s
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

    cursor.execute("DELETE FROM students WHERE stu_id=%s", (id,))

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
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT * FROM admin WHERE email=%s", (email,))
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
            SET password=%s
            WHERE email=%s
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
    app.run(debug=True)