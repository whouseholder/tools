# Telco Sample Database

## Overview

A comprehensive telecommunications (telco) sample database with realistic data for testing the Text-to-SQL agent. Contains customer information, device data, network activity, plans, and financial transactions.

## Database Details

**Location:** `data/telco_sample.db`  
**Type:** SQLite3  
**Size:** ~5 MB  

## Schema

### 1. Plans Table (10 records)

Telecommunications service plans offered to customers.

**Columns:**
- `plan_id` (INTEGER, PRIMARY KEY) - Unique plan identifier
- `plan_name` (TEXT) - Name of the plan
- `plan_type` (TEXT) - Type: Prepaid, Postpaid, Business, Family, Individual
- `monthly_rate` (REAL) - Monthly subscription fee
- `data_limit_gb` (INTEGER) - Data allowance in GB (-1 = unlimited)
- `voice_minutes` (INTEGER) - Voice minutes included (-1 = unlimited)
- `sms_limit` (INTEGER) - SMS messages included (-1 = unlimited)
- `overage_rate_per_gb` (REAL) - Cost per GB over limit
- `description` (TEXT) - Plan description

**Sample Plans:**
- Unlimited Plus ($85/mo)
- Unlimited Elite ($95/mo)
- Starter 5GB ($35/mo)
- Family Unlimited ($120/mo)
- Business Pro ($150/mo)

### 2. Customers Table (500 records)

Customer account information and demographics.

**Columns:**
- `customer_id` (INTEGER, PRIMARY KEY) - Unique customer identifier
- `first_name` (TEXT) - Customer first name
- `last_name` (TEXT) - Customer last name
- `email` (TEXT, UNIQUE) - Email address
- `phone_number` (TEXT, UNIQUE) - Phone number
- `address` (TEXT) - Street address
- `city` (TEXT) - City (15 major US cities)
- `state` (TEXT) - State code
- `zip_code` (TEXT) - ZIP code
- `account_status` (TEXT) - Status: active, suspended, cancelled
- `plan_id` (INTEGER, FOREIGN KEY) - Associated plan
- `signup_date` (DATE) - Account creation date
- `credit_score` (INTEGER) - Credit score (550-850)
- `lifetime_value` (REAL) - Total revenue from customer ($500-$15,000)
- `churn_risk_score` (REAL) - Probability of churn (0.0-1.0)

**Account Status Distribution:**
- Active: 85%
- Suspended: 10%
- Cancelled: 5%

### 3. Devices Table (~517 records)

Customer devices and their information.

**Columns:**
- `device_id` (INTEGER, PRIMARY KEY) - Unique device identifier
- `customer_id` (INTEGER, FOREIGN KEY) - Device owner
- `manufacturer` (TEXT) - Device manufacturer
- `model` (TEXT) - Device model
- `purchase_date` (DATE) - Purchase date
- `purchase_price` (REAL) - Device cost ($200-$1,500)
- `device_status` (TEXT) - Status: active, inactive, lost, damaged
- `imei` (TEXT, UNIQUE) - IMEI number
- `os_version` (TEXT) - Operating system version
- `last_active_date` (DATE) - Last activity date

**Manufacturers:**
- Apple (iPhone models)
- Samsung (Galaxy series)
- Google (Pixel series)
- OnePlus, Motorola, LG, Xiaomi, Huawei

**Device Status:**
- Active: 85%
- Inactive: 10%
- Lost: 3%
- Damaged: 2%

### 4. Network Activity Table (10,000 records)

Customer network usage and activity.

**Columns:**
- `activity_id` (INTEGER, PRIMARY KEY) - Unique activity identifier
- `customer_id` (INTEGER, FOREIGN KEY) - Customer who performed activity
- `device_id` (INTEGER, FOREIGN KEY) - Device used
- `activity_date` (DATE) - Date of activity
- `activity_type` (TEXT) - Type: call, sms, data, roaming, international_call
- `duration_minutes` (REAL) - Call duration (for calls)
- `data_usage_mb` (REAL) - Data usage in MB (for data activities)
- `sms_count` (INTEGER) - Number of SMS (for SMS activities)
- `roaming` (INTEGER) - Roaming flag (0/1)
- `international` (INTEGER) - International flag (0/1)
- `tower_location` (TEXT) - Cell tower location

**Activity Distribution:**
- Calls: 30%
- SMS: 25%
- Data: 35%
- Roaming: 5%
- International: 5%

**Time Range:** Last 90 days

### 5. Transactions Table (~13,884 records)

Financial transactions and billing records.

**Columns:**
- `transaction_id` (INTEGER, PRIMARY KEY) - Unique transaction identifier
- `customer_id` (INTEGER, FOREIGN KEY) - Customer account
- `transaction_date` (DATE) - Transaction date
- `transaction_type` (TEXT) - Type of transaction
- `amount` (REAL) - Transaction amount
- `description` (TEXT) - Transaction description
- `payment_method` (TEXT) - Payment method used
- `status` (TEXT) - Transaction status

**Transaction Types:**
- `monthly_charge` - Regular monthly plan fee
- `overage` - Data/voice overage charges
- `device_payment` - Device installment payment
- `addon_purchase` - Additional service purchase
- `roaming_charge` - Roaming fees
- `international_charge` - International call fees
- `late_fee` - Late payment fee
- `payment` - Customer payment
- `refund` - Refund issued
- `adjustment` - Account adjustment

**Payment Methods:**
- auto_pay
- credit_card
- debit_card
- bank_transfer

## Sample Queries

### Marketing Questions

```sql
-- Top 10 customers by lifetime value
SELECT customer_id, first_name, last_name, lifetime_value 
FROM customers 
ORDER BY lifetime_value DESC 
LIMIT 10;

-- Which device manufacturers are most popular?
SELECT manufacturer, COUNT(*) as device_count 
FROM devices 
GROUP BY manufacturer 
ORDER BY device_count DESC;

-- Which cities have the most active customers?
SELECT city, COUNT(*) as customer_count 
FROM customers 
WHERE account_status = 'active' 
GROUP BY city 
ORDER BY customer_count DESC 
LIMIT 10;
```

### Business Operations Questions

```sql
-- Total monthly revenue from active customers
SELECT SUM(p.monthly_rate) as total_monthly_revenue 
FROM customers c 
JOIN plans p ON c.plan_id = p.plan_id 
WHERE c.account_status = 'active';

-- High churn risk customers on premium plans
SELECT c.customer_id, c.first_name, c.last_name, c.churn_risk_score, p.plan_name 
FROM customers c 
JOIN plans p ON c.plan_id = p.plan_id 
WHERE c.churn_risk_score > 0.7 AND p.monthly_rate > 80;

-- Average customer lifetime value by plan type
SELECT p.plan_type, AVG(c.lifetime_value) as avg_lifetime_value 
FROM customers c 
JOIN plans p ON c.plan_id = p.plan_id 
GROUP BY p.plan_type 
ORDER BY avg_lifetime_value DESC;
```

### Network Operations Questions

```sql
-- Average data usage per customer (last 30 days)
SELECT AVG(data_usage_mb) as avg_data_usage_mb 
FROM network_activity 
WHERE activity_date >= date('now', '-30 days') 
AND data_usage_mb IS NOT NULL;

-- Customers with international calls (last month)
SELECT COUNT(DISTINCT customer_id) as international_callers 
FROM network_activity 
WHERE international = 1 
AND activity_date >= date('now', '-30 days');
```

### Finance Questions

```sql
-- Total overage charges (last 6 months)
SELECT SUM(amount) as total_overage 
FROM transactions 
WHERE transaction_type = 'overage' 
AND transaction_date >= date('now', '-6 months');

-- Monthly recurring revenue trend (last 12 months)
SELECT strftime('%Y-%m', transaction_date) as month, 
       SUM(amount) as monthly_revenue 
FROM transactions 
WHERE transaction_type = 'monthly_charge' 
AND transaction_date >= date('now', '-12 months') 
GROUP BY month 
ORDER BY month;
```

## 10 Test Questions for Agent

### 1. Marketing: Customer Value
**Question:** "What are the top 10 customers by lifetime value?"  
**Tables:** customers  
**Expected Output:** Customer IDs, names, and lifetime values

### 2. Business Operations: Revenue
**Question:** "Show me the total monthly revenue from all active customers"  
**Tables:** customers, plans  
**Expected Output:** Single value (sum of monthly rates)

### 3. Marketing: Device Popularity
**Question:** "Which device manufacturers are most popular among our customers?"  
**Tables:** devices  
**Expected Output:** Manufacturers ranked by device count

### 4. Business Operations: Churn Risk
**Question:** "List customers with high churn risk score (above 0.7) who are on premium plans"  
**Tables:** customers, plans  
**Expected Output:** At-risk premium customers

### 5. Network Operations: Data Usage
**Question:** "What is the average data usage per customer in the last 30 days?"  
**Tables:** network_activity  
**Expected Output:** Average MB per customer

### 6. Finance: Overage Revenue
**Question:** "Show me the total overage charges collected in the last 6 months"  
**Tables:** transactions  
**Expected Output:** Sum of overage charges

### 7. Marketing: Geographic Distribution
**Question:** "Which cities have the most active customers?"  
**Tables:** customers  
**Expected Output:** Cities ranked by customer count

### 8. Business Operations: Plan Analysis
**Question:** "What is the average customer lifetime value by plan type?"  
**Tables:** customers, plans  
**Expected Output:** Plan types with average LTV

### 9. Network Operations: International Usage
**Question:** "How many customers have made international calls in the last month?"  
**Tables:** network_activity  
**Expected Output:** Count of distinct customers

### 10. Finance: Revenue Trend
**Question:** "Show me the monthly recurring revenue trend for the last 12 months"  
**Tables:** transactions, customers  
**Expected Output:** Monthly revenue over time

## Usage

### Create Database

```bash
cd text-to-sql-agent
python3 scripts/create_telco_db.py
```

### Test Questions

```bash
python3 scripts/test_telco_questions.py
```

### Query Directly

```bash
sqlite3 data/telco_sample.db
```

```sql
-- Check tables
.tables

-- Check schema
.schema customers

-- Sample query
SELECT COUNT(*) FROM customers WHERE account_status = 'active';
```

## Business Context

This database represents a mid-sized telecommunications provider with:
- **500 customers** across 15 major US cities
- **10 service plans** ranging from $25-$150/month
- **~$30,000/month** in recurring revenue
- **85% active** account status
- Mix of individual, family, and business accounts
- Device financing programs
- International and roaming services

## Analytics Use Cases

### Marketing
- Customer segmentation by value
- Churn prediction and prevention
- Device upgrade targeting
- Geographic expansion analysis

### Business Operations
- Revenue forecasting
- Plan optimization
- Customer retention strategies
- Service quality monitoring

### Network Operations
- Usage pattern analysis
- Network capacity planning
- Roaming cost management
- Tower optimization

### Finance
- Revenue recognition
- Overage analysis
- Device financing tracking
- Payment collection optimization

## Notes

- All data is synthetic and randomly generated
- Customer names, emails, and phone numbers are fictional
- IMEI numbers are random 15-digit numbers
- Dates span the last 4 years for customers
- Activity is concentrated in the last 90 days
- Transactions include full billing history from signup
