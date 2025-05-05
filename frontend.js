let debts = [];
let payments = [];
let currentDebtId = null;
let paymentPlans = {};
let strategyResults = null;
let paymentPlanChart = null;
let distributionChart = null;
let strategyChart = null;

// Load mock data for demo
function loadMockData() {
    debts = [
        {
            id: 1,
            name: "Credit Card",
            principal: 5000,
            interest_rate: 18.99,
            min_payment: 150,
            total_paid: 1200,
            creation_date: "2023-06-15",
            current_balance: 3800,
            monthly_interest: 60.23
        },
        {
            id: 2,
            name: "Student Loan",
            principal: 20000,
            interest_rate: 4.5,
            min_payment: 220,
            total_paid: 4500,
            creation_date: "2022-09-01",
            current_balance: 15500,
            monthly_interest: 58.13
        },
        {
            id: 3,
            name: "Car Loan",
            principal: 12000,
            interest_rate: 6.2,
            min_payment: 275,
            total_paid: 3500,
            creation_date: "2023-01-10",
            current_balance: 8500,
            monthly_interest: 43.92
        }
    ];
    
    payments = [
        { id: 1, debt_id: 1, amount: 200, payment_date: "2024-04-01" },
        { id: 2, debt_id: 1, amount: 300, payment_date: "2024-03-01" },
        { id: 3, debt_id: 1, amount: 150, payment_date: "2024-02-01" },
        { id: 4, debt_id: 2, amount: 220, payment_date: "2024-04-05" },
        { id: 5, debt_id: 2, amount: 220, payment_date: "2024-03-05" },
        { id: 6, debt_id: 3, amount: 275, payment_date: "2024-04-10" },
        { id: 7, debt_id: 3, amount: 350, payment_date: "2024-03-10" }
    ];
    
    updateDashboard();
}

// Initialize the application
function init() {
    document.getElementById('add-debt-form').addEventListener('submit', function(e) {
        e.preventDefault();
        addDebt();
    });
    
    document.getElementById('make-payment-form').addEventListener('submit', function(e) {
        e.preventDefault();
        makePayment();
    });
    
    // Set today's date as default for payment date input
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('payment-date').value = today;
    
    // Set up tab switching
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            
            if (tabId === 'payment-plan' && currentDebtId) {
                generatePaymentPlan(currentDebtId);
            }
        });
    });
    
    document.getElementById('payment-plan-strategy').addEventListener('change', function() {
        if (currentDebtId) {
            generatePaymentPlan(currentDebtId);
        }
    });
    
    loadMockData();
}

// Show the selected page
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.style.display = 'none';
    });
    document.getElementById(pageId).style.display = 'block';
    
    document.querySelectorAll('nav a').forEach(link => {
        link.classList.remove('active');
    });
    
    // Changed from event.target to use proper event handling
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    if (pageId === 'debts') {
        populateDebtSelector();
    }
}

// Open a modal
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
    
    if (modalId === 'make-payment-modal') {
        populateDebtDropdown();
        
        // If opened from debt details, pre-select the current debt
        if (currentDebtId) {
            document.getElementById('payment-debt-id').value = currentDebtId;
        }
    }
}

// Close a modal
function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Update dashboard with latest data
function updateDashboard() {
    const totalDebt = debts.reduce((sum, debt) => sum + debt.current_balance, 0);
    const totalInterest = debts.reduce((sum, debt) => sum + debt.monthly_interest, 0);
    const totalMinPayment = debts.reduce((sum, debt) => sum + debt.min_payment, 0);
    
    document.getElementById('total-debt').textContent = `$${totalDebt.toFixed(2)}`;
    document.getElementById('monthly-interest').textContent = `$${totalInterest.toFixed(2)}`;
    document.getElementById('monthly-payment').textContent = `$${totalMinPayment.toFixed(2)}`;
    document.getElementById('debt-count').textContent = debts.length;
    
    updateDebtsTable();
    updatePaymentsTable();
}

// Update the debts table
function updateDebtsTable() {
    const tableBody = document.getElementById('debts-table-body');
    tableBody.innerHTML = '';
    
    debts.forEach(debt => {
        const row = document.createElement('tr');
        
        const payoffTime = calculatePayoffTime(debt);
        
        row.innerHTML = `
            <td>${debt.name}</td>
            <td>$${debt.current_balance.toFixed(2)}</td>
            <td>${debt.interest_rate}%</td>
            <td>$${debt.min_payment.toFixed(2)}</td>
            <td>${payoffTime}</td>
            <td class="action-column">
                <button class="btn btn-success btn-sm" onclick="viewDebtDetails(${debt.id})">Details</button>
                <button class="btn btn-danger btn-sm" onclick="confirmDeleteDebt(${debt.id}, '${debt.name}')">Delete</button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Update the payments table
function updatePaymentsTable() {
    const tableBody = document.getElementById('payments-table-body');
    tableBody.innerHTML = '';
    
    // Sort payments by date (newest first)
    const sortedPayments = [...payments].sort((a, b) => {
        return new Date(b.payment_date) - new Date(a.payment_date);
    });
    
    // Show most recent 5 payments
    sortedPayments.slice(0, 5).forEach(payment => {
        const row = document.createElement('tr');
        const debt = debts.find(d => d.id === payment.debt_id);
        
        row.innerHTML = `
            <td>${debt ? debt.name : 'Unknown'}</td>
            <td>$${payment.amount.toFixed(2)}</td>
            <td>${formatDate(payment.payment_date)}</td>
        `;
        
        tableBody.appendChild(row);
    });
    
    if (sortedPayments.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="3">No payments recorded</td>';
        tableBody.appendChild(row);
    }
}

// Add a new debt
function addDebt() {
    const name = document.getElementById('debt-name').value;
    const principal = parseFloat(document.getElementById('debt-principal').value);
    const interestRate = parseFloat(document.getElementById('debt-interest').value);
    const minPayment = parseFloat(document.getElementById('debt-min-payment').value);
    
    const newId = debts.length > 0 ? Math.max(...debts.map(d => d.id)) + 1 : 1;
    
    const newDebt = {
        id: newId,
        name: name,
        principal: principal,
        interest_rate: interestRate,
        min_payment: minPayment,
        total_paid: 0,
        creation_date: new Date().toISOString().split('T')[0],
        current_balance: principal,
        monthly_interest: principal * (interestRate / 12 / 100)
    };
    
    debts.push(newDebt);
    updateDashboard();
    closeModal('add-debt-modal');
    
    // Reset the form
    document.getElementById('add-debt-form').reset();
    
    // Show success notification
    showNotification('Debt added successfully!', 'success');
}

// Make a payment
function makePayment() {
    const debtId = parseInt(document.getElementById('payment-debt-id').value);
    const amount = parseFloat(document.getElementById('payment-amount').value);
    const paymentDate = document.getElementById('payment-date').value;
    
    const debt = debts.find(d => d.id === debtId);
    if (!debt) {
        showNotification('Debt not found', 'error');
        return;
    }
    
    const newId = payments.length > 0 ? Math.max(...payments.map(p => p.id)) + 1 : 1;
    
    const newPayment = {
        id: newId,
        debt_id: debtId,
        amount: amount,
        payment_date: paymentDate
    };
    
    payments.push(newPayment);
    
    // Update debt balance
    debt.total_paid += amount;
    debt.current_balance = debt.principal - debt.total_paid;
    if (debt.current_balance < 0) debt.current_balance = 0;
    debt.monthly_interest = debt.current_balance * (debt.interest_rate / 12 / 100);
    
    updateDashboard();
    closeModal('make-payment-modal');
    
    // Reset the form
    document.getElementById('make-payment-form').reset();
    document.getElementById('payment-date').value = new Date().toISOString().split('T')[0];
    
    // If we're in debt details view, refresh it
    if (currentDebtId === debtId) {
        viewDebtDetails(debtId);
    }
    
    // Show success notification
    showNotification('Payment recorded successfully!', 'success');
}

// Confirm debt delete
function confirmDeleteDebt(debtId, debtName) {
    document.getElementById('delete-debt-id').value = debtId;
    document.getElementById('delete-debt-name').textContent = debtName;
    openModal('delete-debt-modal');
}

// Delete a debt
function deleteDebt() {
    const debtId = parseInt(document.getElementById('delete-debt-id').value);
    
    // Remove the debt
    debts = debts.filter(d => d.id !== debtId);
    
    // Remove associated payments
    payments = payments.filter(p => p.debt_id !== debtId);
    
    updateDashboard();
    closeModal('delete-debt-modal');
    
    // If we're viewing this debt's details, go back to selection
    if (currentDebtId === debtId) {
        currentDebtId = null;
        document.getElementById('debt-details-container').innerHTML = `
            <p>Select a debt to view details</p>
            <div id="debt-selector"></div>
        `;
        document.getElementById('debt-detail-content').style.display = 'none';
        populateDebtSelector();
    }
    
    // Show success notification
    showNotification('Debt deleted successfully!', 'success');
}

// View debt details
function viewDebtDetails(debtId) {
    const debt = debts.find(d => d.id === debtId);
    if (!debt) return;
    
    currentDebtId = debtId;
    
    // For the "Debts" page
    if (document.getElementById('debts').style.display !== 'none') {
        document.getElementById('debt-details-container').innerHTML = '';
        
        const debtDetails = document.createElement('div');
        debtDetails.classList.add('debt-header');
        debtDetails.innerHTML = `
            <h3>${debt.name}</h3>
            <p>Balance: $${debt.current_balance.toFixed(2)}</p>
        `;
        
        document.getElementById('debt-details-container').appendChild(debtDetails);
        document.getElementById('debt-detail-content').style.display = 'block';
        
        // Reset tabs
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelector('.tab[data-tab="overview"]').classList.add('active');
        document.getElementById('overview').classList.add('active');
        
        updateDebtOverview(debt);
        updatePaymentHistory(debtId);
        generatePaymentPlan(debtId);
    } else {
        // If we're on another page, switch to the debts page
        showPage('debts');
        setTimeout(() => viewDebtDetails(debtId), 100);
    }
}

// Update debt overview
function updateDebtOverview(debt) {
    const payoffInfo = calculatePayoffInfo(debt);
    
    const overviewHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px;">
            <div class="dashboard-card">
                <h3>Principal</h3>
                <div class="amount">$${debt.principal.toFixed(2)}</div>
            </div>
            
            <div class="dashboard-card">
                <h3>Current Balance</h3>
                <div class="amount debt">$${debt.current_balance.toFixed(2)}</div>
            </div>
            
            <div class="dashboard-card">
                <h3>Interest Rate</h3>
                <div class="amount">${debt.interest_rate.toFixed(2)}%</div>
            </div>
            
            <div class="dashboard-card">
                <h3>Monthly Interest</h3>
                <div class="amount debt">$${debt.monthly_interest.toFixed(2)}</div>
            </div>
            
            <div class="dashboard-card">
                <h3>Minimum Payment</h3>
                <div class="amount">$${debt.min_payment.toFixed(2)}</div>
            </div>
            
            <div class="dashboard-card">
                <h3>Total Paid</h3>
                <div class="amount payment">$${debt.total_paid.toFixed(2)}</div>
            </div>
        </div>
        
        <div class="dashboard-card">
            <h3>Payoff Information</h3>
            <p>Estimated time to payoff: <strong>${payoffInfo.timeString}</strong></p>
            <p>Estimated payoff date: <strong>${payoffInfo.date}</strong></p>
        </div>
    `;
    
    document.getElementById('debt-overview').innerHTML = overviewHTML;
    
    // Create or update payment distribution chart
    createPaymentDistributionChart(debt);
}

// Create payment distribution chart
function createPaymentDistributionChart(debt) {
    const ctx = document.getElementById('payment-distribution-chart').getContext('2d');
    
    // Calculate values
    const principalPaid = debt.total_paid;
    const principalRemaining = debt.principal - debt.total_paid;
    const interestPaid = calculateTotalInterestPaid(debt.id);
    
    // Destroy existing chart if it exists
    if (distributionChart) distributionChart.destroy();
    
    distributionChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Principal Paid', 'Principal Remaining', 'Interest Paid'],
            datasets: [{
                data: [principalPaid, principalRemaining, interestPaid],
                backgroundColor: [
                    '#16a34a',  // Green
                    '#dc2626',  // Red
                    '#ea580c'   // Orange
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const percentage = Math.round((value / (principalPaid + principalRemaining + interestPaid)) * 100);
                            return `$${value.toFixed(2)} (${percentage}%)`;
                        }
                    }
                },
                title: {
                    display: true,
                    text: 'Payment Distribution'
                }
            }
        }
    });
}

// Update payment history table
function updatePaymentHistory(debtId) {
    const debtPayments = payments.filter(p => p.debt_id === debtId);
    const tableBody = document.getElementById('payment-history-table');
    tableBody.innerHTML = '';
    
    if (debtPayments.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="2">No payment history found</td>';
        tableBody.appendChild(row);
        return;
    }
    
    // Sort payments by date (newest first)
    const sortedPayments = [...debtPayments].sort((a, b) => {
        return new Date(b.payment_date) - new Date(a.payment_date);
    });
    
    sortedPayments.forEach(payment => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>$${payment.amount.toFixed(2)}</td>
            <td>${formatDate(payment.payment_date)}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Generate payment plan for a debt
function generatePaymentPlan(debtId) {
    const debt = debts.find(d => d.id === debtId);
    if (!debt) return;
    
    const strategy = document.getElementById('payment-plan-strategy').value;
    
    // Check if we've already calculated this plan
    const planKey = `${debtId}-${strategy}`;
    let plan = paymentPlans[planKey];
    
    if (!plan) {
        // Generate the plan (simplified simulation)
        plan = simulatePaymentPlan(debt, strategy);
        paymentPlans[planKey] = plan;
    }
    
    // Update the summary
    const totalInterest = plan.interest.reduce((sum, val) => sum + val, 0);
    const totalPayments = plan.payment.reduce((sum, val) => sum + val, 0);
    
    document.getElementById('payment-plan-summary').innerHTML = `
        <div class="dashboard-card">
            <h3>Payment Plan Summary (${strategy === 'minimum' ? 'Minimum Payments' : 'Accelerated Payments'})</h3>
            <p>Months to pay off: <strong>${plan.month.length}</strong></p>
            <p>Total interest paid: <strong>$${totalInterest.toFixed(2)}</strong></p>
            <p>Total amount paid: <strong>$${totalPayments.toFixed(2)}</strong></p>
        </div>
    `;
    
    // Create or update the chart
    createPaymentPlanChart(plan);
}

// Create payment plan chart
function createPaymentPlanChart(plan) {
    const ctx = document.getElementById('payment-plan-chart').getContext('2d');
    
    // Calculate cumulative interest and payments
    const cumulativeInterest = [];
    const cumulativePayments = [];
    let interestSum = 0;
    let paymentSum = 0;
    
    for (let i = 0; i < plan.month.length; i++) {
        interestSum += plan.interest[i];
        paymentSum += plan.payment[i];
        cumulativeInterest.push(interestSum);
        cumulativePayments.push(paymentSum);
    }
    
    // Destroy existing chart if it exists
    if (paymentPlanChart) paymentPlanChart.destroy();
    
    paymentPlanChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: plan.month,
            datasets: [
                {
                    label: 'Balance',
                    data: plan.balance,
                    borderColor: '#dc2626',
                    backgroundColor: 'rgba(220, 38, 38, 0.1)',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Payments Made',
                    data: cumulativePayments,
                    borderColor: '#16a34a',
                    backgroundColor: 'rgba(22, 163, 74, 0.1)',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Interest Paid',
                    data: cumulativeInterest,
                    borderColor: '#ea580c',
                    backgroundColor: 'rgba(234, 88, 12, 0.1)',
                    fill: true,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Debt Payoff Plan'
                }
            }
        }
    });
}

// Compare payoff strategies
function compareStrategies() {
    const extraPayment = parseFloat(document.getElementById('extra-payment').value) || 0;
    
    // Check if we have debts
    if (debts.length === 0) {
        showNotification('No debts found to compare strategies', 'error');
        return;
    }
    
    // Simulate both strategies
    const avalancheResults = simulateStrategy(debts, 'avalanche', extraPayment);
    const snowballResults = simulateStrategy(debts, 'snowball', extraPayment);
    
    // Store results for reference
    strategyResults = {
        avalanche: avalancheResults,
        snowball: snowballResults
    };
    
    // Calculate payoff dates
    const today = new Date();
    const avalancheDate = new Date(today);
    avalancheDate.setMonth(today.getMonth() + avalancheResults.months);
    
    const snowballDate = new Date(today);
    snowballDate.setMonth(today.getMonth() + snowballResults.months);
    
    // Update UI with results
    document.getElementById('avalanche-time').textContent = formatMonthsAsTime(avalancheResults.months);
    document.getElementById('avalanche-date').textContent = formatDate(avalancheDate.toISOString().split('T')[0]);
    document.getElementById('avalanche-interest').textContent = `$${avalancheResults.interestPaid.toFixed(2)}`;
    document.getElementById('avalanche-total').textContent = `$${avalancheResults.totalPaid.toFixed(2)}`;
    
    document.getElementById('snowball-time').textContent = formatMonthsAsTime(snowballResults.months);
    document.getElementById('snowball-date').textContent = formatDate(snowballDate.toISOString().split('T')[0]);
    document.getElementById('snowball-interest').textContent = `$${snowballResults.interestPaid.toFixed(2)}`;
    document.getElementById('snowball-total').textContent = `$${snowballResults.totalPaid.toFixed(2)}`;
    
    // Determine the recommendation
    let recommendation;
    if (avalancheResults.interestPaid < snowballResults.interestPaid) {
        const savings = snowballResults.interestPaid - avalancheResults.interestPaid;
        recommendation = `<strong>Recommendation: Use the Avalanche method.</strong> You'll save $${savings.toFixed(2)} in interest compared to the Snowball method.`;
        
        if (avalancheResults.months < snowballResults.months) {
            const timeDiff = snowballResults.months - avalancheResults.months;
            recommendation += ` It's also faster by ${formatMonthsAsTime(timeDiff)}.`;
        }
    } else if (snowballResults.interestPaid < avalancheResults.interestPaid) {
        const savings = avalancheResults.interestPaid - snowballResults.interestPaid;
        recommendation = `<strong>Recommendation: Use the Snowball method.</strong> You'll save $${savings.toFixed(2)} in interest compared to the Avalanche method.`;
        
        if (snowballResults.months < avalancheResults.months) {
            const timeDiff = avalancheResults.months - snowballResults.months;
            recommendation += ` It's also faster by ${formatMonthsAsTime(timeDiff)}.`;
        }
    } else {
        recommendation = "<strong>Both methods are equally effective</strong> for your current debt situation.";
    }
    
    if (extraPayment > 0) {
        recommendation += ` With an extra $${extraPayment.toFixed(2)} payment each month, you'll pay off your debt ${formatMonthsAsTime(avalancheResults.savedMonths)} earlier and save $${avalancheResults.savedInterest.toFixed(2)} in interest.`;
    }
    
    document.getElementById('strategy-recommendation').innerHTML = recommendation;
    
    // Create strategy comparison chart
    createStrategyComparisonChart();
    
    // Show the results section
    document.getElementById('strategy-comparison-results').style.display = 'block';
}

// Create strategy comparison chart
function createStrategyComparisonChart() {
    if (!strategyResults) return;
    
    const ctx = document.getElementById('strategy-comparison-chart').getContext('2d');
    
    // Destroy existing chart if it exists
    if (strategyChart) strategyChart.destroy();
    
    const months = Math.max(strategyResults.avalanche.months, strategyResults.snowball.months);
    const labels = Array.from({ length: months }, (_, i) => i + 1);
    
    // Pad the shorter strategy with zeros
    const avalancheBalance = [...strategyResults.avalanche.balances];
    const snowballBalance = [...strategyResults.snowball.balances];
    
    if (avalancheBalance.length < months) {
        avalancheBalance.push(...Array(months - avalancheBalance.length).fill(0));
    }
    
    if (snowballBalance.length < months) {
        snowballBalance.push(...Array(months - snowballBalance.length).fill(0));
    }
    
    strategyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Avalanche Balance',
                    data: avalancheBalance,
                    borderColor: '#0369a1',
                    backgroundColor: 'rgba(3, 105, 161, 0.1)',
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Snowball Balance',
                    data: snowballBalance,
                    borderColor: '#ca8a04',
                    backgroundColor: 'rgba(202, 138, 4, 0.1)',
                    fill: true,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Month'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Amount ($)'
                    },
                    beginAtZero: true
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Strategy Comparison'
                }
            }
        }
    });
}

// Populate debt selector for debt details page
function populateDebtSelector() {
    const selector = document.getElementById('debt-selector');
    selector.innerHTML = '';
    
    if (debts.length === 0) {
        selector.innerHTML = '<p>No debts found. Add a debt first.</p>';
        return;
    }
    
    const debtList = document.createElement('div');
    debtList.style.display = 'flex';
    debtList.style.flexWrap = 'wrap';
    debtList.style.gap = '10px';
    debtList.style.marginTop = '15px';
    
    debts.forEach(debt => {
        const debtCard = document.createElement('div');
        debtCard.classList.add('dashboard-card');
        debtCard.style.cursor = 'pointer';
        debtCard.style.minWidth = '200px';
        debtCard.onclick = () => viewDebtDetails(debt.id);
        
        debtCard.innerHTML = `
            <h3>${debt.name}</h3>
            <div class="amount debt">$${debt.current_balance.toFixed(2)}</div>
            <div class="card-detail">${debt.interest_rate}% interest</div>
        `;
        
        debtList.appendChild(debtCard);
    });
    
    selector.appendChild(debtList);
}

// Populate debt dropdown for payment form
function populateDebtDropdown() {
    const dropdown = document.getElementById('payment-debt-id');
    dropdown.innerHTML = '';
    
    debts.forEach(debt => {
        const option = document.createElement('option');
        option.value = debt.id;
        option.textContent = `${debt.name} ($${debt.current_balance.toFixed(2)})`;
        dropdown.appendChild(option);
    });
    
    if (currentDebtId) {
        dropdown.value = currentDebtId;
    }
}

// Calculate payoff time for a debt
// Calculate payoff time for a debt
function calculatePayoffTime(debt) {
    if (debt.current_balance <= 0) {
        return "Paid off";
    }
    
    // Calculate monthly interest rate (decimal)
    const monthlyRate = debt.interest_rate / 100 / 12;
    
    // Use the formula for calculating time to pay off a loan
    // -ln(1 - r * B / P) / ln(1 + r)
    // where r is monthly rate, B is balance, P is payment
    
    // Handle edge cases where payment is less than or equal to monthly interest
    if (debt.min_payment <= debt.current_balance * monthlyRate) {
        return "Never (payment too low)";
    }
    
    const numerator = -Math.log(1 - monthlyRate * debt.current_balance / debt.min_payment);
    const denominator = Math.log(1 + monthlyRate);
    const months = numerator / denominator;
    
    return formatMonthsAsTime(months);
}

// Calculate detailed payoff information
function calculatePayoffInfo(debt) {
    if (debt.current_balance <= 0) {
        return {
            months: 0,
            timeString: "Paid off",
            date: "N/A"
        };
    }
    
    // Calculate monthly interest rate (decimal)
    const monthlyRate = debt.interest_rate / 100 / 12;
    
    // Handle edge cases where payment is less than or equal to monthly interest
    if (debt.min_payment <= debt.current_balance * monthlyRate) {
        return {
            months: Infinity,
            timeString: "Never (payment too low)",
            date: "N/A"
        };
    }
    
    const numerator = -Math.log(1 - monthlyRate * debt.current_balance / debt.min_payment);
    const denominator = Math.log(1 + monthlyRate);
    const months = numerator / denominator;
    
    // Calculate payoff date
    const today = new Date();
    const payoffDate = new Date(today);
    payoffDate.setMonth(today.getMonth() + Math.ceil(months));
    
    return {
        months: months,
        timeString: formatMonthsAsTime(months),
        date: formatDate(payoffDate.toISOString().split('T')[0])
    };
}

// Format months as years and months
function formatMonthsAsTime(months) {
    months = Math.ceil(months);
    
    if (months < 1) {
        return "Less than 1 month";
    }
    
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    
    let result = "";
    
    if (years > 0) {
        result += `${years} year${years !== 1 ? 's' : ''}`;
    }
    
    if (remainingMonths > 0) {
        if (result.length > 0) result += " ";
        result += `${remainingMonths} month${remainingMonths !== 1 ? 's' : ''}`;
    }
    
    return result;
}

// Format date as MM/DD/YYYY
function formatDate(dateString) {
    const date = new Date(dateString);
    return `${date.getMonth() + 1}/${date.getDate()}/${date.getFullYear()}`;
}

// Calculate total interest paid on a debt
function calculateTotalInterestPaid(debtId) {
    // This is a simplified calculation that assumes all payments above minimum
    // go toward reducing the principal
    const debt = debts.find(d => d.id === debtId);
    if (!debt) return 0;
    
    const debtPayments = payments.filter(p => p.debt_id === debtId);
    const totalPayments = debtPayments.reduce((sum, p) => sum + p.amount, 0);
    
    // If total paid is less than principal, no interest has been paid yet
    if (totalPayments <= debt.principal) return 0;
    
    // Otherwise, any amount paid over the principal is interest
    return totalPayments - debt.principal;
}

// Simulate payment plan for a debt
function simulatePaymentPlan(debt, strategy) {
    const plan = {
        month: [],
        balance: [],
        interest: [],
        payment: []
    };
    
    let balance = debt.current_balance;
    let month = 1;
    const monthlyRate = debt.interest_rate / 100 / 12;
    
    // Calculate extra payment for accelerated strategy
    let payment = debt.min_payment;
    if (strategy === 'accelerated') {
        payment = debt.min_payment * 1.5; // 50% more than minimum
    }
    
    while (balance > 0 && month < 1000) { // 1000 months limit to prevent infinite loops
        plan.month.push(month);
        plan.balance.push(balance);
        
        // Calculate interest for this month
        const interest = balance * monthlyRate;
        plan.interest.push(interest);
        
        // Calculate actual payment (don't overpay at the end)
        const actualPayment = Math.min(payment, balance + interest);
        plan.payment.push(actualPayment);
        
        // Apply payment
        balance = balance + interest - actualPayment;
        
        // Round to nearest cent to avoid floating point issues
        balance = Math.round(balance * 100) / 100;
        
        month++;
    }
    
    return plan;
}

// Simulate payoff strategies (Avalanche or Snowball)
function simulateStrategy(debts, strategy, extraPayment = 0) {
    // Create a deep copy of debts to work with
    const debtsCopy = JSON.parse(JSON.stringify(debts));
    
    // Sort debts based on strategy
    if (strategy === 'avalanche') {
        // Sort by interest rate (highest to lowest)
        debtsCopy.sort((a, b) => b.interest_rate - a.interest_rate);
    } else {
        // Sort by balance (lowest to highest)
        debtsCopy.sort((a, b) => a.current_balance - b.current_balance);
    }
    
    let month = 0;
    let totalPaid = 0;
    let interestPaid = 0;
    const balances = [debtsCopy.reduce((sum, debt) => sum + debt.current_balance, 0)];
    
    // Also simulate without extra payment for comparison
    const baselineMonths = calculateMonthsToPayoff(JSON.parse(JSON.stringify(debtsCopy)), 0);
    const baselineInterest = calculateTotalInterest(JSON.parse(JSON.stringify(debtsCopy)), 0);
    
    while (debtsCopy.some(debt => debt.current_balance > 0) && month < 1000) {
        month++;
        let remainingExtra = extraPayment;
        
        // Apply interest and minimum payments to all debts
        for (let i = 0; i < debtsCopy.length; i++) {
            const debt = debtsCopy[i];
            if (debt.current_balance <= 0) continue;
            
            // Calculate interest
            const monthlyRate = debt.interest_rate / 100 / 12;
            const interest = debt.current_balance * monthlyRate;
            interestPaid += interest;
            
            // Apply interest
            debt.current_balance += interest;
            
            // Apply minimum payment
            const payment = Math.min(debt.min_payment, debt.current_balance);
            debt.current_balance -= payment;
            totalPaid += payment;
        }
        
        // Apply extra payment to the first debt with remaining balance (per strategy order)
        for (let i = 0; i < debtsCopy.length; i++) {
            const debt = debtsCopy[i];
            if (debt.current_balance <= 0 || remainingExtra <= 0) continue;
            
            const extraForDebt = Math.min(remainingExtra, debt.current_balance);
            debt.current_balance -= extraForDebt;
            remainingExtra -= extraForDebt;
            totalPaid += extraForDebt;
        }
        
        // Store total balance at this point
        const totalBalance = debtsCopy.reduce((sum, debt) => sum + debt.current_balance, 0);
        balances.push(totalBalance);
    }
    
    return {
        months: month,
        totalPaid: totalPaid,
        interestPaid: interestPaid,
        balances: balances,
        savedMonths: baselineMonths - month,
        savedInterest: baselineInterest - interestPaid
    };
}

// Calculate months to payoff for comparison
function calculateMonthsToPayoff(debts, extraPayment) {
    let month = 0;
    
    while (debts.some(debt => debt.current_balance > 0) && month < 1000) {
        month++;
        let remainingExtra = extraPayment;
        
        // Apply interest and minimum payments to all debts
        for (let i = 0; i < debts.length; i++) {
            const debt = debts[i];
            if (debt.current_balance <= 0) continue;
            
            // Calculate interest
            const monthlyRate = debt.interest_rate / 100 / 12;
            const interest = debt.current_balance * monthlyRate;
            
            // Apply interest
            debt.current_balance += interest;
            
            // Apply minimum payment
            const payment = Math.min(debt.min_payment, debt.current_balance);
            debt.current_balance -= payment;
        }
        
        // Apply extra payment to the first debt
        for (let i = 0; i < debts.length; i++) {
            const debt = debts[i];
            if (debt.current_balance <= 0 || remainingExtra <= 0) continue;
            
            const extraForDebt = Math.min(remainingExtra, debt.current_balance);
            debt.current_balance -= extraForDebt;
            remainingExtra -= extraForDebt;
        }
    }
    
    return month;
}

// Calculate total interest for comparison
function calculateTotalInterest(debts, extraPayment) {
    let month = 0;
    let totalInterest = 0;
    
    while (debts.some(debt => debt.current_balance > 0) && month < 1000) {
        month++;
        let remainingExtra = extraPayment;
        
        // Apply interest and minimum payments to all debts
        for (let i = 0; i < debts.length; i++) {
            const debt = debts[i];
            if (debt.current_balance <= 0) continue;
            
            // Calculate interest
            const monthlyRate = debt.interest_rate / 100 / 12;
            const interest = debt.current_balance * monthlyRate;
            totalInterest += interest;
            
            // Apply interest
            debt.current_balance += interest;
            
            // Apply minimum payment
            const payment = Math.min(debt.min_payment, debt.current_balance);
            debt.current_balance -= payment;
        }
        
        // Apply extra payment to the first debt
        for (let i = 0; i < debts.length; i++) {
            const debt = debts[i];
            if (debt.current_balance <= 0 || remainingExtra <= 0) continue;
            
            const extraForDebt = Math.min(remainingExtra, debt.current_balance);
            debt.current_balance -= extraForDebt;
            remainingExtra -= extraForDebt;
        }
    }
    
    return totalInterest;
}

// Show notification
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.getElementById('notification-container').appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 4700);
}

// Export data to CSV
function exportData() {
    // Generate debt data CSV
    let debtCsv = "Name,Principal,Interest Rate,Minimum Payment,Current Balance,Total Paid\n";
    
    debts.forEach(debt => {
        debtCsv += `"${debt.name}",${debt.principal},${debt.interest_rate},${debt.min_payment},${debt.current_balance},${debt.total_paid}\n`;
    });
    
    // Generate payment data CSV
    let paymentCsv = "Debt,Amount,Date\n";
    
    payments.forEach(payment => {
        const debt = debts.find(d => d.id === payment.debt_id);
        paymentCsv += `"${debt ? debt.name : 'Unknown'}",${payment.amount},${payment.payment_date}\n`;
    });
    
    // Create download links
    const debtBlob = new Blob([debtCsv], { type: 'text/csv' });
    const debtUrl = URL.createObjectURL(debtBlob);
    
    const paymentBlob = new Blob([paymentCsv], { type: 'text/csv' });
    const paymentUrl = URL.createObjectURL(paymentBlob);
    
    // Show modal with download links
    document.getElementById('debt-csv-link').href = debtUrl;
    document.getElementById('payment-csv-link').href = paymentUrl;
    openModal('export-data-modal');
    
    // Clean up URLs after modal is closed
    document.getElementById('export-data-modal').addEventListener('hidden.bs.modal', function () {
        URL.revokeObjectURL(debtUrl);
        URL.revokeObjectURL(paymentUrl);
    }, { once: true });
}

// Import data from CSV
function importData() {
    const debtFile = document.getElementById('import-debt-file').files[0];
    const paymentFile = document.getElementById('import-payment-file').files[0];
    
    // Parse debt file if provided
    if (debtFile) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const contents = e.target.result;
            const rows = contents.split('\n');
            
            // Skip header row
            if (rows.length > 1) {
                const newDebts = [];
                
                for (let i = 1; i < rows.length; i++) {
                    if (!rows[i].trim()) continue;
                    
                    const fields = parseCSVRow(rows[i]);
                    
                    if (fields.length >= 5) {
                        const newDebt = {
                            id: newDebts.length > 0 ? Math.max(...newDebts.map(d => d.id)) + 1 : 1,
                            name: fields[0],
                            principal: parseFloat(fields[1]),
                            interest_rate: parseFloat(fields[2]),
                            min_payment: parseFloat(fields[3]),
                            current_balance: parseFloat(fields[4]),
                            total_paid: fields.length > 5 ? parseFloat(fields[5]) : 0,
                            creation_date: new Date().toISOString().split('T')[0],
                            monthly_interest: parseFloat(fields[4]) * (parseFloat(fields[2]) / 12 / 100)
                        };
                        
                        newDebts.push(newDebt);
                    }
                }
                
                if (newDebts.length > 0) {
                    // Merge with existing or replace
                    if (document.getElementById('merge-data').checked) {
                        // Generate new IDs for imported debts
                        const maxId = debts.length > 0 ? Math.max(...debts.map(d => d.id)) : 0;
                        newDebts.forEach((debt, idx) => {
                            debt.id = maxId + idx + 1;
                        });
                        
                        debts = [...debts, ...newDebts];
                    } else {
                        debts = newDebts;
                    }
                    
                    showNotification(`Imported ${newDebts.length} debts successfully`, 'success');
                    updateDashboard();
                }
            }
        };
        reader.readAsText(debtFile);
    }
    
    // Parse payment file if provided
    if (paymentFile) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const contents = e.target.result;
            const rows = contents.split('\n');
            
            // Skip header row
            if (rows.length > 1) {
                const newPayments = [];
                
                for (let i = 1; i < rows.length; i++) {
                    if (!rows[i].trim()) continue;
                    
                    const fields = parseCSVRow(rows[i]);
                    
                    if (fields.length >= 3) {
                        // Find debt by name
                        const debtName = fields[0];
                        const debt = debts.find(d => d.name === debtName);
                        
                        if (debt) {
                            const newPayment = {
                                id: newPayments.length > 0 ? Math.max(...newPayments.map(p => p.id)) + 1 : 1,
                                debt_id: debt.id,
                                amount: parseFloat(fields[1]),
                                payment_date: fields[2]
                            };
                            
                            newPayments.push(newPayment);
                        }
                    }
                }
                
                if (newPayments.length > 0) {
                    // Merge with existing or replace
                    if (document.getElementById('merge-data').checked) {
                        // Generate new IDs for imported payments
                        const maxId = payments.length > 0 ? Math.max(...payments.map(p => p.id)) : 0;
                        newPayments.forEach((payment, idx) => {
                            payment.id = maxId + idx + 1;
                        });
                        
                        payments = [...payments, ...newPayments];
                    } else {
                        payments = newPayments;
                    }
                    
                    // Update debt balances based on payments
                    recalculateDebtBalances();
                    
                    showNotification(`Imported ${newPayments.length} payments successfully`, 'success');
                    updateDashboard();
                }
            }
        };
        reader.readAsText(paymentFile);
    }
    
    closeModal('import-data-modal');
}

// Parse CSV row handling quoted fields
function parseCSVRow(row) {
    const fields = [];
    let inQuotes = false;
    let currentField = '';
    
    for (let i = 0; i < row.length; i++) {
        const char = row[i];
        
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            fields.push(currentField.trim());
            currentField = '';
        } else {
            currentField += char;
        }
    }
    
    // Add the last field
    fields.push(currentField.trim());
    
    return fields;
}

// Recalculate debt balances based on payments
function recalculateDebtBalances() {
    // Reset balances to principal
    debts.forEach(debt => {
        debt.total_paid = 0;
        debt.current_balance = debt.principal;
    });
    
    // Apply all payments
    payments.forEach(payment => {
        const debt = debts.find(d => d.id === payment.debt_id);
        if (debt) {
            debt.total_paid += payment.amount;
            debt.current_balance = debt.principal - debt.total_paid;
            if (debt.current_balance < 0) debt.current_balance = 0;
        }
    });
    
    // Recalculate monthly interest
    debts.forEach(debt => {
        debt.monthly_interest = debt.current_balance * (debt.interest_rate / 12 / 100);
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', init);