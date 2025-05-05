import os
import base64
import io
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from debt_manager import DebtManager, Debt, Payment
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from datetime import datetime
import json
import numpy as np

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here'  # Change this in production

# Initialize DebtManager
debt_manager = DebtManager()

@app.route('/')
def index():
    """Render the home page with all debts"""
    debts = debt_manager.get_all_debts()
    
    # Calculate totals
    total_balance = sum(debt.current_balance for debt in debts)
    total_min_payment = sum(debt.min_payment for debt in debts)
    total_interest_paid = sum(debt.principal * (debt.interest_rate / 100) * (debt.total_paid / debt.principal) 
                              if debt.principal > 0 else 0 
                              for debt in debts)
    
    # Sort debts by different criteria for the dashboard
    highest_interest = sorted(debts, key=lambda x: x.interest_rate, reverse=True)
    highest_balance = sorted(debts, key=lambda x: x.current_balance, reverse=True)
    
    return render_template('index.html', 
                          debts=debts,
                          total_balance=total_balance,
                          total_min_payment=total_min_payment,
                          total_interest_paid=total_interest_paid,
                          highest_interest=highest_interest[:3] if highest_interest else [],
                          highest_balance=highest_balance[:3] if highest_balance else [])

@app.route('/debts')
def view_all_debts():
    """View all debts page"""
    debts = debt_manager.get_all_debts()
    return render_template('debts.html', debts=debts)

@app.route('/debt/add', methods=['GET', 'POST'])
def add_debt():
    """Add a new debt"""
    if request.method == 'POST':
        try:
            name = request.form['name']
            principal = float(request.form['principal'])
            interest_rate = float(request.form['interest_rate'])
            min_payment = float(request.form['min_payment'])
            
            # Validate inputs
            if principal <= 0:
                flash('Principal amount must be greater than zero', 'danger')
                return redirect(url_for('add_debt'))
            
            if interest_rate < 0:
                flash('Interest rate cannot be negative', 'danger')
                return redirect(url_for('add_debt'))
            
            if min_payment <= 0:
                flash('Minimum payment must be greater than zero', 'danger')
                return redirect(url_for('add_debt'))
            
            debt = Debt(id=None, 
                        name=name, 
                        principal=principal, 
                        interest_rate=interest_rate, 
                        min_payment=min_payment)
            
            debt_id = debt_manager.add_debt(debt)
            
            flash(f'Debt "{name}" added successfully!', 'success')
            return redirect(url_for('view_all_debts'))
            
        except ValueError as e:
            flash(f'Error adding debt: {str(e)}', 'danger')
            return redirect(url_for('add_debt'))
    
    return render_template('add_debt.html')

@app.route('/debt/<int:debt_id>')
def view_debt(debt_id):
    """View details of a specific debt"""
    debt = debt_manager.get_debt(debt_id)
    
    if not debt:
        flash(f'Debt with ID {debt_id} not found', 'danger')
        return redirect(url_for('view_all_debts'))
    
    payments = debt_manager.get_payments_for_debt(debt_id)
    
    # Generate payment chart
    payment_chart = None
    if payments:
        payment_chart = generate_payment_history_chart(payments)
    
    # Calculate statistics
    total_paid = sum(payment.amount for payment in payments)
    interest_paid = total_paid - (debt.principal - debt.current_balance)
    percent_paid = (debt.total_paid / debt.principal) * 100 if debt.principal > 0 else 0
    
    return render_template('view_debt.html', 
                          debt=debt, 
                          payments=payments,
                          payment_chart=payment_chart,
                          interest_paid=interest_paid,
                          percent_paid=percent_paid)

@app.route('/debt/<int:debt_id>/edit', methods=['GET', 'POST'])
def edit_debt(debt_id):
    """Edit a debt"""
    debt = debt_manager.get_debt(debt_id)
    
    if not debt:
        flash(f'Debt with ID {debt_id} not found', 'danger')
        return redirect(url_for('view_all_debts'))
    
    if request.method == 'POST':
        try:
            name = request.form['name']
            principal = float(request.form['principal'])
            interest_rate = float(request.form['interest_rate'])
            min_payment = float(request.form['min_payment'])
            
            # Update debt object
            debt.name = name
            debt.principal = principal
            debt.interest_rate = interest_rate
            debt.min_payment = min_payment
            
            # Save to database
            success = debt_manager.update_debt(debt)
            
            if success:
                flash(f'Debt "{name}" updated successfully!', 'success')
            else:
                flash('Error updating debt', 'danger')
                
            return redirect(url_for('view_debt', debt_id=debt_id))
            
        except ValueError as e:
            flash(f'Error updating debt: {str(e)}', 'danger')
            return redirect(url_for('edit_debt', debt_id=debt_id))
    
    return render_template('edit_debt.html', debt=debt)

@app.route('/debt/<int:debt_id>/delete', methods=['POST'])
def delete_debt(debt_id):
    """Delete a debt"""
    debt = debt_manager.get_debt(debt_id)
    
    if not debt:
        flash(f'Debt with ID {debt_id} not found', 'danger')
        return redirect(url_for('view_all_debts'))
    
    success = debt_manager.delete_debt(debt_id)
    
    if success:
        flash(f'Debt "{debt.name}" deleted successfully!', 'success')
    else:
        flash('Error deleting debt', 'danger')
        
    return redirect(url_for('view_all_debts'))

@app.route('/debt/<int:debt_id>/payment', methods=['GET', 'POST'])
def add_payment(debt_id):
    """Add a payment to a debt"""
    debt = debt_manager.get_debt(debt_id)
    
    if not debt:
        flash(f'Debt with ID {debt_id} not found', 'danger')
        return redirect(url_for('view_all_debts'))
    
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            payment_date = request.form['payment_date']
            
            # Validate inputs
            if amount <= 0:
                flash('Payment amount must be greater than zero', 'danger')
                return redirect(url_for('add_payment', debt_id=debt_id))
            
            # Create payment
            payment = Payment(id=None, 
                             debt_id=debt_id, 
                             amount=amount, 
                             payment_date=payment_date)
            
            payment_id = debt_manager.add_payment(payment)
            
            flash(f'Payment of ${amount:.2f} added successfully!', 'success')
            return redirect(url_for('view_debt', debt_id=debt_id))
            
        except ValueError as e:
            flash(f'Error adding payment: {str(e)}', 'danger')
            return redirect(url_for('add_payment', debt_id=debt_id))
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_payment.html', debt=debt, today=today)

@app.route('/debt/<int:debt_id>/plan')
def payment_plan(debt_id):
    """Generate and display a payment plan"""
    debt = debt_manager.get_debt(debt_id)
    
    if not debt:
        flash(f'Debt with ID {debt_id} not found', 'danger')
        return redirect(url_for('view_all_debts'))
    
    # Get strategy from query parameters, default to "minimum"
    strategy = request.args.get('strategy', 'minimum')
    
    # Generate payment plan
    plan_df = debt_manager.generate_payment_plan(debt_id, strategy)
    
    if plan_df.empty:
        flash('Unable to generate payment plan', 'danger')
        return redirect(url_for('view_debt', debt_id=debt_id))
    
    # Calculate summary statistics
    months_to_payoff = len(plan_df)
    total_interest = sum(plan_df['Interest'])
    total_payments = sum(plan_df['Payment'])
    
    # Generate visualization
    plan_chart = generate_payment_plan_chart(plan_df, debt.name)
    
    # Convert plan to HTML table (limited to first 24 months for display)
    plan_table = plan_df.head(24).to_html(classes='table table-dark table-hover', index=False)
    
    return render_template('payment_plan.html', 
                          debt=debt,
                          plan_chart=plan_chart,
                          plan_table=plan_table,
                          months_to_payoff=months_to_payoff,
                          total_interest=total_interest,
                          total_payments=total_payments,
                          strategy=strategy)

@app.route('/strategies')
def strategy_comparison():
    """Compare different debt payoff strategies"""
    extra_payment = request.args.get('extra', 0)
    
    try:
        extra_payment = float(extra_payment)
    except ValueError:
        extra_payment = 0
    
    # Get comparison results
    results = debt_manager.compare_payoff_strategies(extra_payment)
    
    if not results:
        flash('No debts found for comparison', 'danger')
        return redirect(url_for('index'))
    
    # Generate visualization
    comparison_chart = generate_strategy_comparison_chart(results)
    
    return render_template('strategies.html', 
                          results=results,
                          comparison_chart=comparison_chart,
                          extra_payment=extra_payment)

@app.route('/export_data/<int:debt_id>')
def export_data(debt_id):
    """Export debt payment plan data as CSV"""
    debt = debt_manager.get_debt(debt_id)
    
    if not debt:
        flash(f'Debt with ID {debt_id} not found', 'danger')
        return redirect(url_for('view_all_debts'))
    
    strategy = request.args.get('strategy', 'minimum')
    
    # Generate payment plan
    plan_df = debt_manager.generate_payment_plan(debt_id, strategy)
    
    if plan_df.empty:
        flash('Unable to generate payment plan for export', 'danger')
        return redirect(url_for('view_debt', debt_id=debt_id))
    
    # Convert to CSV
    csv_data = plan_df.to_csv(index=False)
    
    # Create response
    from flask import Response
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=payment_plan_{debt.name}_{strategy}.csv"}
    )

@app.route('/dashboard')
def dashboard():
    """Dashboard with overview of all debts"""
    debts = debt_manager.get_all_debts()
    
    if not debts:
        flash('No debts found', 'warning')
        return redirect(url_for('index'))
    
    # Generate dashboard charts
    debt_distribution_chart = generate_debt_distribution_chart(debts)
    interest_comparison_chart = generate_interest_comparison_chart(debts)
    
    # Calculate totals
    total_balance = sum(debt.current_balance for debt in debts)
    total_min_payment = sum(debt.min_payment for debt in debts)
    
    # Calculate minimum vs. accelerated payoff time
    min_months = max([len(debt_manager.generate_payment_plan(debt.id, "minimum")) 
                      for debt in debts]) if debts else 0
    acc_months = max([len(debt_manager.generate_payment_plan(debt.id, "accelerated")) 
                      for debt in debts]) if debts else 0
    
    return render_template('dashboard.html',
                          debts=debts,
                          debt_distribution_chart=debt_distribution_chart,
                          interest_comparison_chart=interest_comparison_chart,
                          total_balance=total_balance,
                          total_min_payment=total_min_payment,
                          min_months=min_months,
                          acc_months=acc_months)

# Helper functions for generating charts
def generate_payment_history_chart(payments):
    """Generate a payment history chart"""
    fig = Figure(figsize=(8, 4))
    ax = fig.add_subplot(1, 1, 1)
    
    dates = [payment.payment_date for payment in payments]
    amounts = [payment.amount for payment in payments]
    
    # Convert dates to datetime objects for plotting
    dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]
    
    ax.bar(dates, amounts, color='#6d28d9')
    ax.set_xlabel('Date')
    ax.set_ylabel('Amount ($)')
    ax.set_title('Payment History')
    ax.grid(True, alpha=0.3)
    
    # Rotate date labels
    fig.autofmt_xdate()
    
    # Set dark theme
    ax.set_facecolor('#1f2937')
    fig.patch.set_facecolor('#1f2937')
    ax.xaxis.label.set_color('#d1d5db')
    ax.yaxis.label.set_color('#d1d5db')
    ax.title.set_color('#d1d5db')
    ax.tick_params(colors='#d1d5db')
    ax.spines['bottom'].set_color('#4b5563')
    ax.spines['top'].set_color('#4b5563')
    ax.spines['left'].set_color('#4b5563')
    ax.spines['right'].set_color('#4b5563')
    
    # Convert to base64 string for embedding in HTML
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    string = base64.b64encode(buf.read()).decode('utf-8')
    
    return string

def generate_payment_plan_chart(plan_df, debt_name):
    """Generate a payment plan chart"""
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(1, 1, 1)
    
    # Plot balance over time
    ax.plot(plan_df['Month'], plan_df['Balance'], label='Balance', color='#ef4444')
    
    # Plot cumulative payments
    cumulative_payments = [sum(plan_df['Payment'][:i+1]) for i in range(len(plan_df))]
    ax.plot(plan_df['Month'], cumulative_payments, label='Payments Made', color='#10b981')
    
    # Plot cumulative interest
    cumulative_interest = [sum(plan_df['Interest'][:i+1]) for i in range(len(plan_df))]
    ax.plot(plan_df['Month'], cumulative_interest, label='Interest Paid', color='#f59e0b')
    
    ax.set_title(f'Debt Payoff Plan: {debt_name}')
    ax.set_xlabel('Months')
    ax.set_ylabel('Amount ($)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Set dark theme
    ax.set_facecolor('#1f2937')
    fig.patch.set_facecolor('#1f2937')
    ax.xaxis.label.set_color('#d1d5db')
    ax.yaxis.label.set_color('#d1d5db')
    ax.title.set_color('#d1d5db')
    ax.tick_params(colors='#d1d5db')
    ax.spines['bottom'].set_color('#4b5563')
    ax.spines['top'].set_color('#4b5563')
    ax.spines['left'].set_color('#4b5563')
    ax.spines['right'].set_color('#4b5563')
    
    # Convert to base64 string for embedding in HTML
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    string = base64.b64encode(buf.read()).decode('utf-8')
    
    return string

def generate_strategy_comparison_chart(results):
    """Generate a strategy comparison chart"""
    fig = Figure(figsize=(10, 6))
    ax = fig.add_subplot(1, 1, 1)
    
    # Extract data
    strategies = ['Avalanche', 'Snowball']
    months = [results['avalanche']['months'], results['snowball']['months']]
    interest = [results['avalanche']['interest_paid'], results['snowball']['interest_paid']]
    
    # Create grouped bar chart
    x = np.arange(len(strategies))
    width = 0.35
    
    ax.bar(x - width/2, months, width, label='Months to Payoff', color='#3b82f6')
    ax.bar(x + width/2, interest, width, label='Interest Paid ($)', color='#f59e0b')
    
    ax.set_xlabel('Strategy')
    ax.set_ylabel('Value')
    ax.set_title('Debt Payoff Strategy Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(strategies)
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Set dark theme
    ax.set_facecolor('#1f2937')
    fig.patch.set_facecolor('#1f2937')
    ax.xaxis.label.set_color('#d1d5db')
    ax.yaxis.label.set_color('#d1d5db')
    ax.title.set_color('#d1d5db')
    ax.tick_params(colors='#d1d5db')
    ax.spines['bottom'].set_color('#4b5563')
    ax.spines['top'].set_color('#4b5563')
    ax.spines['left'].set_color('#4b5563')
    ax.spines['right'].set_color('#4b5563')
    
    # Convert to base64 string for embedding in HTML
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    string = base64.b64encode(buf.read()).decode('utf-8')
    
    return string

def generate_debt_distribution_chart(debts):
    """Generate a pie chart of debt distribution"""
    if not debts:
        return None
        
    fig = Figure(figsize=(6, 6))
    ax = fig.add_subplot(1, 1, 1)
    
    # Extract data
    debt_names = [debt.name for debt in debts]
    balances = [debt.current_balance for debt in debts]
    
    # Colors
    colors = ['#3b82f6', '#10b981', '#f59e0b', '#6d28d9', '#ef4444', 
              '#8b5cf6', '#06b6d4', '#d946ef', '#f97316', '#14b8a6']
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(
        balances, 
        labels=None,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors[:len(debts)]
    )
    
    # Style autotexts
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)
    
    ax.set_title('Debt Distribution by Balance')
    ax.legend(wedges, debt_names, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    # Set dark theme
    fig.patch.set_facecolor('#1f2937')
    ax.set_facecolor('#1f2937')
    ax.title.set_color('#d1d5db')
    
    # Convert to base64 string for embedding in HTML
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    string = base64.b64encode(buf.read()).decode('utf-8')
    
    return string

def generate_interest_comparison_chart(debts):
    """Generate a bar chart comparing interest rates"""
    fig = Figure(figsize=(8, 5))
    ax = fig.add_subplot(1, 1, 1)
    
    # Extract data
    debt_names = [debt.name for debt in debts]
    interest_rates = [debt.interest_rate for debt in debts]
    
    # Sort by interest rate for better visualization
    sorted_data = sorted(zip(debt_names, interest_rates), key=lambda x: x[1], reverse=True)
    debt_names = [item[0] for item in sorted_data]
    interest_rates = [item[1] for item in sorted_data]
    
    # Create horizontal bar chart
    ax.barh(debt_names, interest_rates, color='#6d28d9')
    ax.set_xlabel('Interest Rate (%)')
    ax.set_title('Interest Rate Comparison')
    ax.grid(True, alpha=0.3, axis='x')
    
    # Add value labels
    for i, v in enumerate(interest_rates):
        ax.text(v + 0.1, i, f"{v}%", va='center', color='#d1d5db')
    
    # Set dark theme
    ax.set_facecolor('#1f2937')
    fig.patch.set_facecolor('#1f2937')
    ax.xaxis.label.set_color('#d1d5db')
    ax.yaxis.label.set_color('#d1d5db')
    ax.title.set_color('#d1d5db')
    ax.tick_params(colors='#d1d5db')
    ax.spines['bottom'].set_color('#4b5563')
    ax.spines['top'].set_color('#4b5563')
    ax.spines['left'].set_color('#4b5563')
    ax.spines['right'].set_color('#4b5563')
    
    # Convert to base64 string for embedding in HTML
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    string = base64.b64encode(buf.read()).decode('utf-8')
    
    return string

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
        
    # Create static/css directory if it doesn't exist
    if not os.path.exists('static/css'):
        os.makedirs('static/css')
        
    # Create static/js directory if it doesn't exist
    if not os.path.exists('static/js'):
        os.makedirs('static/js')
        
    app.run(debug=True)