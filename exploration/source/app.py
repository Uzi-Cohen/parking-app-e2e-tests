import os
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, ParkingSession, VehicleType
from forms import LoginForm, ParkingForm, EndParkingForm, UserForm, VehicleTypeForm
import requests
import redis
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'change-me',
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///parking.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False,
    'UPLOAD_FOLDER': 'uploads'
})

# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Redis configuration with environment variable support
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
redis_client = redis.from_url(redis_url)

# External services URLs
SLOT_SERVICE_URL = os.getenv('SLOT_SERVICE_URL', "http://localhost:5001")
BILLING_SERVICE_URL = os.getenv('BILLING_SERVICE_URL', "http://localhost:5002")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=generate_password_hash('password'))
            db.session.add(admin)
        if not VehicleType.query.filter_by(name='Standard').first():
            vt = VehicleType(name='Standard', rate_per_hour=5.0)
            db.session.add(vt)
        db.session.commit()
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def calculate_fee(start_time, end_time, rate_per_hour):
    hours = (end_time - start_time).total_seconds() / 3600.0
    return round(hours * rate_per_hour, 2)


@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    sessions = ParkingSession.query.filter_by(end_time=None).all()
    parking_form = ParkingForm()
    parking_form.vehicle_type_id.choices = [(vt.id, vt.name) for vt in VehicleType.query.all()]
    return render_template('dashboard.html', sessions=sessions, parking_form=parking_form)

@app.route('/vehicle-types', methods=['GET','POST'])
@login_required
def vehicle_types():
    form = VehicleTypeForm()
    if form.validate_on_submit():
        vt = VehicleType(name=form.name.data, rate_per_hour=form.rate_per_hour.data)
        db.session.add(vt)
        db.session.commit()
        flash('Vehicle type added', 'success')
        return redirect(url_for('vehicle_types'))
    types = VehicleType.query.all()
    return render_template('vehicle_types.html', types=types, form=form)

@app.route('/start', methods=['POST'])
@login_required
def start_parking():
    form = ParkingForm()
    form.vehicle_type_id.choices = [(vt.id, vt.name) for vt in VehicleType.query.all()]
    print('Form data:', form.data)
    print('Form valid:', form.validate_on_submit())
    if form.validate_on_submit():
        plate = form.car_plate.data.strip()  # Clean the input
        vt_id = form.vehicle_type_id.data
        slot = form.slot.data
        
        # Additional server-side validation
        if not plate.isdigit() or len(plate) != 8:
            flash('Invalid license plate format. Must be exactly 8 digits.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Redis-based slot conflict prevention
        slot_key = f"slot:{slot}"
        try:
            if redis_client.exists(slot_key):
                flash('This slot is already occupied.', 'warning')
                return redirect(url_for('dashboard'))
            redis_client.set(slot_key, plate)
            redis_client.expire(slot_key, 3600)
        except Exception as e:
            print('Redis not available (slot check):', e)
        # Only block if there is an active session for this car plate
        active_session = ParkingSession.query.filter_by(car_plate=plate, end_time=None).first()
        if active_session:
            flash('Duplicate parking prevented: this car is already parked.', 'warning')
            return redirect(url_for('dashboard'))
        # (Optional) You can keep the Redis logic for car plate for extra protection, or remove it
        try:
            key = f"park:{plate}"
            redis_client.setnx(key, '1')
            redis_client.expire(key, 3600)
        except Exception as e:
            print('Redis not available (car check):', e)
        reserve_slot(slot)
        image_path = None
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(path)
            image_path = filename
        session = ParkingSession(
            car_plate=plate,
            user=current_user,
            start_time=datetime.utcnow(),
            vehicle_type_id=vt_id,
            image_path=image_path,
            slot=slot
        )
        db.session.add(session)
        db.session.commit()
        print('Session created:', session)
        # Notify if more than 3 active parkings
        active_count = ParkingSession.query.filter_by(end_time=None).count()
        if active_count > 3:
            try:
                from notification_service import notification_queue
                notification_queue.put(('all', 'More than 3 active parkings!'))
            except Exception as e:
                print('Notification queue error:', e)
            flash('active_parking_limit', 'info')
        flash(f'Parking started for {plate}', 'success')
    else:
        print('Form errors:', form.errors)
        # Display specific validation errors to user
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field.replace("_", " ").title()}: {error}', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/end/<int:session_id>', methods=['POST'])
@login_required
def end_parking(session_id):
    session = ParkingSession.query.get_or_404(session_id)
    session.end_time = datetime.utcnow()
    rate = session.vehicle_type.rate_per_hour
    session.fee = calculate_fee(session.start_time, session.end_time, rate)
    release_slot(session.slot)
    # Remove slot reservation from Redis
    try:
        slot_key = f"slot:{session.slot}"
        redis_client.delete(slot_key)
    except Exception as e:
        print('Redis not available (slot release):', e)
    db.session.commit()

    # --- Billing integration ---
    billing_status = "error"
    try:
        res = requests.post(
            f"{BILLING_SERVICE_URL}/charge",
            json={"license_plate": session.car_plate, "amount": session.fee},
            timeout=5
        )
        billing_status = res.json().get("status", "error")
    except Exception as e:
        print("Billing error:", e)

    # --- Notification integration (asynchronous) ---
    try:
        from notification_service import notification_queue
        notification_queue.put((session.slot, f"חניה שוחררה לרכב {session.car_plate}, סטטוס חיוב: {billing_status}"))
    except Exception as e:
        print("Notification error:", e)

    flash(f'Parking ended for {session.car_plate}. Fee: ₪{session.fee} (חיוב: {billing_status})', 'info')
    return redirect(url_for('dashboard'))

@app.route('/history')
@login_required
def history():
    past = ParkingSession.query.filter(ParkingSession.end_time.isnot(None)).order_by(ParkingSession.end_time.desc()).all()
    return render_template('history.html', past=past)

@app.route('/users')
@login_required
def users():
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/users/add', methods=['GET','POST'])
@login_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose another.', 'warning')
            return render_template('user_form.html', form=form)
        u = User(username=form.username.data, password=generate_password_hash(form.password.data))
        db.session.add(u)
        db.session.commit()
        flash('User created', 'success')
        return redirect(url_for('users'))
    return render_template('user_form.html', form=form)

@app.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    u = User.query.get_or_404(user_id)
    if u.sessions:
        flash('Cannot delete user with parking sessions.', 'warning')
        return redirect(url_for('users'))
    db.session.delete(u)
    db.session.commit()
    flash('User deleted', 'warning')
    return redirect(url_for('users'))

# Slot service functions
def get_available_slots():
    resp = requests.get(f"{SLOT_SERVICE_URL}/slots/available")
    return resp.json().get('available_slots', [])

def reserve_slot(slot):
    try:
        requests.post(f"{SLOT_SERVICE_URL}/slots/reserve", json={'slot': slot})
    except Exception as e:
        print("Slot service not available:", e)

def release_slot(slot):
    try:
        requests.post(f"{SLOT_SERVICE_URL}/slots/release", json={'slot': slot})
    except Exception as e:
        print("Slot service not available:", e)

@app.route('/slots')
@login_required
def slots():
    slots = get_available_slots()
    return render_template('slots.html', slots=slots)

@app.route('/slots/reserve', methods=['POST'])
@login_required
def slots_reserve():
    slot = request.form['slot']
    reserve_slot(slot)
    flash(f'Slot {slot} reserved', 'success')
    return redirect(url_for('slots'))

@app.route('/slots/release', methods=['POST'])
@login_required
def slots_release():
    slot = request.form['slot']
    release_slot(slot)
    flash(f'Slot {slot} released', 'info')
    return redirect(url_for('slots'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)
