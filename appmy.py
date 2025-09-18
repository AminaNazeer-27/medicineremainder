
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medtrack.db'
db = SQLAlchemy(app)

# -----------------------------
# Database Models
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    expiry_date = db.Column(db.String(20), nullable=False)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'))
    reminder_time = db.Column(db.String(20), nullable=False)
    frequency = db.Column(db.String(20), nullable=False)
    medicine = db.relationship("Medicine", backref="reminders")

class AlternativeMedicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    condition = db.Column(db.String(100), nullable=False)   # Example: Fever
    medicine_name = db.Column(db.String(100), nullable=False)  # Example: Paracetamol
    alternative_name = db.Column(db.String(100), nullable=False)  # Example: Dolo-650


# -----------------------------
# WHO Alternative Medicine Seeder
# -----------------------------
def seed_alternative_medicines():
    if AlternativeMedicine.query.count() == 0:  # only insert if empty
        data = [
            {"condition": "Fever", "medicine_name": "Paracetamol", "alternative_name": "Dolo-650"},
            {"condition": "Fever", "medicine_name": "Paracetamol", "alternative_name": "Crocin"},
            {"condition": "Cold", "medicine_name": "Cetirizine", "alternative_name": "Levocetirizine"},
            {"condition": "Headache", "medicine_name": "Paracetamol", "alternative_name": "Ibuprofen"},
            {"condition": "Diabetes", "medicine_name": "Metformin", "alternative_name": "Glimepiride"},
            {"condition": "Hypertension", "medicine_name": "Amlodipine", "alternative_name": "Losartan"},
        ]

        for item in data:
            alt = AlternativeMedicine(
                condition=item["condition"],
                medicine_name=item["medicine_name"],
                alternative_name=item["alternative_name"]
            )
            db.session.add(alt)

        db.session.commit()
        print("✅ WHO Alternative Medicines inserted.")


# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def home():
    return render_template("index.html")

# -------- Register --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form['password']

        # Check duplicates
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash("Username already taken!", "danger")
            return redirect(url_for('register'))
        if User.query.filter_by(phone=phone).first():
            flash("Phone number already registered!", "danger")
            return redirect(url_for('register'))

        # Phone validation (10 digits)
        if len(phone) != 10 or not phone.isdigit():
            flash("Phone number must be exactly 10 digits.", "danger")
            return redirect(url_for('register'))

        # Password validation (8+ chars, letters, numbers, symbols)
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
            flash("Password must be at least 8 characters and include letters, numbers & symbols.", "danger")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, phone=phone, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template("register.html")

# -------- Login --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password!", "danger")

    return render_template("login.html")

# -------- Logout --------
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

# -------- Dashboard --------
@app.route('/dashboard')
def dashboard():
    if "user_id" not in session:
        return redirect(url_for('login'))
    medicines = Medicine.query.filter_by(user_id=session['user_id']).all()
    return render_template("dashboard.html", username=session['username'], medicines=medicines)

# -------- Add Medicine --------
@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if "user_id" not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        dosage = request.form['dosage']
        expiry_date = request.form['expiry_date']

        new_medicine = Medicine(user_id=session['user_id'], name=name, dosage=dosage, expiry_date=expiry_date)
        db.session.add(new_medicine)
        db.session.commit()
        flash("Medicine added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template("add_medicine.html")

# -------- Delete Medicine --------
@app.route('/delete_medicine/<int:id>')
def delete_medicine(id):
    if "user_id" not in session:
        return redirect(url_for('login'))

    medicine = Medicine.query.get(id)
    if medicine and medicine.user_id == session['user_id']:
        db.session.delete(medicine)
        db.session.commit()
        flash("Medicine deleted successfully!", "success")
    return redirect(url_for('dashboard'))

# -------- Reminders --------
@app.route('/reminder', methods=['GET', 'POST'])
def reminder():
    if "user_id" not in session:
        return redirect(url_for('login'))

    medicines = Medicine.query.filter_by(user_id=session['user_id']).all()

    if request.method == 'POST':
        medicine_id = request.form['medicine_id']
        reminder_time = request.form['reminder_time']
        frequency = request.form['frequency']

        new_reminder = Reminder(user_id=session['user_id'], medicine_id=medicine_id,
                                reminder_time=reminder_time, frequency=frequency)
        db.session.add(new_reminder)
        db.session.commit()
        flash("Reminder added successfully!", "success")
        return redirect(url_for('reminder'))

    reminders = Reminder.query.filter_by(user_id=session['user_id']).all()
    return render_template("reminder.html", medicines=medicines, reminders=reminders)

# -------- Delete Reminder --------
@app.route('/delete_reminder/<int:id>')
def delete_reminder(id):
    if "user_id" not in session:
        return redirect(url_for('login'))

    reminder = Reminder.query.get(id)
    if reminder and reminder.user_id == session['user_id']:
        db.session.delete(reminder)
        db.session.commit()
        flash("Reminder deleted successfully!", "success")

    return redirect(url_for('reminder'))

# -------- Alternative Medicines --------
@app.route('/alternative_medicines')
def alternative_medicines():
    alternatives = AlternativeMedicine.query.all()
    return render_template("alternative_medicines.html", alternatives=alternatives)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        seed_alternative_medicines()  # <-- insert WHO alternatives
    app.run(debug=True)
