from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd
from datetime import datetime
import os
from database import init_db, SessionLocal, engine
from models import Transaction, BudgetGoal, TransactionType
from sqlalchemy import func, extract
import traceback

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database on startup
with app.app_context():
    init_db()

# ==================== HELPER FUNCTIONS ====================

def get_transactions_as_dataframe(db, start_date=None, end_date=None):
    """Get transactions from database as Pandas DataFrame"""
    query = db.query(Transaction)
    
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    transactions = query.all()
    
    if not transactions:
        return pd.DataFrame()
    
    # Convert to DataFrame
    data = [{
        'id': t.id,
        'date': t.date,
        'category': t.category,
        'amount': t.amount,
        'type': t.type.value,
        'description': t.description
    } for t in transactions]
    
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    return df

def analyze_spending(df):
    """Analyze spending by category using Pandas"""
    if df.empty:
        return {}
    
    # Filter expenses only
    expenses = df[df['type'] == 'expense'].copy()
    expenses['amount'] = expenses['amount'].abs()
    
    # Group by category
    category_spending = expenses.groupby('category')['amount'].sum().to_dict()
    
    return category_spending

def analyze_monthly(df):
    """Analyze monthly income, expenses, and savings"""
    if df.empty:
        return []
    
    df['month'] = df['date'].dt.to_period('M')
    
    # Separate income and expenses
    income_df = df[df['type'] == 'income'].copy()
    expense_df = df[df['type'] == 'expense'].copy()
    expense_df['amount'] = expense_df['amount'].abs()
    
    # Group by month
    monthly_income = income_df.groupby('month')['amount'].sum()
    monthly_expenses = expense_df.groupby('month')['amount'].sum()
    
    # Combine results
    result = []
    for month in pd.period_range(start=df['date'].min(), end=df['date'].max(), freq='M'):
        income = monthly_income.get(month, 0)
        expenses = monthly_expenses.get(month, 0)
        savings = income - expenses
        savings_rate = (savings / income * 100) if income > 0 else 0
        
        result.append({
            'month': str(month),
            'income': round(income, 2),
            'expenses': round(expenses, 2),
            'savings': round(savings, 2),
            'savings_rate': round(savings_rate, 2)
        })
    
    return result

# ==================== API ENDPOINTS ====================

@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        'message': 'Budget Analytics API',
        'version': '1.0',
        'endpoints': {
            'POST /api/upload': 'Upload CSV file',
            'GET /api/transactions': 'Get all transactions',
            'POST /api/transactions': 'Create a transaction',
            'GET /api/analysis': 'Get spending analysis',
            'GET /api/monthly': 'Get monthly breakdown',
            'POST /api/budget-goals': 'Set budget goals',
            'GET /api/budget-goals': 'Get all budget goals',
            'GET /api/comparison': 'Compare time periods'
        }
    })

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    """Upload and process CSV file"""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only CSV files are allowed'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read CSV with Pandas
        df = pd.read_csv(filepath)
        
        # Validate required columns
        required_columns = ['date', 'category', 'amount', 'type']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': f'CSV must contain columns: {required_columns}'}), 400
        
        # Process and insert into database
        db = SessionLocal()
        transactions_added = 0
        
        for _, row in df.iterrows():
            transaction = Transaction(
                date=pd.to_datetime(row['date']),
                category=row['category'],
                amount=float(row['amount']),
                type=TransactionType.INCOME if row['type'] == 'income' else TransactionType.EXPENSE,
                description=row.get('description', '')
            )
            db.add(transaction)
            transactions_added += 1
        
        db.commit()
        db.close()
        
        # Clean up uploaded file
        os.remove(filepath)
        
        return jsonify({
            'message': 'CSV uploaded successfully',
            'transactions_added': transactions_added
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions with optional filtering"""
    try:
        db = SessionLocal()
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        category = request.args.get('category')
        transaction_type = request.args.get('type')
        
        # Build query
        query = db.query(Transaction)
        
        if start_date:
            query = query.filter(Transaction.date >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Transaction.date <= datetime.strptime(end_date, '%Y-%m-%d'))
        if category:
            query = query.filter(Transaction.category == category)
        if transaction_type:
            query = query.filter(Transaction.type == TransactionType[transaction_type.upper()])
        
        transactions = query.all()
        db.close()
        
        return jsonify({
            'count': len(transactions),
            'transactions': [t.to_dict() for t in transactions]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['POST'])
def create_transaction():
    """Create a new transaction"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['date', 'category', 'amount', 'type']
        if not all(field in data for field in required_fields):
            return jsonify({'error': f'Required fields: {required_fields}'}), 400
        
        db = SessionLocal()
        
        transaction = Transaction(
            date=datetime.strptime(data['date'], '%Y-%m-%d'),
            category=data['category'],
            amount=float(data['amount']),
            type=TransactionType.INCOME if data['type'] == 'income' else TransactionType.EXPENSE,
            description=data.get('description', '')
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        result = transaction.to_dict()
        db.close()
        
        return jsonify({
            'message': 'Transaction created successfully',
            'transaction': result
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    """Get spending analysis by category"""
    try:
        db = SessionLocal()
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get data as DataFrame
        df = get_transactions_as_dataframe(db, start_date, end_date)
        db.close()
        
        if df.empty:
            return jsonify({'error': 'No transactions found'}), 404
        
        # Analyze spending
        category_spending = analyze_spending(df)
        
        # Calculate totals
        total_income = df[df['type'] == 'income']['amount'].sum()
        total_expenses = df[df['type'] == 'expense']['amount'].abs().sum()
        total_savings = total_income - total_expenses
        
        return jsonify({
            'summary': {
                'total_income': round(total_income, 2),
                'total_expenses': round(total_expenses, 2),
                'total_savings': round(total_savings, 2),
                'savings_rate': round((total_savings / total_income * 100) if total_income > 0 else 0, 2)
            },
            'category_spending': category_spending,
            'date_range': {
                'start': df['date'].min().strftime('%Y-%m-%d'),
                'end': df['date'].max().strftime('%Y-%m-%d')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monthly', methods=['GET'])
def get_monthly_analysis():
    """Get monthly breakdown"""
    try:
        db = SessionLocal()
        
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get data as DataFrame
        df = get_transactions_as_dataframe(db, start_date, end_date)
        db.close()
        
        if df.empty:
            return jsonify({'error': 'No transactions found'}), 404
        
        # Analyze monthly
        monthly_data = analyze_monthly(df)
        
        return jsonify({
            'monthly_breakdown': monthly_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budget-goals', methods=['GET'])
def get_budget_goals():
    """Get all budget goals"""
    try:
        db = SessionLocal()
        goals = db.query(BudgetGoal).all()
        db.close()
        
        return jsonify({
            'count': len(goals),
            'budget_goals': [g.to_dict() for g in goals]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budget-goals', methods=['POST'])
def set_budget_goal():
    """Set or update a budget goal"""
    try:
        data = request.get_json()
        
        if 'category' not in data or 'monthly_limit' not in data:
            return jsonify({'error': 'Required fields: category, monthly_limit'}), 400
        
        db = SessionLocal()
        
        # Check if goal exists
        existing_goal = db.query(BudgetGoal).filter_by(category=data['category']).first()
        
        if existing_goal:
            # Update existing goal
            existing_goal.monthly_limit = float(data['monthly_limit'])
            existing_goal.updated_at = datetime.utcnow()
            message = 'Budget goal updated successfully'
        else:
            # Create new goal
            goal = BudgetGoal(
                category=data['category'],
                monthly_limit=float(data['monthly_limit'])
            )
            db.add(goal)
            message = 'Budget goal created successfully'
        
        db.commit()
        
        goal = db.query(BudgetGoal).filter_by(category=data['category']).first()
        result = goal.to_dict()
        db.close()
        
        return jsonify({
            'message': message,
            'budget_goal': result
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/comparison', methods=['GET'])
def compare_periods():
    """Compare two time periods"""
    try:
        # Get query parameters
        p1_start = request.args.get('period1_start')
        p1_end = request.args.get('period1_end')
        p2_start = request.args.get('period2_start')
        p2_end = request.args.get('period2_end')
        
        if not all([p1_start, p1_end, p2_start, p2_end]):
            return jsonify({'error': 'Required parameters: period1_start, period1_end, period2_start, period2_end'}), 400
        
        db = SessionLocal()
        
        # Get period 1 data
        df1 = get_transactions_as_dataframe(db, p1_start, p1_end)
        p1_income = df1[df1['type'] == 'income']['amount'].sum() if not df1.empty else 0
        p1_expenses = df1[df1['type'] == 'expense']['amount'].abs().sum() if not df1.empty else 0
        
        # Get period 2 data
        df2 = get_transactions_as_dataframe(db, p2_start, p2_end)
        p2_income = df2[df2['type'] == 'income']['amount'].sum() if not df2.empty else 0
        p2_expenses = df2[df2['type'] == 'expense']['amount'].abs().sum() if not df2.empty else 0
        
        db.close()
        
        # Calculate changes
        income_change = p2_income - p1_income
        expense_change = p2_expenses - p1_expenses
        income_change_pct = (income_change / p1_income * 100) if p1_income > 0 else 0
        expense_change_pct = (expense_change / p1_expenses * 100) if p1_expenses > 0 else 0
        
        return jsonify({
            'period1': {
                'date_range': f"{p1_start} to {p1_end}",
                'income': round(p1_income, 2),
                'expenses': round(p1_expenses, 2),
                'savings': round(p1_income - p1_expenses, 2)
            },
            'period2': {
                'date_range': f"{p2_start} to {p2_end}",
                'income': round(p2_income, 2),
                'expenses': round(p2_expenses, 2),
                'savings': round(p2_income - p2_expenses, 2)
            },
            'changes': {
                'income_change': round(income_change, 2),
                'income_change_pct': round(income_change_pct, 2),
                'expense_change': round(expense_change, 2),
                'expense_change_pct': round(expense_change_pct, 2)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        db = SessionLocal()
        
        total_transactions = db.query(Transaction).count()
        total_income = db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == TransactionType.INCOME
        ).scalar() or 0
        total_expenses = db.query(func.sum(Transaction.amount)).filter(
            Transaction.type == TransactionType.EXPENSE
        ).scalar() or 0
        
        categories = db.query(Transaction.category).distinct().count()
        
        db.close()
        
        return jsonify({
            'total_transactions': total_transactions,
            'total_income': round(total_income, 2),
            'total_expenses': round(abs(total_expenses), 2),
            'net_savings': round(total_income + total_expenses, 2),
            'unique_categories': categories
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)