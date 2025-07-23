from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import json, os
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'supersecretkey'

USER_FILE = 'data/users.json'
TASKS_DIR = 'data'

def load_users():
    if not os.path.exists(USER_FILE):
        return []
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=4)

def get_tasks_file():
    return os.path.join(TASKS_DIR, f"tasks_{{session['username']}}.json")

def load_tasks():
    path = get_tasks_file()
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    path = get_tasks_file()
    with open(path, "w") as f:
        json.dump(tasks, f, indent=4)

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        users = load_users()
        for user in users:
            if user['username'] == data['username'] and user['password'] == data['password']:
                session['username'] = user['username']
                return redirect(url_for('home'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        users = load_users()
        if any(u['username'] == data['username'] for u in users):
            return render_template('signup.html', error="Username already exists")
        users.append({
            "username": data['username'],
            "password": data['password']
        })
        save_users(users)
        os.makedirs(TASKS_DIR, exist_ok=True)
        with open(os.path.join(TASKS_DIR, f"tasks_{data['username']}.json"), "w") as f:
            json.dump([], f)
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(load_tasks())

@app.route('/api/tasks', methods=['POST'])
def add_task():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    tasks = load_tasks()
    data = request.json
    new_task = {
        "id": max([t["id"] for t in tasks], default=0) + 1,
        "text": data.get("text", ""),
        "priority": data.get("priority", "low"),
        "dueDate": data.get("dueDate"),
        "completed": False,
        "createdAt": datetime.now().isoformat()
    }
    tasks.append(new_task)
    save_tasks(tasks)
    return jsonify(new_task), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    tasks = load_tasks()
    for task in tasks:
        if task['id'] == task_id:
            task.update(request.json)
            save_tasks(tasks)
            return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    tasks = load_tasks()
    tasks = [t for t in tasks if t['id'] != task_id]
    save_tasks(tasks)
    return jsonify({'success': True})

if __name__ == '__main__':
    os.makedirs(TASKS_DIR, exist_ok=True)
    app.run(debug=True)
