# Telco Analytics Test Suite

## Overview

A complete test suite for the Text-to-SQL agent using realistic telecommunications data. Includes a sample database with 500 customers, network activity, transactions, and 10 business questions commonly asked by marketing and operations teams.

## What's Included

### 1. Sample Database
- **File:** `data/telco_sample.db`
- **Type:** SQLite3
- **Records:** 24,911 total
  - 500 customers
  - 10 service plans
  - 517 devices
  - 10,000 network activity records
  - 13,884 transactions

### 2. Test Questions
10 realistic business questions across categories:
- Marketing (4 questions)
- Business Operations (3 questions)
- Network Operations (2 questions)
- Finance (2 questions)

### 3. Scripts
- `scripts/create_telco_db.py` - Generate sample database
- `scripts/test_telco_questions.py` - Test all 10 questions

## Quick Start

### Step 1: Create Database

```bash
cd text-to-sql-agent
python3 scripts/create_telco_db.py
```

**Output:**
```
============================================================
Creating Telco Sample Database
============================================================

✓ Created 10 plans
✓ Created 500 customers
✓ Created 517 devices
✓ Created 10000 network activity records
✓ Created 13884 transactions

Database created successfully!
Location: data/telco_sample.db
```

### Step 2: Run Test Suite

```bash
python3 scripts/test_telco_questions.py
```

This will:
1. Verify database exists and has data
2. Run all 10 test questions
3. Display results in formatted tables
4. Show success/failure summary

### Step 3: Explore Data

```bash
sqlite3 data/telco_sample.db
```

```sql
-- See all tables
.tables

-- Check customer data
SELECT * FROM customers LIMIT 5;

-- Check network activity
SELECT * FROM network_activity WHERE activity_type = 'data' LIMIT 10;

-- Exit
.quit
```

## Test Questions

### Question 1: Top Customers by Value
**Question:** "What are the top 10 customers by lifetime value?"  
**Category:** Marketing  
**Expected:** List of customers sorted by lifetime value

**Sample Output:**
```
customer_id | first_name | last_name | lifetime_value
421         | Patricia   | Johnson   | 14983.31
208         | Daniel     | Johnson   | 14969.07
84          | Richard    | Anderson  | 14961.99
```

### Question 2: Total Monthly Revenue
**Question:** "Show me the total monthly revenue from all active customers"  
**Category:** Business Operations  
**Expected:** Single aggregated revenue value

**Sample Output:**
```
total_monthly_revenue
30250.00
```

### Question 3: Popular Devices
**Question:** "Which device manufacturers are most popular among our customers?"  
**Category:** Marketing  
**Expected:** Manufacturers ranked by count

**Sample Output:**
```
manufacturer | device_count
Samsung      | 142
Apple        | 128
Google       | 95
```

### Question 4: Churn Risk Analysis
**Question:** "List customers with high churn risk score (above 0.7) who are on premium plans"  
**Category:** Business Operations  
**Expected:** At-risk premium customers

**Sample Output:**
```
customer_id | name          | churn_risk | plan_name
234         | John Smith    | 0.85       | Unlimited Elite
456         | Jane Doe      | 0.78       | Premium 20GB
```

### Question 5: Data Usage Average
**Question:** "What is the average data usage per customer in the last 30 days?"  
**Category:** Network Operations  
**Expected:** Average MB usage

**Sample Output:**
```
avg_data_usage_mb
542.38
```

### Question 6: Overage Revenue
**Question:** "Show me the total overage charges collected in the last 6 months"  
**Category:** Finance  
**Expected:** Sum of overage charges

**Sample Output:**
```
total_overage
12456.78
```

### Question 7: Geographic Distribution
**Question:** "Which cities have the most active customers?"  
**Category:** Marketing  
**Expected:** Cities ranked by customer count

**Sample Output:**
```
city            | customer_count
New York        | 58
Los Angeles     | 52
Chicago         | 47
```

### Question 8: Plan Performance
**Question:** "What is the average customer lifetime value by plan type?"  
**Category:** Business Operations  
**Expected:** Plan types with average LTV

**Sample Output:**
```
plan_type  | avg_lifetime_value
Business   | 9845.23
Postpaid   | 8234.56
Family     | 7123.45
```

### Question 9: International Usage
**Question:** "How many customers have made international calls in the last month?"  
**Category:** Network Operations  
**Expected:** Count of customers

**Sample Output:**
```
international_callers
127
```

### Question 10: Revenue Trend
**Question:** "Show me the monthly recurring revenue trend for the last 12 months"  
**Category:** Finance  
**Expected:** Monthly revenue over time

**Sample Output:**
```
month    | monthly_revenue
2025-01  | 28450.00
2025-02  | 29120.00
2025-03  | 30250.00
```

## Database Schema

### Customers
- Basic demographics (name, email, phone, address)
- Account status (active, suspended, cancelled)
- Plan assignment
- Credit score
- Lifetime value
- Churn risk score

### Plans
- Plan details (name, type, rate)
- Data/voice/SMS limits
- Overage rates

### Devices
- Device details (manufacturer, model)
- Purchase info
- Status (active, inactive, lost, damaged)
- Technical details (IMEI, OS version)

### Network Activity
- Usage records (calls, SMS, data)
- Roaming and international flags
- Tower locations
- Timestamps

### Transactions
- Financial records
- Transaction types (charges, payments, refunds)
- Payment methods
- Status tracking

## Use Cases

### Marketing Analytics
- Customer segmentation
- Lifetime value analysis
- Device preference trends
- Geographic targeting

### Business Operations
- Revenue tracking
- Churn prediction
- Plan optimization
- Customer retention

### Network Operations
- Usage pattern analysis
- Capacity planning
- Roaming cost management

### Finance
- Revenue recognition
- Billing analysis
- Payment collection
- Overage tracking

## Testing with the Agent

### Option 1: Manual Testing (Recommended for SQLite)

The included test script runs manual SQL queries to demonstrate results:

```bash
python3 scripts/test_telco_questions.py
```

### Option 2: Full Agent Testing (Requires Configuration)

To test with the full LLM-powered agent:

1. **Configure for SQLite:**
   Edit `src/query/query_executor.py` to support SQLite in addition to Hive.

2. **Update Configuration:**
   ```yaml
   metadata:
     database:
       type: "sqlite"
       path: "data/telco_sample.db"
   ```

3. **Run Agent:**
   ```python
   from src.agent.agent import TextToSQLAgent
   from src.utils.config import load_config
   
   config = load_config()
   agent = TextToSQLAgent(config)
   
   result = agent.process_question(
       "What are the top 10 customers by lifetime value?"
   )
   ```

## Sample Data Characteristics

### Realistic Patterns
- Customer signup dates span 4 years
- Activity concentrated in last 90 days
- 85% active account rate (industry typical)
- Credit scores follow realistic distribution
- Device prices match market rates

### Business-Relevant Metrics
- Lifetime values: $500 - $15,000
- Churn risk scores: 0.0 - 1.0
- Monthly plans: $25 - $150
- Data usage: 10 MB - 2 GB per session

### Geographic Coverage
15 major US cities across 9 states

## Extending the Database

### Add More Customers

Edit `scripts/create_telco_db.py`:
```python
generate_customers(cursor, num_customers=1000)  # Increase from 500
```

### Add Custom Plans

```python
plans.append((
    11, 'Custom Plan', 'Postpaid', 65.00, 15, 1500, 1500, 9.00, 
    'Custom plan description'
))
```

### Generate More Activity

```python
generate_network_activity(cursor, num_records=50000)  # Increase from 10,000
```

## Troubleshooting

### Database Not Found
```bash
# Create it
python3 scripts/create_telco_db.py
```

### Empty Tables
```bash
# Verify
sqlite3 data/telco_sample.db "SELECT COUNT(*) FROM customers;"

# Recreate if needed
rm data/telco_sample.db
python3 scripts/create_telco_db.py
```

### Query Errors
- Check SQL syntax for SQLite compatibility
- Verify table and column names
- Use `.schema` in sqlite3 to see structure

## Performance Notes

- Database size: ~5 MB
- Query response time: < 100ms for most queries
- Suitable for testing and demonstration
- Can scale to larger datasets by modifying generation scripts

## Next Steps

1. ✅ Create database
2. ✅ Run test questions
3. Explore data with SQLite CLI
4. Modify questions for your use case
5. Add custom business logic
6. Integrate with the full agent workflow

## Documentation

- Full schema: `docs/TELCO_DATABASE.md`
- Agent setup: `README.md`
- API reference: `docs/API.md`

## Support

For issues or questions:
1. Check database was created: `ls -lh data/telco_sample.db`
2. Verify table counts match expected values
3. Test with simple queries first
4. Review test script output for errors
