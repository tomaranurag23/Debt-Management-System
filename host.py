import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

# Create Flask app
app = Flask(__name__)
app.secret_key = 'dev_key_change_in_production'

# Database setup
DB_PATH = 'debt_tracker.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create debts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        amount REAL NOT NULL,
        interest_rate REAL NOT NULL,
        min_payment REAL NOT NULL,
        paid REAL DEFAULT 0.0,
        created_at TEXT NOT NULL
    )
    ''')
    
    # Create payments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        debt_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        date TEXT NOT NULL,
        FOREIGN KEY (debt_id) REFERENCES debts (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Create a simple template directory and index.html
def create_templates():
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    with open('templates/layout.html', 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Debt Manager</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #1a1a1a;
            color: #f0f0f0;
            margin: 0;
            padding: 0;
        }
        .container {
            width: 90%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .navbar {
            background-color: #333;
            padding: 10px 20px;
            margin-bottom: 20px;
        }
        .navbar a {
            color: white;
            text-decoration: none;
            margin-right: 15px;
        }
        .card {
            background-color: #2a2a2a;
            border-radius: 5px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            background-color: #6200ee;
            color: white;
            border: none;
            border-radius: 4px;
            text-decoration: none;
            cursor: pointer;
            font-size: 14px;
        }
        .btn-danger {
            background-color: #cf0000;
        }
        .btn-success {
            background-color: #00a86b;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        table, th, td {
            border: 1px solid #444;
        }
        th, td {
            padding: 10px;
            text-align: left;
        }
        th {
            background-color: #333;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
        }
        input, select {
            width: 100%;
            padding: 8px;
            border: 1px solid #444;
            border-radius: 4px;
            background-color: #333;
            color: white;
        }
        .alert {
            padding: 10px;
            margin-bottom: 15px;
            border-radius: 4px;
        }
        .alert-success {
            background-color: #00a86b33;
            border: 1px solid #00a86b;
        }
        .alert-danger {
            background-color: #cf000033;
            border: 1px solid #cf0000;
        }
        .progress-bar {
            height: 10px;
            background-color: #333;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .progress {
            height: 100%;
            background-color: #6200ee;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <a href="/">Dashboard</a>
        <a href="/debts">Debts</a>
        <a href="/debt/add">Add Debt</a>
    </div>

    <div class="container">
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert alert-{{ category }}">
                {{ message }}
              </div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>
</body>
</html>''')
    
    with open('templates/index.html', 'w') as f:
        f.write('''{% extends "layout.html" %}
{% block content %}
    <h1>Debt Management Dashboard</h1>
    
    {% if debts %}
        <div class="card">
            <h2>Debt Summary</h2>
            <p>Total Debt: ${{ total_debt }}</p>
            <p>Monthly Minimum: ${{ total_min_payment }}</p>
        </div>
        
        <div class="card">
            <h2>Your Debts</h2>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Balance</th>
                        <th>Interest Rate</th>
                        <th>Progress</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for debt in debts %}
                    <tr>
                        <td>{{ debt['name'] }}</td>
                        <td>${{ debt['balance'] }}</td>
                        <td>{{ debt['interest_rate'] }}%</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress" style="width: {{ debt['progress'] }}%"></div>
                            </div>
                            {{ debt['progress'] }}%
                        </td>
                        <td>
                            <a href="/debt/{{ debt['id'] }}" class="btn">View</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    {% else %}
        <div class="card">
            <h2>No debts found</h2>
            <p>Start by adding your first debt.</p>
            <a href="/debt/add" class="btn">Add Debt</a>
        </div>
    {% endif %}
{% endblock %}''')
    
    with open('templates/debts.html', 'w') as f:
        f.write('''{% extends "layout.html" %}
{% block content %}
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h1>Your Debts</h1>
        <a href="/debt/add" class="btn">Add Debt</a>
    </div>
    
    {% if debts %}
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Balance</th>
                    <th>Interest Rate</th>
                    <th>Min Payment</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for debt in debts %}
                <tr>
                    <td>{{ debt['name'] }}</td>
                    <td>${{ debt['balance'] }}</td>
                    <td>{{ debt['interest_rate'] }}%</td>
                    <td>${{ debt['min_payment'] }}</td>
                    <td>
                        <a href="/debt/{{ debt['id'] }}" class="btn">View</a>
                        <a href="/debt/{{ debt['id'] }}/edit" class="btn">Edit</a>
                        <a href="/debt/{{ debt['id'] }}/payment" class="btn btn-success">Pay</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    {% else %}
        <div class="card">
            <h2>No debts found</h2>
            <p>Start by adding your first debt.</p>
            <a href="/debt/add" class="btn">Add Debt</a>
        </div>
    {% endif %}
{% endblock %}''')
    
    with open('templates/add_debt.html', 'w') as f:
        f.write('''{% extends "layout.html" %}
{% block content %}
    <h1>Add New Debt</h1>
    
    <div class="card">
        <form method="post">
            <div class="form-group">
                <label for="name">Debt Name</label>
                <input type="text" id="name" name="name" required>
            </div>
            
            <div class="form-group">
                <label for="amount">Total Amount ($)</label>
                <input type="number" id="amount" name="amount" step="0.01" min="0.01" required>
            </div>
            
            <div class="form-group">
                <label for="interest_rate">Interest Rate (%)</label>
                <input type="number" id="interest_rate" name="interest_rate" step="0.01" min="0" required>
            </div>
            
            <div class="form-group">
                <label for="min_payment">Minimum Monthly Payment ($)</label>
                <input type="number" id="min_payment" name="min_payment" step="0.01" min="0.01" required>
            </div>
            
            <button type="submit" class="btn">Add Debt</button>
            <a href="/debts" style="margin-left: 10px;">Cancel</a>
        </form>
    </div>
{% endblock %}''')
    
    with open('templates/view_debt.html', 'w') as f:
        f.write('''{% extends "layout.html" %}
{% block content %}
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h1>{{ debt['name'] }}</h1>
        <div>
            <a href="/debt/{{ debt['id'] }}/payment" class="btn btn-success">Make Payment</a>
            <a href="/debt/{{ debt['id'] }}/edit" class="btn">Edit</a>
            <form method="post" action="/debt/{{ debt['id'] }}/delete" style="display: inline;">
                <button type="submit" class="btn btn-danger" onclick="return confirm('Are you sure you want to delete this debt?')">Delete</button>
            </form>
        </div>
    </div>
    
    <div class="card">
        <h2>Debt Information</h2>
        <p><strong>Total Amount:</strong> ${{ debt['amount'] }}</p>
        <p><strong>Current Balance:</strong> ${{ debt['balance'] }}</p>
        <p><strong>Interest Rate:</strong> {{ debt['interest_rate'] }}%</p>
        <p><strong>Minimum Payment:</strong> ${{ debt['min_payment'] }}</p>
        <p><strong>Created On:</strong> {{ debt['created_at'] }}</p>
        
        <h3>Progress</h3>
        <div class="progress-bar">
            <div class="progress" style="width: {{ debt['progress'] }}%"></div>
        </div>
        <p>{{ debt['progress'] }}% paid</p>
    </div>
    
    {% if payments %}
    <div class="card">
        <h2>Payment History</h2>
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Amount</th>
                </tr>
            </thead>
            <tbody>
                {% for payment in payments %}
                <tr>
                    <td>{{ payment['date'] }}</td>
                    <td>${{ payment['amount'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% else %}
    <div class="card">
        <h2>No Payment History</h2>
        <p>You haven't made any payments yet.</p>
        <a href="/debt/{{ debt['id'] }}/payment" class="btn btn-success">Make First Payment</a>
    </div>
    {% endif %}
{% endblock %}''')
    
    with open('templates/edit_debt.html', 'w') as f:
        f.write('''{% extends "layout.html" %}
{% block content %}
    <h1>Edit Debt</h1>
    
    <div class="card">
        <form method="post">
            <div class="form-group">
                <label for="name">Debt Name</label>
                <input type="text" id="name" name="name" value="{{ debt['name'] }}" required>
            </div>
            
            <div class="form-group">
                <label for="amount">Total Amount ($)</label>
                <input type="number" id="amount" name="amount" step="0.01" min="0.01" value="{{ debt['amount'] }}" required>
            </div>
            
            <div class="form-group">
                <label for="interest_rate">Interest Rate (%)</label>
                <input type="number" id="interest_rate" name="interest_rate" step="0.01" min="0" value="{{ debt['interest_rate'] }}" required>
            </div>
            
            <div class="form-group">
                <label for="min_payment">Minimum Monthly Payment ($)</label>
                <input type="number" id="min_payment" name="min_payment" step="0.01" min="0.01" value="{{ debt['min_payment'] }}" required>
            </div>
            
            <button type="submit" class="btn">Save Changes</button>
            <a href="/debt/{{ debt['id'] }}" style="margin-left: 10px;">Cancel</a>
        </form>
    </div>
{% endblock %}''')
    
    with open('templates/add_payment.html', 'w') as f:
        f.write('''{% extends "layout.html" %}
{% block content %}
    <h1>Make Payment</h1>
    <h2>{{ debt['name'] }}</h2>
    
    <div class="card">
        <h3>Debt Information</h3>
        <p><strong>Current Balance:</strong> ${{ debt['balance'] }}</p>
        <p><strong>Minimum Payment:</strong> ${{ debt['min_payment'] }}</p>
    </div>
    
    <div class="card">
        <form method="post">
            <div class="form-group">
                <label for="amount">Payment Amount ($)</label>
                <input type="number" id="amount" name="amount" step="0.01" min="0.01" value="{{ debt['min_payment'] }}" required>
            </div>
            
            <div class="form-group">
                <label for="date">Payment Date</label>
                <input type="date" id="date" name="date" value="{{ today }}" required>
            </div>
            
            <button type="submit" class="btn btn-success">Add Payment</button>
            <a href="/debt/{{ debt['id'] }}" style="margin-left: 10px;">Cancel</a>
        </form>
    </div>
{% endblock %}''')

# Routes
@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM debts')
    db_debts = cursor.fetchall()
    
    debts = []
    total_debt = 0
    total_min_payment = 0
    
    for debt in db_debts:
        balance = debt['amount'] - debt['paid']
        progress = round((debt['paid'] / debt['amount']) * 100, 1) if debt['amount'] > 0 else 0
        
        debts.append({
            'id': debt['id'],
            'name': debt['name'],
            'amount': debt['amount'],
            'balance': round(balance, 2),
            'interest_rate': debt['interest_rate'],
            'min_payment': debt['min_payment'],
            'progress': progress
        })
        
        total_debt += balance
        total_min_payment += debt['min_payment']
    
    conn.close()
    
    return render_template('index.html', 
                           debts=debts, 
                           total_debt=round(total_debt, 2),
                           total_min_payment=round(total_min_payment, 2))

@app.route('/debts')
def all_debts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM debts')
    db_debts = cursor.fetchall()
    
    debts = []
    
    for debt in db_debts:
        balance = debt['amount'] - debt['paid']
        
        debts.append({
            'id': debt['id'],
            'name': debt['name'],
            'balance': round(balance, 2),
            'interest_rate': debt['interest_rate'],
            'min_payment': debt['min_payment']
        })
    
    conn.close()
    
    return render_template('debts.html', debts=debts)

@app.route('/debt/add', methods=['GET', 'POST'])
def add_debt():
    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        interest_rate = float(request.form['interest_rate'])
        min_payment = float(request.form['min_payment'])
        created_at = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO debts (name, amount, interest_rate, min_payment, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, amount, interest_rate, min_payment, created_at))
        
        conn.commit()
        conn.close()
        
        flash(f'Debt "{name}" added successfully!', 'success')
        return redirect(url_for('all_debts'))
    
    return render_template('add_debt.html')

@app.route('/debt/<int:debt_id>')
def view_debt(debt_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM debts WHERE id = ?', (debt_id,))
    db_debt = cursor.fetchone()
    
    if not db_debt:
        flash('Debt not found', 'danger')
        return redirect(url_for('all_debts'))
    
    balance = db_debt['amount'] - db_debt['paid']
    progress = round((db_debt['paid'] / db_debt['amount']) * 100, 1) if db_debt['amount'] > 0 else 0
    
    debt = {
        'id': db_debt['id'],
        'name': db_debt['name'],
        'amount': round(db_debt['amount'], 2),
        'balance': round(balance, 2),
        'interest_rate': db_debt['interest_rate'],
        'min_payment': round(db_debt['min_payment'], 2),
        'paid': round(db_debt['paid'], 2),
        'progress': progress,
        'created_at': db_debt['created_at']
    }
    
    cursor.execute('SELECT * FROM payments WHERE debt_id = ? ORDER BY date DESC', (debt_id,))
    db_payments = cursor.fetchall()
    
    payments = []
    for payment in db_payments:
        payments.append({
            'id': payment['id'],
            'amount': round(payment['amount'], 2),
            'date': payment['date']
        })
    
    conn.close()
    
    return render_template('view_debt.html', debt=debt, payments=payments)

@app.route('/debt/<int:debt_id>/edit', methods=['GET', 'POST'])
def edit_debt(debt_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM debts WHERE id = ?', (debt_id,))
    db_debt = cursor.fetchone()
    
    if not db_debt:
        flash('Debt not found', 'danger')
        return redirect(url_for('all_debts'))
    
    if request.method == 'POST':
        name = request.form['name']
        amount = float(request.form['amount'])
        interest_rate = float(request.form['interest_rate'])
        min_payment = float(request.form['min_payment'])
        
        cursor.execute('''
        UPDATE debts
        SET name = ?, amount = ?, interest_rate = ?, min_payment = ?
        WHERE id = ?
        ''', (name, amount, interest_rate, min_payment, debt_id))
        
        conn.commit()
        conn.close()
        
        flash(f'Debt "{name}" updated successfully!', 'success')
        return redirect(url_for('view_debt', debt_id=debt_id))
    
    balance = db_debt['amount'] - db_debt['paid']
    
    debt = {
        'id': db_debt['id'],
        'name': db_debt['name'],
        'amount': db_debt['amount'],
        'balance': round(balance, 2),
        'interest_rate': db_debt['interest_rate'],
        'min_payment': db_debt['min_payment']
    }
    
    conn.close()
    
    return render_template('edit_debt.html', debt=debt)

@app.route('/debt/<int:debt_id>/delete', methods=['POST'])
def delete_debt(debt_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT name FROM debts WHERE id = ?', (debt_id,))
    debt = cursor.fetchone()
    
    if not debt:
        flash('Debt not found', 'danger')
        return redirect(url_for('all_debts'))
    
    # Delete associated payments
    cursor.execute('DELETE FROM payments WHERE debt_id = ?', (debt_id,))
    
    # Delete the debt
    cursor.execute('DELETE FROM debts WHERE id = ?', (debt_id,))
    
    conn.commit()
    conn.close()
    
    flash(f'Debt "{debt[0]}" deleted successfully!', 'success')
    return redirect(url_for('all_debts'))

@app.route('/debt/<int:debt_id>/payment', methods=['GET', 'POST'])
def add_payment(debt_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM debts WHERE id = ?', (debt_id,))
    db_debt = cursor.fetchone()
    
    if not db_debt:
        flash('Debt not found', 'danger')
        return redirect(url_for('all_debts'))
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        date = request.form['date']
        
        # Add the payment
        cursor.execute('''
        INSERT INTO payments (debt_id, amount, date)
        VALUES (?, ?, ?)
        ''', (debt_id, amount, date))
        
        # Update the total paid amount
        cursor.execute('''
        UPDATE debts
        SET paid = paid + ?
        WHERE id = ?
        ''', (amount, debt_id))
        
        conn.commit()
        conn.close()
        
        flash(f'Payment of ${amount:.2f} added successfully!', 'success')
        return redirect(url_for('view_debt', debt_id=debt_id))
    
    balance = db_debt['amount'] - db_debt['paid']
    
    debt = {
        'id': db_debt['id'],
        'name': db_debt['name'],
        'balance': round(balance, 2),
        'min_payment': round(db_debt['min_payment'], 2)
    }
    
    conn.close()
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_payment.html', debt=debt, today=today)

if __name__ == '__main__':
    # Initialize the database
    init_db()
    
    # Create templates
    create_templates()
    
    # Run the app
    app.run(debug=True)