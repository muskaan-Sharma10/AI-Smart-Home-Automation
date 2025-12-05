from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import json
import random
from datetime import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///smart_home.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    devices = db.relationship('Device', backref='owner', lazy=True)

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class AutomationRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    trigger_device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    trigger_condition = db.Column(db.String(100))
    action_device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    action_state = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Enhanced intent recognition with more sophisticated NLP
def recognize_intent(message):
    message = message.lower()
    intents = {
        'lights': ['light', 'lights', 'lamp', 'bright', 'dim', 'color'],
        'temperature': ['temperature', 'thermostat', 'heat', 'cool', 'warm'],
        'door': ['door', 'lock', 'unlock', 'entry'],
        'speaker': ['speaker', 'volume', 'music', 'play', 'pause', 'stop', 'sound', 'mute'],
        'fan': ['fan', 'speed', 'oscillate', 'swing'],
        'blinds': ['blind', 'blinds', 'shade', 'shades'],
        'camera': ['camera', 'record', 'snapshot', 'motion'],
        'outlet': ['outlet', 'plug', 'socket', 'smart plug'],
        'automation': ['automation', 'rule', 'schedule', 'routine']
    }
    
    for intent, keywords in intents.items():
        if any(word in message for word in keywords):
            return intent
    return 'unknown'

def handle_lights(message, user_id):
    device = Device.query.filter_by(user_id=user_id, type='light').first()
    if not device:
        return "No light device found.", None
    
    message = message.lower()
    
    # Extract brightness percentage if present
    brightness_match = re.search(r'(\d+)%?', message)
    
    # Handle brightness commands
    if brightness_match and any(word in message for word in ['brightness', 'dim', 'bright']):
        brightness = int(brightness_match.group(1))
        if 0 <= brightness <= 100:
            device.state = f'on_{brightness}%'
            db.session.commit()
            return f"Set {device.name} brightness to {brightness}%.", {'device_id': device.id, 'state': f'on_{brightness}%'}
        return "Please specify brightness between 0% and 100%.", None
    
    # Handle color commands (if supported)
    elif any(color in message for color in ['red', 'blue', 'green', 'yellow', 'purple', 'white']):
        color = next(c for c in ['red', 'blue', 'green', 'yellow', 'purple', 'white'] if c in message)
        device.state = f'on_{color}'
        db.session.commit()
        return f"Changed {device.name} color to {color}.", {'device_id': device.id, 'state': f'on_{color}'}
    
    # Basic on/off commands
    elif 'on' in message:
        device.state = 'on_100%'
        db.session.commit()
        return f"I've turned on the {device.name}.", {'device_id': device.id, 'state': 'on_100%'}
    elif 'off' in message:
        device.state = 'off'
        db.session.commit()
        return f"I've turned off the {device.name}.", {'device_id': device.id, 'state': 'off'}
    
    return f"The {device.name} is currently {device.state}. You can turn it on/off, adjust brightness, or change colors.", None

def handle_temperature(message, user_id):
    device = Device.query.filter_by(user_id=user_id, type='thermostat').first()
    if not device:
        return "No thermostat found.", None
        
    if 'set' in message.lower():
        try:
            temp = [int(s) for s in message.split() if s.isdigit()][0]
            device.state = f'{temp}°F'
            db.session.commit()
            return f"I've set the temperature to {temp}°F.", {'device_id': device.id, 'state': f'{temp}°F'}
        except:
            return "Please specify a temperature value.", None
    return f"The current temperature is {device.state}.", None

def handle_door(message, user_id):
    device = Device.query.filter_by(user_id=user_id, type='lock').first()
    if not device:
        return "No door lock found.", None
    
    message = message.lower()  # Convert message to lowercase once
        
    if 'lock' in message and 'unlock' not in message:  # Changed condition to avoid confusion
        device.state = 'locked'
        db.session.commit()
        return f"I've locked the {device.name}.", {'device_id': device.id, 'state': 'locked'}
    elif 'unlock' in message:  # Check for unlock specifically
        device.state = 'unlocked'
        db.session.commit()
        return f"I've unlocked the {device.name}.", {'device_id': device.id, 'state': 'unlocked'}
    
    # Status query
    return f"The {device.name} is currently {device.state}. Would you like me to lock or unlock it?", None

def handle_speaker(message, user_id):
    device = Device.query.filter_by(user_id=user_id, type='speaker').first()
    if not device:
        return "No speaker found.", None
        
    message = message.lower()
    
    # Handle power commands
    if 'turn on' in message or 'power on' in message:
        device.state = 'on'
        db.session.commit()
        return f"I've turned on the {device.name}.", {'device_id': device.id, 'state': 'on'}
    elif 'turn off' in message or 'power off' in message:
        device.state = 'off'
        db.session.commit()
        return f"I've turned off the {device.name}.", {'device_id': device.id, 'state': 'off'}
    
    # Handle playback commands
    elif 'play' in message:
        device.state = 'playing'
        db.session.commit()
        return f"Playing music on {device.name}.", {'device_id': device.id, 'state': 'playing'}
    elif 'pause' in message:
        device.state = 'paused'
        db.session.commit()
        return f"Paused music on {device.name}.", {'device_id': device.id, 'state': 'paused'}
    elif 'stop' in message:
        device.state = 'stopped'
        db.session.commit()
        return f"Stopped music on {device.name}.", {'device_id': device.id, 'state': 'stopped'}
    elif 'next' in message:
        return f"Skipped to next track on {device.name}.", {'device_id': device.id, 'state': device.state}
    elif 'previous' in message or 'prev' in message:
        return f"Skipped to previous track on {device.name}.", {'device_id': device.id, 'state': device.state}
    
    # Handle volume commands
    elif 'volume' in message:
        try:
            volume = [int(s) for s in message.split() if s.isdigit()][0]
            if 0 <= volume <= 100:
                device.state = f'volume_{volume}'
                db.session.commit()
                return f"Set {device.name} volume to {volume}%.", {'device_id': device.id, 'state': f'volume_{volume}'}
            else:
                return "Please specify a volume level between 0 and 100.", None
        except:
            return "Please specify a valid volume level (0-100).", None
    elif 'mute' in message:
        device.state = 'muted'
        db.session.commit()
        return f"Muted {device.name}.", {'device_id': device.id, 'state': 'muted'}
    elif 'unmute' in message:
        device.state = 'on'
        db.session.commit()
        return f"Unmuted {device.name}.", {'device_id': device.id, 'state': 'on'}
    
    return f"The {device.name} is currently {device.state}. You can control power, playback, or volume.", None

def handle_outlet(message, user_id):
    device = Device.query.filter_by(user_id=user_id, type='outlet').first()
    if not device:
        return "No smart plug found.", None
        
    message = message.lower()
    
    # Handle power commands
    if 'turn on' in message or 'power on' in message:
        device.state = 'on'
        db.session.commit()
        return f"I've turned on the {device.name}.", {'device_id': device.id, 'state': 'on'}
    elif 'turn off' in message or 'power off' in message:
        device.state = 'off'
        db.session.commit()
        return f"I've turned off the {device.name}.", {'device_id': device.id, 'state': 'off'}
    
    # Handle scheduling commands (optional feature)
    elif 'schedule' in message:
        try:
            # Basic time extraction (you can enhance this)
            time_str = re.search(r'\d{1,2}(?::\d{2})?\s*(?:am|pm)?', message, re.I)
            if time_str:
                return f"I'll schedule the {device.name} for {time_str.group(0)}.", None
            else:
                return "Please specify a time for scheduling.", None
        except:
            return "I couldn't understand the scheduling time.", None
    
    # Status query
    return f"The {device.name} is currently {device.state}.", None

def handle_fan(message, user_id):
    device = Device.query.filter_by(user_id=user_id, type='fan').first()
    if not device:
        return "No fan found.", None
        
    message = message.lower()
    
    # Handle power commands
    if 'turn on' in message:
        device.state = 'on_medium'
        db.session.commit()
        return f"Turned on the {device.name} at medium speed.", {'device_id': device.id, 'state': 'on_medium'}
    elif 'turn off' in message:
        device.state = 'off'
        db.session.commit()
        return f"Turned off the {device.name}.", {'device_id': device.id, 'state': 'off'}
    
    # Handle speed commands
    elif 'high' in message or 'fast' in message:
        device.state = 'on_high'
        db.session.commit()
        return f"Set {device.name} to high speed.", {'device_id': device.id, 'state': 'on_high'}
    elif 'medium' in message:
        device.state = 'on_medium'
        db.session.commit()
        return f"Set {device.name} to medium speed.", {'device_id': device.id, 'state': 'on_medium'}
    elif 'low' in message or 'slow' in message:
        device.state = 'on_low'
        db.session.commit()
        return f"Set {device.name} to low speed.", {'device_id': device.id, 'state': 'on_low'}
    
    # Handle oscillation
    elif 'oscillate' in message or 'swing' in message:
        if 'stop' in message:
            device.state = 'on_fixed'
            db.session.commit()
            return f"Stopped {device.name} oscillation.", {'device_id': device.id, 'state': 'on_fixed'}
        else:
            device.state = 'on_oscillating'
            db.session.commit()
            return f"Started {device.name} oscillation.", {'device_id': device.id, 'state': 'on_oscillating'}
    
    return f"The {device.name} is currently {device.state}. You can control power, speed, and oscillation.", None

def handle_blinds(message, user_id):
    device = Device.query.filter_by(user_id=user_id, type='blinds').first()
    if not device:
        return "No blinds found.", None
        
    message = message.lower()
    
    # Handle open/close commands
    if 'open' in message:
        if 'partially' in message or 'half' in message:
            device.state = 'half_open'
            db.session.commit()
            return f"Partially opened the {device.name}.", {'device_id': device.id, 'state': 'half_open'}
        device.state = 'open'
        db.session.commit()
        return f"Opened the {device.name}.", {'device_id': device.id, 'state': 'open'}
    elif 'close' in message:
        device.state = 'closed'
        db.session.commit()
        return f"Closed the {device.name}.", {'device_id': device.id, 'state': 'closed'}
    
    # Handle percentage commands
    percentage_match = re.search(r'(\d+)%?', message)
    if percentage_match:
        percentage = int(percentage_match.group(1))
        if 0 <= percentage <= 100:
            device.state = f'open_{percentage}%'
            db.session.commit()
            return f"Set {device.name} to {percentage}% open.", {'device_id': device.id, 'state': f'open_{percentage}%'}
        return "Please specify a percentage between 0% and 100%.", None
    
    return f"The {device.name} are currently {device.state}. You can open/close them or set a specific percentage.", None

def handle_camera(message, user_id):
    device = Device.query.filter_by(user_id=user_id, type='camera').first()
    if not device:
        return "No camera found.", None
        
    message = message.lower()
    
    # Handle power commands
    if 'turn on' in message:
        device.state = 'recording'
        db.session.commit()
        return f"Started recording on {device.name}.", {'device_id': device.id, 'state': 'recording'}
    elif 'turn off' in message:
        device.state = 'off'
        db.session.commit()
        return f"Stopped recording on {device.name}.", {'device_id': device.id, 'state': 'off'}
    
    # Handle recording commands
    elif 'start recording' in message:
        device.state = 'recording'
        db.session.commit()
        return f"Started recording on {device.name}.", {'device_id': device.id, 'state': 'recording'}
    elif 'stop recording' in message:
        device.state = 'standby'
        db.session.commit()
        return f"Stopped recording on {device.name}.", {'device_id': device.id, 'state': 'standby'}
    elif 'take picture' in message or 'snapshot' in message:
        device.state = 'snapshot'
        db.session.commit()
        return f"Took a snapshot with {device.name}.", {'device_id': device.id, 'state': 'snapshot'}
    
    # Handle motion detection
    elif 'motion detection' in message:
        if 'enable' in message or 'on' in message:
            device.state = 'motion_detection'
            db.session.commit()
            return f"Enabled motion detection on {device.name}.", {'device_id': device.id, 'state': 'motion_detection'}
        elif 'disable' in message or 'off' in message:
            device.state = 'standby'
            db.session.commit()
            return f"Disabled motion detection on {device.name}.", {'device_id': device.id, 'state': 'standby'}
    
    return f"The {device.name} is currently {device.state}. You can control recording, take snapshots, or toggle motion detection.", None

@app.route('/')
@login_required
def home():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', devices=devices)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        
        user = User(username=username)
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()
        
        # Create default devices for the new user
        devices = [
            Device(name="Living Room Light", type="light", state="off", user_id=user.id),
            Device(name="Home Thermostat", type="thermostat", state="72°F", user_id=user.id),
            Device(name="Front Door Lock", type="lock", state="locked", user_id=user.id),
            Device(name="Living Room Camera", type="camera", state="off", user_id=user.id),
            Device(name="Living Room Speaker", type="speaker", state="off", user_id=user.id),
            Device(name="Bedroom Fan", type="fan", state="off", user_id=user.id),
            Device(name="Living Room Blinds", type="blinds", state="closed", user_id=user.id),
            Device(name="Kitchen Outlet", type="outlet", state="off", user_id=user.id)
        ]
        
        for device in devices:
            db.session.add(device)
        db.session.commit()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.json
        user_message = data['message']
        
        intent = recognize_intent(user_message)
        device_update = None
        
        handlers = {
            'lights': handle_lights,
            'temperature': handle_temperature,
            'door': handle_door,
            'speaker': handle_speaker,
            'fan': handle_fan,
            'blinds': handle_blinds,
            'camera': handle_camera,
            'outlet': handle_outlet
        }
        
        if intent in handlers:
            response, device_update = handlers[intent](user_message, current_user.id)
        elif intent == 'automation':
            response = handle_automation(user_message, current_user.id)
        else:
            response = "I'm not sure how to help with that. You can control these devices: lights, temperature, doors, speakers, fans, blinds, cameras, and outlets."

        return jsonify({
            'response': response,
            'device_update': device_update
        })
    except Exception as e:
        print(f"Error in chat route: {str(e)}")
        return jsonify({
            'response': "Sorry, there was an error processing your request.",
            'device_update': None
        }), 500

@app.route('/devices', methods=['GET', 'POST'])
@login_required
def devices():  # Changed from manage_devices to devices
    if request.method == 'POST':
        if request.is_json:
            data = request.json
            name = data.get('name')
            device_type = data.get('type')
        else:
            name = request.form.get('name')
            device_type = request.form.get('type')
            
        device = Device(name=name, type=device_type, state='off', user_id=current_user.id)
        db.session.add(device)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('devices'))
        
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('devices.html', devices=devices)

@app.route('/devices/<int:device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    try:
        device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()
        if not device:
            return jsonify({'success': False, 'error': 'Device not found'}), 404
        
        db.session.delete(device)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting device {device_id}: {str(e)}")  # For server logs
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/devices/<int:device_id>', methods=['PUT'])
@login_required
def update_device(device_id):
    device = Device.query.filter_by(id=device_id, user_id=current_user.id).first()
    if not device:
        return jsonify({'error': 'Device not found'}), 404

    data = request.json
    device.name = data.get('name', device.name)
    device.type = data.get('type', device.type)
    db.session.commit()

    return jsonify({
        'id': device.id,
        'name': device.name,
        'type': device.type,
        'state': device.state
    })

@app.route('/automation', methods=['GET', 'POST'])
@login_required
def automation():
    if request.method == 'POST':
        name = request.form.get('name')
        trigger_device_id = request.form.get('trigger_device')
        trigger_condition = request.form.get('trigger_condition')
        action_device_id = request.form.get('action_device')
        action_state = request.form.get('action_state')
        
        rule = AutomationRule(
            name=name,
            trigger_device_id=trigger_device_id,
            trigger_condition=trigger_condition,
            action_device_id=action_device_id,
            action_state=action_state,
            user_id=current_user.id
        )
        db.session.add(rule)
        db.session.commit()
        return redirect(url_for('automation'))
        
    rules = AutomationRule.query.filter_by(user_id=current_user.id).all()
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return render_template('automation.html', rules=rules, devices=devices)

def create_default_devices():
    user = User.query.first()
    if user and not Device.query.filter_by(user_id=user.id).first():
        devices = [
            Device(name="Living Room Light", type="light", state="off", user_id=user.id),
            Device(name="Home Thermostat", type="thermostat", state="72°F", user_id=user.id),
            Device(name="Front Door Lock", type="lock", state="locked", user_id=user.id),
            Device(name="Living Room Camera", type="camera", state="off", user_id=user.id),
            Device(name="Living Room Speaker", type="speaker", state="off", user_id=user.id),
            Device(name="Bedroom Fan", type="fan", state="off", user_id=user.id),
            Device(name="Living Room Blinds", type="blinds", state="closed", user_id=user.id),
            Device(name="Kitchen Outlet", type="outlet", state="off", user_id=user.id)
        ]
        
        for device in devices:
            db.session.add(device)
        db.session.commit()

@app.route('/get_devices')
@login_required
def get_devices():
    devices = Device.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': device.id,
        'name': device.name,
        'type': device.type,
        'state': device.state
    } for device in devices])

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
