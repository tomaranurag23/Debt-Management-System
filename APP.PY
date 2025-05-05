import os
import sqlite3
import datetime
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd
import matplotlib.pyplot as plt
import time
from dateutil.relativedelta import relativedelta


@dataclass
class Debt:
    id: Optional[int]
    name: str
    principal: float
    interest_rate: float
    min_payment: float
    total_paid: float = 0.0
    creation_date: str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    @property
    def current_balance(self):
        return self.principal - self.total_paid
    
    @property
    def monthly_interest(self):
        return self.current_balance * (self.interest_rate / 12 / 100)
    
    def calculate_payoff_date(self):
        """Calculate the estimated payoff date based on minimum payments"""
        if self.current_balance <= 0:
            return "Already paid off"
            
        # Simple calculation for payoff time in months
        balance = self.current_balance
        monthly_payment = self.min_payment
        interest_rate_monthly = self.interest_rate / 12 / 100
        
        # If minimum payment doesn't cover interest, it will never be paid off
        if monthly_payment <= balance * interest_rate_monthly:
            return "Never (min payment too low)"
        
        months = 0
        today = datetime.datetime.now()
        
        while balance > 0 and months < 1200:  # Cap at 100 years
            months += 1
            interest = balance * interest_rate_monthly
            principal_payment = monthly_payment - interest
            
            if principal_payment <= 0:
                return "Never (min payment too low)"
                
            balance -= principal_payment
            
            if balance <= 0:
                break
        
        payoff_date = today + relativedelta(months=months)
        years = months // 12
        remaining_months = months % 12
        
        time_to_payoff = ""
        if years > 0:
            time_to_payoff += f"{years} year{'s' if years != 1 else ''}"
            if remaining_months > 0:
                time_to_payoff += f", {remaining_months} month{'s' if remaining_months != 1 else ''}"
        else:
            time_to_payoff = f"{months} month{'s' if months != 1 else ''}"
        
        return {
            "date": payoff_date.strftime("%Y-%m-%d"),
            "months": months,
            "time_string": time_to_payoff
        }


@dataclass
class Payment:
    id: Optional[int]
    debt_id: int
    amount: float
    payment_date: str = datetime.datetime.now().strftime("%Y-%m-%d")


class DebtManager:
    def __init__(self, db_path="debt_management.db"):
        self.db_path = db_path
        self.initialize_db()
    
    def initialize_db(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create Debts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            principal REAL NOT NULL,
            interest_rate REAL NOT NULL,
            min_payment REAL NOT NULL,
            total_paid REAL DEFAULT 0.0,
            creation_date TEXT NOT NULL
        );
        ''')
        
        # Create Payments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debt_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            FOREIGN KEY (debt_id) REFERENCES debts (id)
        );
        ''')
        
        conn.commit()
        conn.close()
    
    def add_debt(self, debt: Debt) -> int:
        """Add a new debt to the database"""
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO debts (name, principal, interest_rate, min_payment, total_paid, creation_date)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (debt.name, debt.principal, debt.interest_rate, debt.min_payment, debt.total_paid, debt.creation_date))
        
        debt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Operation completed in {execution_time:.4f} seconds")
        
        return debt_id
    
    def update_debt(self, debt: Debt) -> bool:
        """Update debt information"""
        start_time = time.time()
        
        if debt.id is None:
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Operation failed in {execution_time:.4f} seconds: No debt ID provided")
            return False
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE debts
        SET name = ?, principal = ?, interest_rate = ?, min_payment = ?, total_paid = ?
        WHERE id = ?
        ''', (debt.name, debt.principal, debt.interest_rate, debt.min_payment, debt.total_paid, debt.id))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Operation completed in {execution_time:.4f} seconds")
        
        return success
    
    def get_debt(self, debt_id: int) -> Optional[Debt]:
        """Get a debt by its ID"""
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory for column names
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM debts WHERE id = ?', (debt_id,))
        debt_data = cursor.fetchone()
        conn.close()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        if debt_data:
            debt = Debt(
                id=debt_data['id'],
                name=debt_data['name'],
                principal=debt_data['principal'],
                interest_rate=debt_data['interest_rate'],
                min_payment=debt_data['min_payment'],
                total_paid=debt_data['total_paid'],
                creation_date=debt_data['creation_date']
            )
            print(f"Debt retrieved in {execution_time:.4f} seconds")
            return debt
        
        print(f"Debt not found in {execution_time:.4f} seconds")
        return None
    
    def get_all_debts(self) -> List[Debt]:
        """Get all debts"""
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory for column names
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM debts')
        debts_data = cursor.fetchall()
        conn.close()
        
        debts = []
        for data in debts_data:
            debt = Debt(
                id=data['id'],
                name=data['name'],
                principal=data['principal'],
                interest_rate=data['interest_rate'],
                min_payment=data['min_payment'],
                total_paid=data['total_paid'],
                creation_date=data['creation_date']
            )
            debts.append(debt)
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Retrieved {len(debts)} debts in {execution_time:.4f} seconds")
        
        return debts
    
    def delete_debt(self, debt_id: int) -> bool:
        """Delete a debt and its associated payments"""
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete associated payments first
        cursor.execute('DELETE FROM payments WHERE debt_id = ?', (debt_id,))
        
        # Delete the debt
        cursor.execute('DELETE FROM debts WHERE id = ?', (debt_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Deletion completed in {execution_time:.4f} seconds. Success: {success}")
        
        return success
    
    def add_payment(self, payment: Payment) -> int:
        """Add a payment to a debt"""
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Add the payment
        cursor.execute('''
        INSERT INTO payments (debt_id, amount, payment_date)
        VALUES (?, ?, ?)
        ''', (payment.debt_id, payment.amount, payment.payment_date))
        
        payment_id = cursor.lastrowid
        
        # Update the total paid amount for the debt
        cursor.execute('''
        UPDATE debts
        SET total_paid = total_paid + ?
        WHERE id = ?
        ''', (payment.amount, payment.debt_id))
        
        conn.commit()
        conn.close()
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Payment added in {execution_time:.4f} seconds")
        
        return payment_id
    
    def get_payments_for_debt(self, debt_id: int) -> List[Payment]:
        """Get all payments for a specific debt"""
        start_time = time.time()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable row factory for column names
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM payments WHERE debt_id = ? ORDER BY payment_date', (debt_id,))
        payments_data = cursor.fetchall()
        conn.close()
        
        payments = []
        for data in payments_data:
            payment = Payment(
                id=data['id'],
                debt_id=data['debt_id'],
                amount=data['amount'],
                payment_date=data['payment_date']
            )
            payments.append(payment)
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Retrieved {len(payments)} payments in {execution_time:.4f} seconds")
        
        return payments
    
    def generate_payment_plan(self, debt_id: int, strategy="minimum") -> pd.DataFrame:
        """Generate a payment plan based on a strategy
        
        Strategies:
        - minimum: Only pay the minimum payment
        - snowball: Pay extra after minimum payments (smallest balance first)
        - avalanche: Pay extra after minimum payments (highest interest first)
        """
        start_time = time.time()
        
        debt = self.get_debt(debt_id)
        if not debt:
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Failed to generate payment plan in {execution_time:.4f} seconds: Debt not found")
            return pd.DataFrame()
        
        # Create a basic minimum payment plan
        balance = debt.current_balance
        months = []
        balances = []
        interests = []
        payments = []
        
        month = 0
        
        while balance > 0 and month < 360:  # Cap at 30 years
            month += 1
            monthly_interest = balance * (debt.interest_rate / 12 / 100)
            interest_for_month = monthly_interest
            
            if strategy == "minimum":
                payment = max(debt.min_payment, monthly_interest + 1)  # Ensure we pay at least interest + something
            else:
                # Other strategies would be implemented here
                payment = max(debt.min_payment, monthly_interest + 50)  # Just an example
            
            if payment > balance + interest_for_month:
                payment = balance + interest_for_month
                
            balance = balance + interest_for_month - payment
            
            months.append(month)
            interests.append(interest_for_month)
            payments.append(payment)
            balances.append(balance)
            
            if balance <= 0:
                break
        
        # Create a DataFrame for the payment plan
        data = {
            'Month': months,
            'Payment': payments,
            'Interest': interests,
            'Balance': balances
        }
        
        result = pd.DataFrame(data)
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Payment plan generated in {execution_time:.4f} seconds with {len(months)} months")
        
        return result
    
    def compare_payoff_strategies(self, extra_payment=0) -> dict:
        """Compare different debt payoff strategies and return results"""
        start_time = time.time()
        
        debts = self.get_all_debts()
        
        if not debts:
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Failed to compare strategies in {execution_time:.4f} seconds: No debts found")
            return {}
        
        # Collect total principal and minimum payments
        total_principal = sum(debt.current_balance for debt in debts)
        total_min_payment = sum(debt.min_payment for debt in debts)
        
        # Add the extra payment
        total_payment = total_min_payment + extra_payment
        
        # Simulate avalanche method (highest interest first)
        sorted_by_interest = sorted(debts, key=lambda x: x.interest_rate, reverse=True)
        avalanche_months, avalanche_interest = self._simulate_payoff(sorted_by_interest, total_payment)
        
        # Simulate snowball method (lowest balance first)
        sorted_by_balance = sorted(debts, key=lambda x: x.current_balance)
        snowball_months, snowball_interest = self._simulate_payoff(sorted_by_balance, total_payment)
        
        result = {
            'total_principal': total_principal,
            'avalanche': {
                'months': avalanche_months,
                'interest_paid': avalanche_interest,
                'total_paid': total_principal + avalanche_interest
            },
            'snowball': {
                'months': snowball_months,
                'interest_paid': snowball_interest,
                'total_paid': total_principal + snowball_interest
            }
        }
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Strategy comparison completed in {execution_time:.4f} seconds")
        
        return result
    
    def _simulate_payoff(self, debts: List[Debt], total_payment: float) -> tuple:
        """Simulate a debt payoff strategy and return months and interest paid"""
        start_time = time.time()
        
        # Create copies to avoid modifying the original objects
        debt_copies = [
            Debt(
                id=debt.id,
                name=debt.name,
                principal=debt.principal,
                interest_rate=debt.interest_rate,
                min_payment=debt.min_payment,
                total_paid=debt.total_paid,
                creation_date=debt.creation_date
            )
            for debt in debts
        ]
        
        months = 0
        total_interest = 0
        
        while debt_copies and months < 1200:  # Cap at 100 years
            months += 1
            payment_remaining = total_payment
            
            # Pay minimum payments first
            for debt in debt_copies[:]:
                balance = debt.current_balance
                if balance <= 0:
                    debt_copies.remove(debt)
                    continue
                
                interest = balance * (debt.interest_rate / 12 / 100)
                total_interest += interest
                
                balance += interest
                min_payment = min(debt.min_payment, balance)
                
                if payment_remaining >= min_payment:
                    balance -= min_payment
                    payment_remaining -= min_payment
                else:
                    balance -= payment_remaining
                    payment_remaining = 0
                
                debt.total_paid = debt.principal - balance
            
            # Apply remaining payment to the first debt in the strategy
            for debt in debt_copies:
                if debt.current_balance > 0 and payment_remaining > 0:
                    payment = min(payment_remaining, debt.current_balance)
                    debt.total_paid += payment
                    payment_remaining -= payment
                    break
            
            # Check if all debts are paid off
            if all(debt.current_balance <= 0 for debt in debt_copies):
                break
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Payoff simulation completed in {execution_time:.4f} seconds over {months} months")
        
        return months, total_interest
    
    def visualize_payment_plan(self, debt_id: int, strategy="minimum"):
        """Visualize a payment plan"""
        start_time = time.time()
        
        plan_df = self.generate_payment_plan(debt_id, strategy)
        debt = self.get_debt(debt_id)
        
        if plan_df.empty or not debt:
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"Failed to visualize payment plan in {execution_time:.4f} seconds: No data available")
            return
        
        # Create the visualization
        plt.figure(figsize=(10, 6))
        
        # Plot balance over time
        plt.plot(plan_df['Month'], plan_df['Balance'], label='Balance', color='red')
        
        # Plot cumulative payments
        cumulative_payments = [sum(plan_df['Payment'][:i+1]) for i in range(len(plan_df))]
        plt.plot(plan_df['Month'], cumulative_payments, label='Payments Made', color='green')
        
        # Plot cumulative interest
        cumulative_interest = [sum(plan_df['Interest'][:i+1]) for i in range(len(plan_df))]
        plt.plot(plan_df['Month'], cumulative_interest, label='Interest Paid', color='orange')
        
        plt.title(f'Debt Payoff Plan: {debt.name}')
        plt.xlabel('Months')
        plt.ylabel('Amount ($)')
        plt.legend()
        plt.grid(True)
        
        # Save the plot to a file
        plt.savefig(f'debt_plan_{debt_id}.png')
        plt.close()
        
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Visualization completed in {execution_time:.4f} seconds")
        
        print(f"Payment plan visualization saved to debt_plan_{debt_id}.png")


class DebtManagementCLI:
    def __init__(self):
        self.debt_manager = DebtManager()
        
    def display_menu(self):
        """Display the main menu"""
        print("\n===== Debt Management System =====")
        print("1. View all debts")
        print("2. Add a new debt")
        print("3. Make a payment")
        print("4. View debt details")
        print("5. Generate payment plan")
        print("6. Compare payoff strategies")
        print("7. Delete a debt")
        print("8. Exit")
        print("==================================")
        
    def run(self):
        """Run the CLI application"""
        print("Welcome to the Debt Management System!")
        
        while True:
            self.display_menu()
            choice = input("Enter your choice (1-8): ")
            
            start_time = time.time()
            
            if choice == '1':
                self.view_all_debts()
            elif choice == '2':
                self.add_debt()
            elif choice == '3':
                self.make_payment()
            elif choice == '4':
                self.view_debt_details()
            elif choice == '5':
                self.generate_payment_plan()
            elif choice == '6':
                self.compare_strategies()
            elif choice == '7':
                self.delete_debt()
            elif choice == '8':
                print("Thank you for using the Debt Management System. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")
            
            end_time = time.time()
            execution_time = end_time - start_time
            print(f"\nOperation completed in {execution_time:.4f} seconds")
    
    def view_all_debts(self):
        """Display all debts"""
        debts = self.debt_manager.get_all_debts()
        
        if not debts:
            print("No debts found.")
            return
        
        print("\n===== Your Debts =====")
        print(f"{'ID':<5} {'Name':<20} {'Balance':<15} {'Interest':<10} {'Min Payment':<15} {'Time to Payoff':<25}")
        print("-" * 90)
        
        for debt in debts:
            payoff_info = debt.calculate_payoff_date()
            if isinstance(payoff_info, dict):
                payoff_time = payoff_info["time_string"]
            else:
                payoff_time = payoff_info
                
            print(f"{debt.id:<5} {debt.name:<20} ${debt.current_balance:<14.2f} {debt.interest_rate:<10.2f}% ${debt.min_payment:<14.2f} {payoff_time:<25}")
    
    def add_debt(self):
        """Add a new debt"""
        name = input("Enter debt name: ")
        
        try:
            principal = float(input("Enter principal amount: $"))
            interest_rate = float(input("Enter annual interest rate (%): "))
            min_payment = float(input("Enter minimum monthly payment: $"))
        except ValueError:
            print("Invalid input. Please enter numeric values.")
            return
        
        debt = Debt(id=None, name=name, principal=principal, interest_rate=interest_rate, min_payment=min_payment)
        debt_id = self.debt_manager.add_debt(debt)
        
        # Calculate and display payoff time
        debt.id = debt_id  # Set the ID so we can get the payoff info
        payoff_info = debt.calculate_payoff_date()
        if isinstance(payoff_info, dict):
            print(f"Debt '{name}' added successfully with ID: {debt_id}")
            print(f"Estimated time to payoff: {payoff_info['time_string']}")
            print(f"Estimated payoff date: {payoff_info['date']}")
        else:
            print(f"Debt '{name}' added successfully with ID: {debt_id}")
            print(f"Estimated time to payoff: {payoff_info}")
    
    def make_payment(self):
        """Make a payment on a debt"""
        self.view_all_debts()
        
        try:
            debt_id = int(input("\nEnter debt ID to make payment: "))
            amount = float(input("Enter payment amount: $"))
        except ValueError:
            print("Invalid input. Please enter numeric values.")
            return
        
        debt = self.debt_manager.get_debt(debt_id)
        if not debt:
            print(f"No debt found with ID: {debt_id}")
            return
        
        payment = Payment(id=None, debt_id=debt_id, amount=amount)
        payment_id = self.debt_manager.add_payment(payment)
        
        # Get updated debt info to show accurate payoff time
        updated_debt = self.debt_manager.get_debt(debt_id)
        payoff_info = updated_debt.calculate_payoff_date()
        
        print(f"Payment of ${amount:.2f} applied to '{debt.name}'. New balance: ${updated_debt.current_balance:.2f}")
        
        if isinstance(payoff_info, dict):
            print(f"Updated time to payoff: {payoff_info['time_string']}")
            print(f"Updated payoff date: {payoff_info['date']}")
        else:
            print(f"Updated time to payoff: {payoff_info}")
    
    def view_debt_details(self):
        """View detailed information about a debt"""
        self.view_all_debts()
        
        try:
            debt_id = int(input("\nEnter debt ID to view details: "))
        except ValueError:
            print("Invalid input. Please enter a numeric ID.")
            return
        
        debt = self.debt_manager.get_debt(debt_id)
        if not debt:
            print(f"No debt found with ID: {debt_id}")
            return
        
        payments = self.debt_manager.get_payments_for_debt(debt_id)
        payoff_info = debt.calculate_payoff_date()
        
        print(f"\n===== Debt Details: {debt.name} =====")
        print(f"Principal: ${debt.principal:.2f}")
        print(f"Current Balance: ${debt.current_balance:.2f}")
        print(f"Interest Rate: {debt.interest_rate:.2f}%")
        print(f"Minimum Payment: ${debt.min_payment:.2f}")
        print(f"Monthly Interest: ${debt.monthly_interest:.2f}")
        print(f"Total Paid: ${debt.total_paid:.2f}")
        print(f"Created On: {debt.creation_date}")
        
        # Display payoff information
        if isinstance(payoff_info, dict):
            print(f"Estimated time to payoff: {payoff_info['time_string']}")
            print(f"Estimated payoff date: {payoff_info['date']}")
        else:
            print(f"Estimated time to payoff: {payoff_info}")
        
        if payments:
            print("\n===== Payment History =====")
            print(f"{'ID':<5} {'Date':<12} {'Amount':<10}")
            print("-" * 30)
            
            for payment in payments:
                print(f"{payment.id:<5} {payment.payment_date:<12} ${payment.amount:<9.2f}")
        else:
            print("\nNo payment history found.")
    
    def generate_payment_plan(self):
        """Generate and display a payment plan"""
        self.view_all_debts()
        
        try:
            debt_id = int(input("\nEnter debt ID to generate payment plan: "))
        except ValueError:
            print("Invalid input. Please enter a numeric ID.")
            return
        
        debt = self.debt_manager.get_debt(debt_id)
        if not debt:
            print(f"No debt found with ID: {debt_id}")
            return
        
        print("\nPayment Plan Strategies:")
        print("1. Minimum payments only")
        print("2. Accelerated payments")
        
        try:
            strategy_choice = int(input("Choose a strategy (1-2): "))
        except ValueError:
            print("Invalid input. Using minimum payments strategy.")
            strategy_choice = 1
        
        strategy = "minimum" if strategy_choice == 1 else "accelerated"
        
        plan_df = self.debt_manager.generate_payment_plan(debt_id, strategy)
        
        if plan_df.empty:
            print("Unable to generate payment plan.")
            return
        
        # Calculate payoff date based on the plan
        today = datetime.datetime.now()
        payoff_date = today + relativedelta(months=len(plan_df))
        
        print(f"\n===== Payment Plan for {debt.name} =====")
        print(f"Total Months to Pay Off: {len(plan_df)}")
        print(f"Estimated Payoff Date: {payoff_date.strftime('%Y-%m-%d')}")
        print(f"Total Interest Paid: ${sum(plan_df['Interest']):.2f}")
        print(f"Total Amount Paid: ${sum(plan_df['Payment']):.2f}")
        
        view_details = input("\nWould you like to see month-by-month details? (y/n): ").lower()
        if view_details == 'y':
            pd.set_option('display.max_rows', None)
            print(plan_df)
            pd.reset_option('display.max_rows')
        
        visualize = input("\nWould you like to visualize this payment plan? (y/n): ").lower()
        if visualize == 'y':
            self.debt_manager.visualize_payment_plan(debt_id, strategy)
    
    def compare_strategies(self):
        """Compare different debt payoff strategies"""
        try:
            extra_payment = float(input("Enter monthly extra payment amount: $"))
        except ValueError:
            print("Invalid input. Using $0 for extra payment.")
            extra_payment = 0
        
        results = self.debt_manager.compare_payoff_strategies(extra_payment)
        
        if not results:
            print("No debts found for comparison.")
            return
        
        # Calculate payoff dates
        today = datetime.datetime.now()
        avalanche_date = today + relativedelta(months=results['avalanche']['months'])
        snowball_date = today + relativedelta(months=results['snowball']['months'])
        
        print("\n===== Debt Payoff Strategy Comparison =====")
        print(f"Total Debt Principal: ${results['total_principal']:.2f}")
        print("\nAvalanche Method (Highest Interest First):")
        print(f"  Months to Payoff: {results['avalanche']['months']}")
        print(f"  Estimated Payoff Date: {avalanche_date.strftime('%Y-%m-%d')}")
        print(f"  Total Interest Paid: ${results['avalanche']['interest_paid']:.2f}")
        print(f"  Total Amount Paid: ${results['avalanche']['total_paid']:.2f}")
        
        print("\nSnowball Method (Lowest Balance First):")
        print(f"  Months to Payoff: {results['snowball']['months']}")
        print(f"  Estimated Payoff Date: {snowball_date.strftime('%Y-%m-%d')}")
        print(f"  Total Interest Paid: ${results['snowball']['interest_paid']:.2f}")
        print(f"  Total Amount Paid: ${results['snowball']['total_paid']:.2f}")
        
        difference = abs(results['avalanche']['interest_paid'] - results['snowball']['interest_paid'])
        better_method = "Avalanche" if results['avalanche']['interest_paid'] < results['snowball']['interest_paid'] else "Snowball"
        
        print(f"\nThe {better_method} method will save you ${difference:.2f} in interest.")
        
        # Compare time difference between methods
        time_diff_months = abs(results['avalanche']['months'] - results['snowball']['months'])
        faster_method = "Avalanche" if results['avalanche']['months'] < results['snowball']['months'] else "Snowball"
        
        if time_diff_months > 0:
            years = time_diff_months // 12
            months = time_diff_months % 12
            
            time_diff_str = ""
            if years > 0:
                time_diff_str += f"{years} year{'s' if years != 1 else ''}"
                if months > 0:
                    time_diff_str += f" and {months} month{'s' if months != 1 else ''}"
            else:
                time_diff_str = f"{months} month{'s' if months != 1 else ''}"
                
            print(f"The {faster_method} method will pay off your debts {time_diff_str} faster.")
        else:
            print("Both methods will take the same amount of time to pay off your debts.")
    
    def delete_debt(self):
        """Delete a debt"""
        self.view_all_debts()
        
        try:
            debt_id = int(input("\nEnter debt ID to delete: "))
        except ValueError:
            print("Invalid input. Please enter a numeric ID.")
            return
        
        debt = self.debt_manager.get_debt(debt_id)
        if not debt:
            print(f"No debt found with ID: {debt_id}")
            return
        
        confirm = input(f"Are you sure you want to delete '{debt.name}'? This cannot be undone. (y/n): ").lower()
        
        if confirm == 'y':
            success = self.debt_manager.delete_debt(debt_id)
            if success:
                print(f"Debt '{debt.name}' deleted successfully.")
            else:
                print("Error deleting debt.")
        else:
            print("Deletion cancelled.")


if __name__ == "__main__":
    # Check for required packages
    try:
        import dateutil.relativedelta
    except ImportError:
        print("The 'python-dateutil' package is required. Installing it...")
        import subprocess
        subprocess.check_call(["pip", "install", "python-dateutil"])
        print("Package installed successfully!")
    
    # Run the CLI application
    cli = DebtManagementCLI()
    cli.run()