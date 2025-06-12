from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = "84a325623c47c1932a6aa053c1f20e9e"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.String(50))
    start = db.Column(db.String(50), nullable=False)
    end = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer)
    registrations = db.relationship('Registration', backref='event', lazy=True)

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(50))
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    events = Event.query.all()
    events_json = [
        {
            'id': event.id,
            'title': event.title,
            'start': f"{event.date}T{event.start}",
            'end': f"{event.date}T{event.end}",
            'url': f"/register/{event.id}"  # ✅ This enables clicking
        }
        for event in events
    ]
    return render_template('index.html', events_json=json.dumps(events_json))


@app.route('/register/<int:event_id>', methods=['GET', 'POST'])
def register(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if len(event.registrations) >= event.capacity:
            return "Event Full"
        reg = Registration(name=name, email=email, event_id=event.id)
        db.session.add(reg)
        db.session.commit()
        return render_template("confirmation.html", name=name, event=event)
    return render_template('register.html', event=event)


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['admin'] = True
            return redirect('/admin')
        else:
            flash('Invalid credentials', 'danger')
    return render_template('admin_login.html')

@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/admin_login')
    events = Event.query.all()
    return render_template('admin.html', events=events)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if not session.get('admin'):
        return redirect('/admin_login')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        start = request.form['start']
        end = request.form['end']
        capacity = int(request.form['capacity'])
        new_event = Event(
            title=title,
            description=description,
            date=date,
            start=start,
            end=end,
            capacity=capacity
        )
        db.session.add(new_event)
        db.session.commit()
        return redirect('/admin')
    return render_template('create_event.html')

@app.route('/attendees/<int:event_id>')
def attendees(event_id):
    if not session.get('admin'):
        return redirect('/admin_login')
    event = Event.query.get_or_404(event_id)
    return render_template('attendees.html', attendees=event.registrations)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
