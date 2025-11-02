# Budget Analytics REST API

A production-ready RESTful backend service for financial data processing, built with Flask, PostgreSQL, and Pandas. Provides comprehensive endpoints for budget tracking, spending analysis, and financial insights.

## 🎯 Features

- **CSV Upload & Processing**: Upload CSV files with automatic validation and batch insertion into PostgreSQL
- **RESTful API Design**: 9 endpoints following REST conventions with proper HTTP methods and status codes
- **Database Integration**: PostgreSQL with SQLAlchemy ORM for robust data persistence
- **Pandas Data Processing**: Real-time data aggregation, filtering, and analysis
- **Spending Analytics**: Category-based spending breakdown with Pandas groupby operations
- **Monthly Breakdown**: Income, expenses, and savings rate calculations by month
- **Period Comparisons**: Compare financial metrics across different time periods
- **Budget Goal Management**: Set and track spending limits by category
- **Query Filtering**: Filter transactions by date range, category, and transaction type

## 🛠️ Technologies Used

- **Python 3.12**
- **Flask**: Web framework for REST API
- **PostgreSQL**: Relational database
- **SQLAlchemy**: ORM for database operations
- **Pandas**: Data processing and analysis
- **Flask-CORS**: Cross-origin resource sharing support

## 🏗️ Architecture
```
budget-api/
├── app.py              # Main Flask application with API endpoints
├── models.py           # SQLAlchemy database models
├── database.py         # Database connection and session management
├── requirements.txt    # Python dependencies
└── .env               # Environment configuration
```

## 📦 Installation
```bash
# Clone the repository
git clone https://github.com/JavadValibayov/budget-analytics-api.git
cd budget-analytics-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL database
createdb budget_db

# Configure environment variables
cp .env.example .env
# Edit .env with your database URL
```

## 🚀 Running the API
```bash
python3 app.py
```

The API will be available at `http://localhost:5001`

## 📡 API Endpoints

### Upload CSV
```bash
POST /api/upload
Content-Type: multipart/form-data

# Upload a CSV file
curl -X POST -F "file=@transactions.csv" http://localhost:5001/api/upload
```

### Get All Transactions
```bash
GET /api/transactions?start_date=2024-01-01&end_date=2024-12-31&category=Groceries

# Example
curl http://localhost:5001/api/transactions
```

### Create Transaction
```bash
POST /api/transactions
Content-Type: application/json

# Example
curl -X POST http://localhost:5001/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15",
    "category": "Groceries",
    "amount": -120.50,
    "type": "expense",
    "description": "Weekly shopping"
  }'
```

### Get Spending Analysis
```bash
GET /api/analysis?start_date=2024-01-01&end_date=2024-12-31

# Returns spending by category, totals, and savings rate
curl http://localhost:5001/api/analysis
```

### Get Monthly Breakdown
```bash
GET /api/monthly

# Returns monthly income, expenses, savings, and savings rate
curl http://localhost:5001/api/monthly
```

### Set Budget Goal
```bash
POST /api/budget-goals
Content-Type: application/json

# Example
curl -X POST http://localhost:5001/api/budget-goals \
  -H "Content-Type: application/json" \
  -d '{"category": "Groceries", "monthly_limit": 400}'
```

### Get Budget Goals
```bash
GET /api/budget-goals

curl http://localhost:5001/api/budget-goals
```

### Compare Time Periods
```bash
GET /api/comparison?period1_start=2024-01-01&period1_end=2024-01-31&period2_start=2024-02-01&period2_end=2024-02-29

# Returns income, expenses, and percentage changes between periods
curl "http://localhost:5001/api/comparison?period1_start=2024-01-01&period1_end=2024-01-31&period2_start=2024-02-01&period2_end=2024-02-29"
```

### Get Overall Statistics
```bash
GET /api/stats

curl http://localhost:5001/api/stats
```

## 📊 CSV Format

Upload CSV files with these required columns:
```csv
date,category,amount,type,description
2024-01-05,Groceries,-120.50,expense,Weekly groceries
2024-01-01,Salary,3500.00,income,Monthly salary
```

## 🔍 Key Technical Features

### Pandas Operations
- `pd.read_csv()`: CSV parsing and validation
- `df.groupby()`: Aggregating transactions by category
- `df.to_datetime()`: Date conversion and filtering
- DataFrame filtering and transformation

### Database Design
- **Transactions Table**: Stores all financial transactions
- **Budget Goals Table**: Stores category spending limits
- **Enum Types**: PostgreSQL enums for transaction types
- **Relationships**: Foreign keys and constraints for data integrity

### API Design Patterns
- RESTful resource naming conventions
- Proper HTTP status codes (200, 201, 400, 404, 500)
- Request validation and error handling
- Query parameter filtering
- JSON request/response format

## 📈 Sample API Response
```json
{
  "summary": {
    "total_income": 14000.00,
    "total_expenses": 2541.00,
    "total_savings": 11459.00,
    "savings_rate": 81.85
  },
  "category_spending": {
    "Groceries": 701.00,
    "Utilities": 630.00,
    "Entertainment": 310.00
  },
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-04-25"
  }
}
```

## 🧪 Testing
```bash
# Run all endpoint tests
python3 test_api.py
```

## 🗄️ Database Schema
```sql
-- Transactions table
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    category VARCHAR(100) NOT NULL,
    amount FLOAT NOT NULL,
    type transactiontype NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Budget goals table
CREATE TABLE budget_goals (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) UNIQUE NOT NULL,
    monthly_limit FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 👤 Author

**Javad Valibayov**
- GitHub: [@JavadValibayov](https://github.com/JavadValibayov)
- LinkedIn: [javadvalibayov](https://linkedin.com/in/javadvalibayov)

## 📄 License

This project is open source and available under the MIT License.
