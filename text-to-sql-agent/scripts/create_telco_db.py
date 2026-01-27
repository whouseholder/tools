"""Create sample telco database with realistic data."""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# Sample data
FIRST_NAMES = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 'William', 'Mary',
               'James', 'Patricia', 'Richard', 'Jennifer', 'Thomas', 'Linda', 'Charles', 'Elizabeth', 'Daniel', 'Susan']

LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
              'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']

CITIES = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego',
          'Dallas', 'San Jose', 'Austin', 'Jacksonville', 'Fort Worth', 'Columbus', 'Charlotte']

STATES = ['NY', 'CA', 'IL', 'TX', 'AZ', 'PA', 'TX', 'CA', 'TX', 'CA', 'TX', 'FL', 'TX', 'OH', 'NC']

DEVICE_MANUFACTURERS = ['Apple', 'Samsung', 'Google', 'OnePlus', 'Motorola', 'LG', 'Xiaomi', 'Huawei']

DEVICE_MODELS = {
    'Apple': ['iPhone 15 Pro', 'iPhone 15', 'iPhone 14 Pro', 'iPhone 14', 'iPhone 13', 'iPhone 12'],
    'Samsung': ['Galaxy S24', 'Galaxy S23', 'Galaxy S22', 'Galaxy A54', 'Galaxy A34', 'Galaxy Z Fold5'],
    'Google': ['Pixel 8 Pro', 'Pixel 8', 'Pixel 7', 'Pixel 6'],
    'OnePlus': ['OnePlus 12', 'OnePlus 11', 'OnePlus 10 Pro'],
    'Motorola': ['Moto G Power', 'Moto G Stylus', 'Edge 40'],
    'LG': ['Wing', 'Velvet', 'G8'],
    'Xiaomi': ['13 Pro', '12T', 'Redmi Note 12'],
    'Huawei': ['P60', 'Mate 50', 'Nova 11']
}

PLAN_TYPES = ['Prepaid', 'Postpaid', 'Business', 'Family', 'Individual']
PLAN_NAMES = [
    'Unlimited Plus', 'Unlimited Elite', 'Starter 5GB', 'Standard 10GB', 'Premium 20GB',
    'Family Unlimited', 'Business Pro', 'Pay As You Go', 'Value Plan', 'Premium Unlimited'
]

ACTIVITY_TYPES = ['call', 'sms', 'data', 'roaming', 'international_call']

TRANSACTION_TYPES = ['monthly_charge', 'overage', 'device_payment', 'addon_purchase', 'roaming_charge', 
                     'international_charge', 'late_fee', 'payment', 'refund', 'adjustment']

def create_database(db_path='telco_sample.db'):
    """Create telco database with schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing tables
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS network_activity")
    cursor.execute("DROP TABLE IF EXISTS devices")
    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("DROP TABLE IF EXISTS plans")
    
    # Create plans table
    cursor.execute("""
        CREATE TABLE plans (
            plan_id INTEGER PRIMARY KEY,
            plan_name TEXT NOT NULL,
            plan_type TEXT NOT NULL,
            monthly_rate REAL NOT NULL,
            data_limit_gb INTEGER,
            voice_minutes INTEGER,
            sms_limit INTEGER,
            overage_rate_per_gb REAL,
            description TEXT
        )
    """)
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone_number TEXT UNIQUE NOT NULL,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            account_status TEXT NOT NULL,
            plan_id INTEGER,
            signup_date DATE NOT NULL,
            credit_score INTEGER,
            lifetime_value REAL,
            churn_risk_score REAL,
            FOREIGN KEY (plan_id) REFERENCES plans(plan_id)
        )
    """)
    
    # Create devices table
    cursor.execute("""
        CREATE TABLE devices (
            device_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            manufacturer TEXT NOT NULL,
            model TEXT NOT NULL,
            purchase_date DATE NOT NULL,
            purchase_price REAL,
            device_status TEXT NOT NULL,
            imei TEXT UNIQUE,
            os_version TEXT,
            last_active_date DATE,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    # Create network_activity table
    cursor.execute("""
        CREATE TABLE network_activity (
            activity_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            device_id INTEGER,
            activity_date DATE NOT NULL,
            activity_type TEXT NOT NULL,
            duration_minutes REAL,
            data_usage_mb REAL,
            sms_count INTEGER,
            roaming INTEGER DEFAULT 0,
            international INTEGER DEFAULT 0,
            tower_location TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
            FOREIGN KEY (device_id) REFERENCES devices(device_id)
        )
    """)
    
    # Create transactions table
    cursor.execute("""
        CREATE TABLE transactions (
            transaction_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            transaction_date DATE NOT NULL,
            transaction_type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            payment_method TEXT,
            status TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
    conn.commit()
    return conn, cursor


def generate_plans(cursor):
    """Generate sample plans."""
    plans = [
        (1, 'Unlimited Plus', 'Postpaid', 85.00, -1, -1, -1, 0, 'Unlimited data, voice, and text'),
        (2, 'Unlimited Elite', 'Postpaid', 95.00, -1, -1, -1, 0, 'Premium unlimited with 5G access'),
        (3, 'Starter 5GB', 'Prepaid', 35.00, 5, 500, 500, 15.00, '5GB data with limited voice and text'),
        (4, 'Standard 10GB', 'Postpaid', 55.00, 10, 1000, 1000, 10.00, '10GB data package'),
        (5, 'Premium 20GB', 'Postpaid', 75.00, 20, 2000, 2000, 8.00, '20GB data with extra features'),
        (6, 'Family Unlimited', 'Family', 120.00, -1, -1, -1, 0, 'Unlimited for up to 4 lines'),
        (7, 'Business Pro', 'Business', 150.00, -1, -1, -1, 0, 'Business unlimited with priority support'),
        (8, 'Pay As You Go', 'Prepaid', 25.00, 2, 200, 200, 20.00, 'Basic prepaid plan'),
        (9, 'Value Plan', 'Individual', 45.00, 8, 800, 800, 12.00, 'Good value for moderate usage'),
        (10, 'Premium Unlimited', 'Postpaid', 105.00, -1, -1, -1, 0, 'Top-tier unlimited everything')
    ]
    
    cursor.executemany("""
        INSERT INTO plans VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, plans)
    
    print(f"✓ Created {len(plans)} plans")


def generate_customers(cursor, num_customers=500):
    """Generate sample customers."""
    customers = []
    base_date = datetime(2020, 1, 1)
    
    for i in range(1, num_customers + 1):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{i}@email.com"
        phone = f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        
        city_idx = random.randint(0, len(CITIES) - 1)
        city = CITIES[city_idx]
        state = STATES[city_idx]
        zip_code = f"{random.randint(10000, 99999)}"
        address = f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Maple', 'Park', 'Washington'])} St"
        
        account_status = random.choices(
            ['active', 'suspended', 'cancelled'],
            weights=[85, 10, 5]
        )[0]
        
        plan_id = random.randint(1, 10)
        
        # Signup date in the last 4 years
        days_ago = random.randint(0, 1460)
        signup_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        credit_score = random.randint(550, 850)
        lifetime_value = round(random.uniform(500, 15000), 2)
        churn_risk_score = round(random.uniform(0, 1), 2)
        
        customers.append((
            i, first_name, last_name, email, phone, address, city, state, zip_code,
            account_status, plan_id, signup_date, credit_score, lifetime_value, churn_risk_score
        ))
    
    cursor.executemany("""
        INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, customers)
    
    print(f"✓ Created {len(customers)} customers")


def generate_devices(cursor):
    """Generate sample devices for customers."""
    cursor.execute("SELECT customer_id FROM customers WHERE account_status = 'active'")
    active_customers = [row[0] for row in cursor.fetchall()]
    
    devices = []
    device_id = 1
    
    for customer_id in active_customers:
        # Most customers have 1 device, some have 2
        num_devices = random.choices([1, 2], weights=[80, 20])[0]
        
        for _ in range(num_devices):
            manufacturer = random.choice(DEVICE_MANUFACTURERS)
            model = random.choice(DEVICE_MODELS[manufacturer])
            
            days_ago = random.randint(30, 1095)
            purchase_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            purchase_price = round(random.uniform(200, 1500), 2)
            device_status = random.choices(
                ['active', 'inactive', 'lost', 'damaged'],
                weights=[85, 10, 3, 2]
            )[0]
            
            imei = f"{random.randint(100000000000000, 999999999999999)}"
            os_version = f"{random.randint(10, 15)}.{random.randint(0, 5)}"
            
            last_active_days = random.randint(0, 30)
            last_active_date = (datetime.now() - timedelta(days=last_active_days)).strftime('%Y-%m-%d')
            
            devices.append((
                device_id, customer_id, manufacturer, model, purchase_date, purchase_price,
                device_status, imei, os_version, last_active_date
            ))
            device_id += 1
    
    cursor.executemany("""
        INSERT INTO devices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, devices)
    
    print(f"✓ Created {len(devices)} devices")


def generate_network_activity(cursor, num_records=10000):
    """Generate sample network activity."""
    cursor.execute("""
        SELECT d.device_id, d.customer_id 
        FROM devices d 
        JOIN customers c ON d.customer_id = c.customer_id 
        WHERE d.device_status = 'active' AND c.account_status = 'active'
    """)
    active_devices = cursor.fetchall()
    
    activities = []
    
    for i in range(1, num_records + 1):
        device_id, customer_id = random.choice(active_devices)
        
        # Activity in the last 90 days
        days_ago = random.randint(0, 90)
        activity_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        activity_type = random.choices(
            ACTIVITY_TYPES,
            weights=[30, 25, 35, 5, 5]
        )[0]
        
        duration_minutes = None
        data_usage_mb = None
        sms_count = None
        roaming = random.choices([0, 1], weights=[95, 5])[0]
        international = random.choices([0, 1], weights=[97, 3])[0]
        
        if activity_type == 'call':
            duration_minutes = round(random.uniform(1, 60), 2)
        elif activity_type == 'data':
            data_usage_mb = round(random.uniform(10, 2000), 2)
        elif activity_type == 'sms':
            sms_count = random.randint(1, 50)
        elif activity_type == 'roaming':
            data_usage_mb = round(random.uniform(5, 500), 2)
            roaming = 1
        elif activity_type == 'international_call':
            duration_minutes = round(random.uniform(5, 30), 2)
            international = 1
        
        tower_location = f"{random.choice(CITIES)}-Tower-{random.randint(1, 20)}"
        
        activities.append((
            i, customer_id, device_id, activity_date, activity_type,
            duration_minutes, data_usage_mb, sms_count, roaming, international, tower_location
        ))
    
    cursor.executemany("""
        INSERT INTO network_activity VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, activities)
    
    print(f"✓ Created {len(activities)} network activity records")


def generate_transactions(cursor):
    """Generate sample transactions."""
    cursor.execute("SELECT customer_id, plan_id, signup_date FROM customers WHERE account_status = 'active'")
    customers = cursor.fetchall()
    
    cursor.execute("SELECT plan_id, monthly_rate FROM plans")
    plans = {row[0]: row[1] for row in cursor.fetchall()}
    
    transactions = []
    transaction_id = 1
    
    for customer_id, plan_id, signup_date in customers:
        signup = datetime.strptime(signup_date, '%Y-%m-%d')
        monthly_rate = plans[plan_id]
        
        # Generate monthly charges
        current_date = signup
        while current_date < datetime.now():
            trans_date = current_date.strftime('%Y-%m-%d')
            
            # Monthly charge
            transactions.append((
                transaction_id, customer_id, trans_date, 'monthly_charge', monthly_rate,
                f"Monthly service charge - Plan {plan_id}", 'auto_pay', 'completed'
            ))
            transaction_id += 1
            
            # Random overage (10% chance)
            if random.random() < 0.1:
                overage = round(random.uniform(10, 50), 2)
                transactions.append((
                    transaction_id, customer_id, trans_date, 'overage', overage,
                    'Data overage charge', 'auto_pay', 'completed'
                ))
                transaction_id += 1
            
            # Random addon purchase (5% chance)
            if random.random() < 0.05:
                addon = round(random.uniform(5, 30), 2)
                transactions.append((
                    transaction_id, customer_id, trans_date, 'addon_purchase', addon,
                    random.choice(['International calling pack', 'Extra data', 'Premium features']),
                    'credit_card', 'completed'
                ))
                transaction_id += 1
            
            current_date += timedelta(days=30)
        
        # Device payment (30% of customers)
        if random.random() < 0.3:
            device_price = round(random.uniform(500, 1200), 2)
            payment_months = random.choice([12, 24, 36])
            monthly_device_payment = round(device_price / payment_months, 2)
            
            for month in range(payment_months):
                payment_date = (signup + timedelta(days=month * 30)).strftime('%Y-%m-%d')
                if datetime.strptime(payment_date, '%Y-%m-%d') < datetime.now():
                    transactions.append((
                        transaction_id, customer_id, payment_date, 'device_payment',
                        monthly_device_payment, f'Device installment {month + 1}/{payment_months}',
                        'auto_pay', 'completed'
                    ))
                    transaction_id += 1
    
    cursor.executemany("""
        INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, transactions)
    
    print(f"✓ Created {len(transactions)} transactions")


def main():
    """Main function to create and populate the database."""
    print("=" * 60)
    print("Creating Telco Sample Database")
    print("=" * 60)
    print()
    
    db_path = 'data/telco_sample.db'
    Path('data').mkdir(exist_ok=True)
    
    conn, cursor = create_database(db_path)
    
    print("Generating sample data...")
    print()
    
    generate_plans(cursor)
    generate_customers(cursor, num_customers=500)
    generate_devices(cursor)
    generate_network_activity(cursor, num_records=10000)
    generate_transactions(cursor)
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print("Database created successfully!")
    print("=" * 60)
    print(f"Location: {db_path}")
    print()
    print("Tables created:")
    print("  - plans (10 records)")
    print("  - customers (500 records)")
    print("  - devices (~500-600 records)")
    print("  - network_activity (10,000 records)")
    print("  - transactions (~6,000-8,000 records)")
    print()


if __name__ == "__main__":
    main()
