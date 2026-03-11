#!/usr/bin/env python3
"""Personal finance database: import credit card CSVs, categorize, query."""

import csv
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = VAULT_ROOT / "Finance" / "finance.db"
CSV_ROOT = VAULT_ROOT / "Finance" / "credit-card"
AMAZON_CSV_ROOT = Path.home() / "Dropbox" / "0-FinancialStatements" / "amazon"
PAYSLIP_ROOT = VAULT_ROOT / "Finance" / "payslips"
TAX_ROOT = VAULT_ROOT / "Finance" / "tax"
FIDELITY_ROOT = VAULT_ROOT / "Finance" / "fidelity-accounts"
SOFI_ROOT = VAULT_ROOT / "Finance" / "sofi-loan"
BECU_ROOT = VAULT_ROOT / "Finance" / "becu"
WF_CAR_ROOT = VAULT_ROOT / "Finance" / "wellsfargo-car-loan"
RULES_BACKUP_PATH = VAULT_ROOT / "Finance" / "categorization_rules.json"
PENDING_TXN_PATH = VAULT_ROOT / "Finance" / "pending-transactions.yaml"
ISSUES_PATH = VAULT_ROOT / "Finance" / "pipeline-issues.md"

SCRIPTS_DIR = Path(__file__).resolve().parent
VENV_PYTHON = str(VAULT_ROOT / "Scripts" / "venv" / "bin" / "python3")

PROCESSING_LOGS = {
    "CC Statements": VAULT_ROOT / "Finance" / "credit-card" / "processing_log.json",
    "Tax Documents": VAULT_ROOT / "Finance" / "tax" / "processing_log.json",
    "Payslips": VAULT_ROOT / "Finance" / "payslips" / "processing_log.json",
    "Fidelity": VAULT_ROOT / "Finance" / "fidelity-accounts" / "processing_log.json",
    "SoFi Loan": VAULT_ROOT / "Finance" / "sofi-loan" / "processing_log.json",
    "BECU": VAULT_ROOT / "Finance" / "becu" / "processing_log.json",
    "WF Car Loan": VAULT_ROOT / "Finance" / "wellsfargo-car-loan" / "processing_log.json",
}

SOURCE_DIRS = {
    "CC Statements": Path.home() / "Dropbox" / "0-FinancialStatements" / "credit-cards",
    "Tax Documents": [
        Path.home() / "Dropbox" / "1-Tax" / "2-prepare",
        Path.home() / "Dropbox" / "1-Tax" / "3-archive",
    ],
    "Payslips": Path.home() / "Dropbox" / "0-FinancialStatements" / "payslips",
    "Fidelity": Path.home() / "Dropbox" / "0-FinancialStatements" / "fidelity-accounts",
    "SoFi Loan": Path.home() / "Dropbox" / "0-FinancialStatements" / "sofi-loan",
    "BECU": Path.home() / "Dropbox" / "0-FinancialStatements" / "BECU",
    "WF Car Loan": Path.home() / "Dropbox" / "0-FinancialStatements" / "wellsfargo-car-loan",
}

INGEST_SCRIPTS = [
    ("CC Statements", [VENV_PYTHON, str(SCRIPTS_DIR / "ingest_cc_statements.py"), "--run"]),
    ("Tax Documents", [VENV_PYTHON, str(SCRIPTS_DIR / "ingest_tax.py"), "--run"]),
    ("Payslips", [VENV_PYTHON, str(SCRIPTS_DIR / "ingest_payslips.py"), "--run"]),
    ("Fidelity", [VENV_PYTHON, str(SCRIPTS_DIR / "ingest_fidelity_accounts.py"), "run"]),
    ("SoFi Loan", [VENV_PYTHON, str(SCRIPTS_DIR / "ingest_sofi_loan.py"), "run"]),
    ("BECU", [VENV_PYTHON, str(SCRIPTS_DIR / "ingest_becu.py"), "run"]),
    ("WF Car Loan", [VENV_PYTHON, str(SCRIPTS_DIR / "ingest_wellsfargo_car.py"), "run"]),
]

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    UNIQUE(name, parent_id)
);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    source_file TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    is_transfer INTEGER DEFAULT 0,
    notes TEXT,
    UNIQUE(source_file, source_row)
);

CREATE TABLE IF NOT EXISTS categorization_rules (
    id INTEGER PRIMARY KEY,
    pattern TEXT NOT NULL,
    pattern_type TEXT DEFAULT 'keyword',
    category_id INTEGER NOT NULL REFERENCES categories(id),
    priority INTEGER DEFAULT 100,
    source TEXT DEFAULT 'manual',
    UNIQUE(pattern, pattern_type)
);

CREATE TABLE IF NOT EXISTS import_log (
    id INTEGER PRIMARY KEY,
    source_file TEXT NOT NULL UNIQUE,
    transaction_count INTEGER,
    imported_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_txn_category ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_txn_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_txn_source ON transactions(source_file);

CREATE TABLE IF NOT EXISTS trips (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    trip_type TEXT,
    booking_method TEXT,
    location_keywords TEXT,
    trip_file TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS amazon_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    order_timestamp TEXT,
    asin TEXT NOT NULL,
    product_name TEXT,
    product_condition TEXT,
    quantity INTEGER,
    unit_price REAL,
    unit_price_tax REAL,
    subtotal REAL,
    subtotal_tax REAL,
    shipping_charge REAL,
    total_discount REAL,
    total_amount REAL,
    currency TEXT DEFAULT 'USD',
    payment_method TEXT,
    card_type TEXT,
    card_last4 TEXT,
    order_status TEXT,
    ship_date TEXT,
    shipping_address TEXT,
    shipping_option TEXT,
    website TEXT,
    category_id INTEGER REFERENCES categories(id),
    notes TEXT,
    UNIQUE(order_id, asin)
);

CREATE INDEX IF NOT EXISTS idx_amazon_date ON amazon_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_amazon_card ON amazon_orders(card_last4);
CREATE INDEX IF NOT EXISTS idx_amazon_category ON amazon_orders(category_id);

CREATE TABLE IF NOT EXISTS payslips (
    id INTEGER PRIMARY KEY,
    employer TEXT NOT NULL,
    employee_id TEXT,
    pay_period_start TEXT NOT NULL,
    pay_period_end TEXT NOT NULL,
    pay_date TEXT NOT NULL,
    pay_type TEXT NOT NULL,
    hours_worked REAL,
    gross_pay REAL NOT NULL,
    pre_tax_deductions REAL,
    employee_taxes REAL,
    post_tax_deductions REAL,
    net_pay REAL NOT NULL,
    total_earnings REAL,
    total_employer_benefits REAL,
    deposit_amount REAL,
    source_file TEXT NOT NULL,
    source_pages TEXT,
    processed_at TEXT,
    UNIQUE(employer, pay_date, pay_period_start, pay_period_end, gross_pay)
);

CREATE TABLE IF NOT EXISTS payslip_line_items (
    id INTEGER PRIMARY KEY,
    payslip_id INTEGER NOT NULL REFERENCES payslips(id) ON DELETE CASCADE,
    section TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    ytd REAL,
    dates TEXT,
    hours REAL,
    rate REAL
);

CREATE INDEX IF NOT EXISTS idx_payslip_date ON payslips(pay_date);
CREATE INDEX IF NOT EXISTS idx_payslip_employer ON payslips(employer);
CREATE INDEX IF NOT EXISTS idx_payslip_type ON payslips(pay_type);
CREATE INDEX IF NOT EXISTS idx_payslip_items ON payslip_line_items(payslip_id);

CREATE TABLE IF NOT EXISTS tax_documents (
    id INTEGER PRIMARY KEY,
    form_type TEXT NOT NULL,
    tax_year INTEGER NOT NULL,
    source_folder TEXT NOT NULL,
    payer_name TEXT,
    payer_tin TEXT,
    recipient_ssn_last4 TEXT,
    filing_status TEXT,
    source_file TEXT NOT NULL,
    yaml_file TEXT NOT NULL,
    processed_at TEXT,
    validation_ok INTEGER DEFAULT 1,
    UNIQUE(yaml_file)
);

CREATE TABLE IF NOT EXISTS tax_line_items (
    id INTEGER PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES tax_documents(id) ON DELETE CASCADE,
    box_name TEXT NOT NULL,
    box_value REAL,
    box_text TEXT,
    box_bool INTEGER
);

CREATE INDEX IF NOT EXISTS idx_tax_doc_year ON tax_documents(tax_year);
CREATE INDEX IF NOT EXISTS idx_tax_doc_type ON tax_documents(form_type);
CREATE INDEX IF NOT EXISTS idx_tax_doc_folder ON tax_documents(source_folder);
CREATE INDEX IF NOT EXISTS idx_tax_items_doc ON tax_line_items(doc_id);
CREATE INDEX IF NOT EXISTS idx_tax_items_box ON tax_line_items(box_name);

CREATE TABLE IF NOT EXISTS fidelity_accounts (
    id INTEGER PRIMARY KEY,
    account_number TEXT UNIQUE NOT NULL,
    account_name TEXT,
    account_type TEXT NOT NULL,
    tax_status TEXT NOT NULL,
    beneficiary TEXT NOT NULL,
    first_seen TEXT,
    last_seen TEXT
);

CREATE TABLE IF NOT EXISTS fidelity_portfolio_snapshots (
    id INTEGER PRIMARY KEY,
    statement_date TEXT UNIQUE NOT NULL,
    beginning_value REAL,
    ending_value REAL,
    additions REAL,
    subtractions REAL,
    change_in_investment_value REAL,
    income_taxable REAL,
    income_tax_deferred REAL,
    income_tax_free REAL,
    income_total REAL,
    source_file TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fidelity_monthly_snapshots (
    id INTEGER PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES fidelity_accounts(id),
    statement_date TEXT NOT NULL,
    beginning_value REAL,
    ending_value REAL,
    additions REAL,
    subtractions REAL,
    change_in_investment_value REAL,
    deposits REAL,
    withdrawals REAL,
    exchanges_in REAL,
    exchanges_out REAL,
    transfers_between_fidelity REAL,
    income_dividends REAL,
    income_interest REAL,
    income_total REAL,
    source_file TEXT NOT NULL,
    UNIQUE(account_id, statement_date)
);

CREATE TABLE IF NOT EXISTS fidelity_holdings (
    id INTEGER PRIMARY KEY,
    snapshot_id INTEGER NOT NULL REFERENCES fidelity_monthly_snapshots(id),
    symbol TEXT,
    description TEXT,
    asset_class TEXT,
    quantity REAL,
    price REAL,
    market_value REAL NOT NULL,
    cost_basis REAL,
    unrealized_gain_loss REAL
);

CREATE INDEX IF NOT EXISTS idx_fidelity_snap_date ON fidelity_monthly_snapshots(statement_date);
CREATE INDEX IF NOT EXISTS idx_fidelity_snap_acct ON fidelity_monthly_snapshots(account_id);
CREATE INDEX IF NOT EXISTS idx_fidelity_hold_snap ON fidelity_holdings(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_fidelity_port_date ON fidelity_portfolio_snapshots(statement_date);

CREATE TABLE IF NOT EXISTS fidelity_cma_transactions (
    id INTEGER PRIMARY KEY,
    date TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    payee TEXT,
    category TEXT,
    is_transfer INTEGER DEFAULT 0,
    source_file TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    UNIQUE(source_file, source_row)
);
CREATE INDEX IF NOT EXISTS idx_cma_txn_date ON fidelity_cma_transactions(date);
CREATE INDEX IF NOT EXISTS idx_cma_txn_cat ON fidelity_cma_transactions(category);

CREATE TABLE IF NOT EXISTS sofi_loan_statements (
    id INTEGER PRIMARY KEY,
    statement_month TEXT NOT NULL UNIQUE,
    current_balance REAL NOT NULL,
    credit_limit REAL,
    payment_due REAL NOT NULL,
    principal REAL NOT NULL,
    interest REAL NOT NULL,
    fees REAL DEFAULT 0,
    ytd_interest_paid REAL,
    last_txn_date TEXT,
    last_txn_total REAL,
    source_file TEXT NOT NULL,
    processed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sofi_stmt_month ON sofi_loan_statements(statement_month);

CREATE TABLE IF NOT EXISTS becu_checking_statements (
    id INTEGER PRIMARY KEY,
    statement_month TEXT NOT NULL UNIQUE,
    period_start TEXT,
    period_end TEXT,
    beginning_balance REAL NOT NULL,
    withdrawals_fees REAL,
    deposits REAL,
    dividends_interest REAL,
    ending_balance REAL NOT NULL,
    apy REAL,
    avg_daily_balance REAL,
    ytd_dividends REAL,
    num_deposits INTEGER,
    num_withdrawals INTEGER,
    source_file TEXT NOT NULL,
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS becu_checking_transactions (
    id INTEGER PRIMARY KEY,
    statement_id INTEGER NOT NULL REFERENCES becu_checking_statements(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS becu_heloc_statements (
    id INTEGER PRIMARY KEY,
    statement_month TEXT NOT NULL UNIQUE,
    period_start TEXT,
    period_end TEXT,
    previous_balance REAL NOT NULL,
    payments REAL,
    other_credits REAL,
    advances REAL,
    fees_charged REAL,
    interest_charged REAL,
    new_balance REAL NOT NULL,
    credit_limit REAL,
    available_credit REAL,
    apr REAL,
    ytd_interest REAL,
    ytd_fees REAL,
    minimum_payment REAL,
    payment_date TEXT,
    total_interest_this_period REAL,
    source_file TEXT NOT NULL,
    processed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_becu_check_month ON becu_checking_statements(statement_month);
CREATE INDEX IF NOT EXISTS idx_becu_check_txn ON becu_checking_transactions(statement_id);
CREATE INDEX IF NOT EXISTS idx_becu_heloc_month ON becu_heloc_statements(statement_month);

CREATE TABLE IF NOT EXISTS wellsfargo_car_statements (
    id INTEGER PRIMARY KEY,
    statement_month TEXT NOT NULL UNIQUE,
    statement_date TEXT NOT NULL,
    account_number TEXT NOT NULL,
    vehicle TEXT,
    interest_rate REAL,
    monthly_payment REAL,
    maturity_date TEXT,
    daily_interest REAL,
    payoff_amount REAL,
    payoff_date TEXT,
    payment_due_date TEXT,
    total_amount_due REAL,
    principal_paid REAL,
    interest_paid REAL,
    extra_principal REAL,
    total_paid REAL,
    ytd_interest_paid REAL,
    yaml_file TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_wf_car_stmt_month ON wellsfargo_car_statements(statement_month);
"""

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

ACCOUNTS = [
    ("apple-card", "Apple Card"),
    ("chase-prime-1158", "Chase Prime"),
    ("chase-sapphire-2341", "Chase Sapphire"),
    ("chase-freedom-1350", "Chase Freedom"),
    ("fidelity-credit-card", "Fidelity Credit Card"),
    ("bofa-atmos-7982", "BofA Atmos Rewards"),
    ("bofa-rewards-visa", "BofA Rewards Visa Signature"),
]

# (name, parent_name_or_None)
CATEGORIES = [
    # Top-level
    ("Food & Drink", None),
    ("Home & Utilities", None),
    ("Transportation", None),
    ("Shopping", None),
    ("Health & Wellness", None),
    ("Kids & Family", None),
    ("Subscriptions", None),
    ("Travel", None),
    ("Legal & Professional", None),
    ("Personal Care", None),
    ("International", None),
    ("Transfers", None),
    # Food & Drink
    ("Groceries", "Food & Drink"),
    ("Restaurants", "Food & Drink"),
    ("Coffee", "Food & Drink"),
    ("Fast Food", "Food & Drink"),
    ("Food Delivery", "Food & Drink"),
    # Home & Utilities
    ("Internet & Phone", "Home & Utilities"),
    ("Home Services", "Home & Utilities"),
    ("Home Improvement", "Home & Utilities"),
    # Transportation
    ("Gas", "Transportation"),
    ("Ride Share", "Transportation"),
    ("Parking", "Transportation"),
    ("Car Maintenance", "Transportation"),
    ("Flights", "Travel"),
    # Shopping
    ("Amazon", "Shopping"),
    ("Online Shopping", "Shopping"),
    ("Clothing", "Shopping"),
    # Health & Wellness
    ("Medical", "Health & Wellness"),
    ("Fitness", "Health & Wellness"),
    ("Therapy", "Health & Wellness"),
    ("Pharmacy", "Health & Wellness"),
    # Kids & Family
    ("Childcare", "Kids & Family"),
    ("Kids Activities", "Kids & Family"),
    ("Kids Education", "Kids & Family"),
    ("Orthodontics", "Kids & Family"),
    # Subscriptions
    ("Media", "Subscriptions"),
    ("Software", "Subscriptions"),
    # Travel
    ("Lodging", "Travel"),
    ("Rental Car", "Travel"),
    # Legal & Professional
    ("Legal", "Legal & Professional"),
    # Personal Care
    ("Haircuts", "Personal Care"),
    ("Massage", "Personal Care"),
    ("Pet Care", "Personal Care"),
    # Insurance (new top-level)
    ("Insurance", None),
    # International
    ("China Shopping", "International"),
    ("Foreign Fees", "International"),
    # Transfers
    ("Card Payments", "Transfers"),
    ("ACH Transfers", "Transfers"),
    ("Interest Charges", "Transfers"),
]

# (pattern, category_name, priority)  — lower priority = matched first
RULES = [
    # Transfers (highest priority — must override everything)
    ("AUTOMATIC PAYMENT", "Card Payments", 10),
    ("PAYMENT THANK YOU", "Card Payments", 10),
    ("Payment Thank You", "Card Payments", 10),
    ("ACH Deposit", "ACH Transfers", 10),
    ("ACH DEPOSIT", "ACH Transfers", 10),
    ("INTEREST CHARGE", "Interest Charges", 10),
    ("BALANCE REFUND", "ACH Transfers", 10),
    # Groceries
    ("QFC", "Groceries", 100),
    ("TRADER JOE", "Groceries", 100),
    ("COSTCO WHSE", "Groceries", 100),
    ("SAFEWAY", "Groceries", 100),
    ("WHOLE FOODS", "Groceries", 100),
    ("ASIAN FAMILY MARKET", "Groceries", 100),
    ("PCC COMMUNITY", "Groceries", 100),
    ("METROPOLITAN MARKET", "Groceries", 100),
    ("FRED MEYER", "Groceries", 100),
    ("UWAJIMAYA", "Groceries", 100),
    ("H MART", "Groceries", 100),
    # Coffee
    ("STARBUCKS", "Coffee", 100),
    ("ISSAQUAH COFFEE", "Coffee", 100),
    # Fast Food
    ("MCDONALD", "Fast Food", 100),
    ("CHIPOTLE", "Fast Food", 100),
    ("MOD PIZZA", "Fast Food", 100),
    ("HABIT BURGER", "Fast Food", 100),
    ("JIMMY JOHN", "Fast Food", 100),
    ("CHICK-FIL-A", "Fast Food", 100),
    ("PANDA EXPRESS", "Fast Food", 100),
    # Food Delivery
    ("GRUBHUB", "Food Delivery", 100),
    ("UBER EATS", "Food Delivery", 100),
    ("INSTACART", "Food Delivery", 100),
    ("DOORDASH", "Food Delivery", 100),
    # Internet & Phone
    ("COMCAST", "Internet & Phone", 100),
    ("STARLINK", "Internet & Phone", 100),
    ("GOOGLE *FI", "Internet & Phone", 100),
    ("Google Fi", "Internet & Phone", 100),
    # Home Services
    ("REPUBLIC SERVICES", "Home Services", 100),
    ("CSC SERVICEWORK", "Home Services", 100),
    # Home Improvement
    ("HOME DEPOT", "Home Improvement", 100),
    ("LOWE'S", "Home Improvement", 100),
    ("LOWES", "Home Improvement", 100),
    # Gas
    ("CHEVRON", "Gas", 100),
    ("SHELL OIL", "Gas", 100),
    ("76 -", "Gas", 100),
    ("ARCO", "Gas", 100),
    # Ride Share
    ("UBER TRIP", "Ride Share", 100),
    ("UBER *TRIP", "Ride Share", 100),
    ("LYFT", "Ride Share", 100),
    # Parking
    ("PARKWHIZ", "Parking", 100),
    ("IMPARK", "Parking", 100),
    ("SP PLUS", "Parking", 100),
    ("MASTERPARK", "Parking", 100),
    # Car Maintenance
    ("PLATEAU MOTORS", "Car Maintenance", 100),
    # Flights
    ("ALASKA AIR", "Flights", 100),
    ("DELTA AIR", "Flights", 100),
    ("UNITED AIR", "Flights", 100),
    ("SOUTHWEST", "Flights", 100),
    # Amazon
    ("AMZN", "Amazon", 100),
    ("AMAZON", "Amazon", 100),
    # Clothing
    ("REI ", "Clothing", 100),
    ("LULULEMON", "Clothing", 100),
    ("ARC'TERYX", "Clothing", 100),
    ("ARCTERYX", "Clothing", 100),
    # Medical
    ("VIRGINIA MASON", "Medical", 100),
    ("BALANCE PHYSICAL", "Medical", 100),
    ("OVERLAKE", "Medical", 100),
    # Fitness
    ("YMCA", "Fitness", 100),
    ("PILATES", "Fitness", 100),
    # Therapy
    ("ERIN D THERAPY", "Therapy", 100),
    ("CENTERED MIND", "Therapy", 100),
    # Pharmacy
    ("RITE AID", "Pharmacy", 100),
    ("CVS", "Pharmacy", 100),
    ("WALGREENS", "Pharmacy", 100),
    # Childcare
    ("CARE.COM", "Childcare", 100),
    ("GO AU PAIR", "Childcare", 100),
    ("YUXIN SUN", "Childcare", 100),
    # Kids Activities
    ("SNO KING ICE", "Kids Activities", 100),
    ("BLAZE ROBOTICS", "Kids Activities", 100),
    ("MEL SCIENCE", "Kids Activities", 100),
    # Kids Education
    ("ISSAQUAH SD", "Kids Education", 100),
    ("DOC NETWORK", "Kids Education", 100),
    # Orthodontics
    ("SAMMAMISH ORTHO", "Orthodontics", 100),
    # Media subscriptions
    ("APPLE.COM/BILL", "Media", 100),
    ("NYTIMES", "Media", 100),
    ("NY TIMES", "Media", 100),
    ("WSJ", "Media", 100),
    ("NETFLIX", "Media", 100),
    ("PEACOCK", "Media", 100),
    ("HULU", "Media", 100),
    ("SPOTIFY", "Media", 100),
    ("YOUTUBE", "Media", 100),
    # Software subscriptions
    ("ADOBE", "Software", 100),
    ("JETBRAINS", "Software", 100),
    ("1PASSWORD", "Software", 100),
    ("CURSOR", "Software", 100),
    ("BACKBLAZE", "Software", 100),
    ("GITHUB", "Software", 100),
    ("OPENAI", "Software", 100),
    # Lodging
    ("AIRBNB", "Lodging", 100),
    ("MARRIOTT", "Lodging", 100),
    ("HILTON", "Lodging", 100),
    ("HYATT", "Lodging", 100),
    # Rental Car
    ("ALAMO", "Rental Car", 100),
    ("ENTERPRISE RENT", "Rental Car", 100),
    # Legal
    ("DELLINO LAW", "Legal", 100),
    ("LEGALZOOM", "Legal", 100),
    ("YU DING PLLC", "Legal", 100),
    # Haircuts
    ("GREAT CLIPS", "Haircuts", 100),
    # Pet Care
    ("PLATEAU PET", "Pet Care", 100),
    # International
    ("TAOBAO", "China Shopping", 100),
    ("WECHAT", "China Shopping", 100),
    ("TENCENT", "China Shopping", 100),
    ("FRGN TRANS FEE", "Foreign Fees", 100),
    ("FOREIGN TRANSACTION", "Foreign Fees", 100),
    # --- Additional rules based on uncategorized scan ---
    # Restaurants
    ("SAMMAMISH CAFE", "Restaurants", 100),
    ("LA CASITA", "Restaurants", 100),
    ("NUODLE", "Restaurants", 100),
    ("TST*", "Restaurants", 100),
    ("SQ *SOMISOMI", "Restaurants", 100),
    ("ISSAQUAH BREWHOUSE", "Restaurants", 100),
    ("GREAT WOLF LDG", "Lodging", 100),
    ("DERU MARKET", "Restaurants", 100),
    ("SQ *LUCKY ENVELOPE", "Restaurants", 100),
    ("SQ *ASIAN COOKHOUSE", "Restaurants", 100),
    ("FACING EAST", "Restaurants", 100),
    ("DIN TAI FUNG", "Restaurants", 100),
    ("CACTUS", "Restaurants", 100),
    ("TRIPLE XXX", "Restaurants", 100),
    ("FATBURGER", "Restaurants", 100),
    ("ZEEKS PIZZA", "Restaurants", 100),
    ("BOILING POINT", "Restaurants", 100),
    ("SZECHUAN CHEF", "Restaurants", 100),
    ("TAQUERIA", "Restaurants", 100),
    ("THAI", "Restaurants", 120),
    ("BAMBOO GARDEN", "Restaurants", 100),
    ("SQ *BA BAR", "Restaurants", 100),
    ("WILD GINGER", "Restaurants", 100),
    ("SQ *PANAMERA", "Restaurants", 100),
    ("SQ *ISSAQUAH RAMEN", "Restaurants", 100),
    ("IVAR'S", "Restaurants", 100),
    ("MENCHIE'S", "Restaurants", 100),
    ("GOPUFF", "Food Delivery", 100),
    # Groceries - additional patterns
    ("PCC - ", "Groceries", 100),
    ("RANCH 99", "Groceries", 100),
    ("99 RANCH", "Groceries", 100),
    # Clothing - additional
    ("REI.COM", "Clothing", 90),
    ("MOOSEJAW", "Clothing", 100),
    ("PATAGONIA", "Clothing", 100),
    ("EDDIE BAUER", "Clothing", 100),
    # Media - additional
    ("MEDIUM CORPORATION", "Media", 100),
    ("Washington P", "Media", 100),
    ("DISNEY PLUS", "Media", 100),
    ("DISNEY+", "Media", 100),
    ("KQED", "Media", 100),
    ("SAMHARRIS.ORG", "Media", 100),
    ("CAMPNAB", "Media", 100),
    ("RING MONTHLY", "Media", 100),
    # Software - additional
    ("GOOGLE *DOMAINS", "Software", 100),
    ("Google Domains", "Software", 100),
    ("ZOOM.US", "Software", 100),
    ("LEETCODE", "Software", 100),
    ("CLAUDE.AI", "Software", 100),
    ("ANTHROPIC", "Software", 100),
    ("NOTION", "Software", 100),
    ("DROPBOX", "Software", 100),
    # Kids Education - additional
    ("ISSAQUAH SCHOOL", "Kids Education", 100),
    ("DOCNETWORK", "Kids Education", 100),
    # Therapy - additional
    ("Yu Ding, PsyD", "Therapy", 100),
    ("YU DING PSYD", "Therapy", 100),
    # Home Services - additional
    ("SAMMAMISH PLATEAU WATE", "Home Services", 100),
    ("COIN-O-MATIC", "Home Services", 100),
    ("ARCADIA", "Home Services", 100),
    # Medical - additional
    ("SWEDISH MEDICAL", "Medical", 100),
    ("KAISER", "Medical", 100),
    ("LABCORP", "Medical", 100),
    # Pharmacy - additional
    ("EXPRESS SCRIPTS", "Pharmacy", 100),
    # Fitness - additional
    ("GARMIN", "Fitness", 100),
    # Insurance
    ("STATE FARM", "Insurance", 100),
    # Car Maintenance - additional
    ("ACURA OF BELLEVUE", "Car Maintenance", 100),
    ("JIFFY LUBE", "Car Maintenance", 100),
    # Travel - additional
    ("Chase Travel", "Travel", 90),
    ("COSTCO TRAVEL", "Travel", 90),
    ("RECREATION.GOV", "Travel", 100),
    ("OR STATE PARKS", "Travel", 100),
    ("WIFIONBOARD", "Flights", 100),
    # Parking/Tolls - additional
    ("GOODTOGO", "Parking", 100),
    ("PAYBYPHONE", "Parking", 100),
    # Shopping - additional
    ("MICHAELS STORES", "Online Shopping", 100),
    ("TARGET", "Online Shopping", 100),
    ("WALMART", "Online Shopping", 100),
    ("IKEA", "Home Improvement", 100),
    ("BED BATH", "Home Improvement", 100),
    # Massage
    ("GARAGE MASSAGE", "Massage", 100),
    # Food & Drink - meal kits/prep
    ("THISTLE.CO", "Food Delivery", 100),
    ("THISTLE ", "Food Delivery", 100),
    # Childcare - additional
    ("VICTORIA GARCIA", "Childcare", 100),
    # Uber One subscription
    ("UBER ONE", "Media", 100),
    # Costco online shopping (not groceries)
    ("WWW COSTCO COM", "Online Shopping", 100),
    ("COSTCO.COM", "Online Shopping", 100),
    # --- Round 3 uncategorized scan ---
    # Media
    ("WALL-ST-JOURNAL", "Media", 100),
    ("TESLA SUBSCRIPTION", "Software", 100),
    ("GOOGLE *Google Storage", "Software", 100),
    # Medical
    ("NEW VISION EYECARE", "Medical", 100),
    ("SEATTLE CHILDRENS", "Medical", 100),
    ("PROVIDENCE", "Medical", 100),
    ("APRIA", "Medical", 100),
    ("SUNBURST PSYCHOLOGY", "Therapy", 100),
    # Home Services
    ("PUGET SOUND ENERGY", "Home Services", 100),
    # Pet Care
    ("PETCO", "Pet Care", 100),
    # Restaurants - more
    ("TACO TIME", "Fast Food", 100),
    ("WILDFIN", "Restaurants", 100),
    ("SLEEPING GIANT", "Restaurants", 100),
    ("JUST POKE", "Restaurants", 100),
    ("LA PRIMA TAZZA", "Coffee", 100),
    ("WHEATFIELDS BAKERY", "Restaurants", 100),
    ("ISLAND COUNTRY MKTS", "Groceries", 100),
    # Shopping - more
    ("APPLE.COM/US", "Online Shopping", 100),
    ("Apple Online Store", "Online Shopping", 100),
    ("B&H PHOTO", "Online Shopping", 100),
    ("HANNA ANDERSSON", "Clothing", 100),
    ("Fjallraven", "Clothing", 100),
    ("STRIDERITE", "Clothing", 100),
    # Gas
    ("COSTCO GAS", "Gas", 100),
    # Kids
    ("REMLINGER FARM", "Kids Activities", 100),
    ("BRIGHT HORIZONS", "Childcare", 100),
    ("CHESS4LIFE", "Kids Activities", 100),
    ("EMERALD CITY GYMN", "Kids Activities", 100),
    ("MAEVE LI", "Kids Activities", 100),
    # Travel
    ("TRIP.COM", "Travel", 100),
    ("SUNCADIA", "Lodging", 100),
    ("SOL DUC", "Lodging", 100),
    # Legal
    ("Law Office", "Legal", 100),
    # Personal Care
    ("LARISSA SOFIA SALON", "Haircuts", 100),
    # Insurance
    ("ANNUAL MEMBERSHIP FEE", "Insurance", 100),
    # Parking
    ("2GC@WPZ", "Parking", 100),
]

TRANSFER_PATTERNS = [
    "AUTOMATIC PAYMENT",
    "PAYMENT THANK YOU",
    "Payment Thank You",
    "ACH Deposit",
    "ACH DEPOSIT",
    "INTEREST CHARGE",
    "BALANCE REFUND",
]


def get_db():
    """Open (or create) the database and return a connection."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def backup_db():
    """Create a .bak copy of the database and export rules before destructive operations."""
    if DB_PATH.exists():
        bak = DB_PATH.with_suffix(".db.bak")
        shutil.copy2(DB_PATH, bak)
        size_kb = bak.stat().st_size / 1024
        print(f"Backup: {bak.name} ({size_kb:.0f} KB)")
        # Auto-export categorization rules
        _export_rules(quiet=True)


def _export_rules(quiet=False):
    """Export categorization rules to JSON for disaster recovery.

    The JSON file syncs via Obsidian Sync, so rules survive even if the
    DB is deleted or corrupted. Use cmd_restore_rules() to reimport.
    """
    if not DB_PATH.exists():
        return
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT cr.pattern, cr.pattern_type, cr.priority, cr.source,
               c.name as category_name,
               pc.name as parent_category_name
        FROM categorization_rules cr
        JOIN categories c ON c.id = cr.category_id
        LEFT JOIN categories pc ON pc.id = c.parent_id
        ORDER BY cr.priority, cr.pattern
    """).fetchall()
    conn.close()

    rules = []
    for pattern, ptype, priority, source, cat, parent_cat in rows:
        rules.append({
            "pattern": pattern,
            "pattern_type": ptype,
            "priority": priority,
            "source": source,
            "category": cat,
            "parent_category": parent_cat,
        })

    with open(RULES_BACKUP_PATH, "w") as f:
        json.dump({"exported_at": __import__("datetime").datetime.now().isoformat(),
                    "count": len(rules), "rules": rules}, f, indent=2)

    if not quiet:
        print(f"Exported {len(rules)} rules to {RULES_BACKUP_PATH.name}")


def cmd_backup_rules():
    """Export categorization rules to JSON."""
    _export_rules(quiet=False)


def cmd_restore_rules():
    """Restore categorization rules from JSON backup.

    Rebuilds from scratch: init must have run first (categories must exist).
    Skips rules whose category doesn't exist in the DB.
    """
    if not RULES_BACKUP_PATH.exists():
        print(f"No backup found at {RULES_BACKUP_PATH}")
        sys.exit(1)

    with open(RULES_BACKUP_PATH) as f:
        data = json.load(f)

    rules = data.get("rules", [])
    print(f"Restoring from {RULES_BACKUP_PATH.name} ({data.get('count', '?')} rules, exported {data.get('exported_at', '?')})")

    conn = get_db()
    conn.executescript(SCHEMA)

    restored = 0
    skipped = 0
    for r in rules:
        cat_name = r["category"]
        parent_name = r.get("parent_category")

        # Find category id
        if parent_name:
            row = conn.execute(
                """SELECT c.id FROM categories c
                   JOIN categories pc ON pc.id = c.parent_id
                   WHERE c.name = ? AND pc.name = ?""",
                (cat_name, parent_name),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT id FROM categories WHERE name = ? AND parent_id IS NULL",
                (cat_name,),
            ).fetchone()

        if not row:
            skipped += 1
            continue

        cat_id = row[0]
        conn.execute(
            """INSERT OR REPLACE INTO categorization_rules
               (pattern, pattern_type, category_id, priority, source)
               VALUES (?, ?, ?, ?, ?)""",
            (r["pattern"], r.get("pattern_type", "keyword"),
             cat_id, r.get("priority", 100), r.get("source", "manual")),
        )
        restored += 1

    conn.commit()
    conn.close()
    print(json.dumps({
        "restored": restored,
        "skipped_missing_category": skipped,
        "total_in_backup": len(rules),
    }, indent=2))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init():
    """Create schema, seed accounts, categories, and rules."""
    backup_db()
    conn = get_db()
    conn.executescript(SCHEMA)

    # Add trip_id column to transactions if missing (migration)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(transactions)").fetchall()]
    if "trip_id" not in cols:
        conn.execute("ALTER TABLE transactions ADD COLUMN trip_id TEXT REFERENCES trips(id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_trip ON transactions(trip_id)")
        print("Added trip_id column to transactions.")
    else:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_txn_trip ON transactions(trip_id)")

    # Seed accounts
    for name, display in ACCOUNTS:
        conn.execute(
            "INSERT OR IGNORE INTO accounts(name, display_name) VALUES (?, ?)",
            (name, display),
        )

    # Seed categories — parents first, then children
    cat_ids = {}
    for cat_name, parent_name in CATEGORIES:
        parent_id = cat_ids.get(parent_name)
        conn.execute(
            "INSERT OR IGNORE INTO categories(name, parent_id) VALUES (?, ?)",
            (cat_name, parent_id),
        )
        row = conn.execute(
            "SELECT id FROM categories WHERE name=? AND parent_id IS ?",
            (cat_name, parent_id),
        ).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT id FROM categories WHERE name=? AND parent_id=?",
                (cat_name, parent_id),
            ).fetchone()
        cat_ids[cat_name] = row[0]

    # Seed rules
    for pattern, cat_name, priority in RULES:
        cat_id = cat_ids.get(cat_name)
        if cat_id is None:
            print(f"WARNING: category '{cat_name}' not found for rule '{pattern}'")
            continue
        conn.execute(
            "INSERT OR IGNORE INTO categorization_rules(pattern, category_id, priority) VALUES (?, ?, ?)",
            (pattern, cat_id, priority),
        )

    conn.commit()
    conn.close()
    print("Database initialized.")


def validate_balances(card_filter: str | None = None) -> list[dict]:
    """Validate DB transactions against PDF balance summaries.

    Reads balance_summary from processing_log.json, then for each statement:
      previous_balance + sum(all DB txns for that source_file) should = new_balance

    Also performs chain validation: each statement's previous_balance should equal
    the prior statement's new_balance.

    Returns list of error dicts. Empty list = all checks passed.
    """
    log_path = CSV_ROOT / "processing_log.json"
    if not log_path.exists():
        return []

    with open(log_path) as f:
        processing_log = json.load(f)

    conn = get_db()
    errors = []

    for card_name, card_data in sorted(processing_log.get("cards", {}).items()):
        if card_filter and card_name != card_filter:
            continue

        # Collect statements with balance data, sorted by date
        statements = []
        for filename, result in sorted(card_data.get("processed", {}).items()):
            balance = result.get("balance_summary")
            if not balance:
                continue
            source_file = f"{card_name}/{result['output_csv']}"
            stmt = {
                "source_file": source_file,
                "statement_date": result["statement_date"],
                "previous_balance": balance["previous_balance"],
                "new_balance": balance["new_balance"],
            }
            if "installments" in balance:
                stmt["installments"] = balance["installments"]
            statements.append(stmt)

        # Sort by statement date
        statements.sort(key=lambda s: s["statement_date"])

        # Check each statement: previous_balance + sum(txns) = new_balance
        for s in statements:
            row = conn.execute(
                "SELECT ROUND(SUM(amount), 2) FROM transactions WHERE source_file = ?",
                (s["source_file"],),
            ).fetchone()
            db_sum = row[0] if row[0] is not None else 0

            # Credit card: new_balance = previous_balance - sum(txns) + installments
            # Payments (positive) reduce balance, charges (negative) increase it
            # Apple Card installments are charged to balance but not in transactions
            installments = s.get("installments", 0)
            expected_new = round(s["previous_balance"] - db_sum + installments, 2)
            diff = abs(expected_new - s["new_balance"])
            if diff > 3.0:  # allow small PDF text extraction rounding
                errors.append({
                    "type": "balance_mismatch",
                    "source_file": s["source_file"],
                    "previous_balance": s["previous_balance"],
                    "db_txn_sum": db_sum,
                    "computed_new_balance": expected_new,
                    "pdf_new_balance": s["new_balance"],
                    "diff": round(diff, 2),
                })

        # Chain check: previous_balance[n] should = new_balance[n-1]
        for i in range(1, len(statements)):
            prev_new = statements[i - 1]["new_balance"]
            curr_prev = statements[i]["previous_balance"]
            diff = abs(prev_new - curr_prev)
            if diff > 0.01:
                errors.append({
                    "type": "chain_break",
                    "statement": statements[i]["source_file"],
                    "expected_previous": prev_new,
                    "actual_previous": curr_prev,
                    "diff": round(diff, 2),
                })

    conn.close()
    return errors


def log_issues(balance_errors=None, parse_errors=None, categorization=None):
    """Persist pipeline issues to Finance/pipeline-issues.md for later review."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    sections = []

    if balance_errors:
        lines = ["### Balance Validation"]
        for e in balance_errors:
            if e.get("type") == "balance_mismatch":
                lines.append(
                    f"- [ ] **{e['source_file']}**: computed {e['computed_new_balance']}"
                    f" vs PDF {e['pdf_new_balance']} (diff ${e['diff']:.2f})"
                )
            elif e.get("type") == "chain_break":
                lines.append(
                    f"- [ ] **{e['statement']}**: chain break — expected previous"
                    f" {e['expected_previous']}, actual {e['actual_previous']}"
                    f" (diff ${e['diff']:.2f})"
                )
            else:
                lines.append(f"- [ ] {json.dumps(e)}")
        sections.append("\n".join(lines))

    if parse_errors:
        lines = ["### Parse Errors"]
        for name, detail in parse_errors:
            lines.append(f"- [ ] **{name}**: {detail}")
        sections.append("\n".join(lines))

    if categorization:
        cc_uncat = categorization.get("cc_uncategorized", 0)
        amz_uncat = categorization.get("amazon_uncategorized", 0)
        if cc_uncat > 0 or amz_uncat > 0:
            lines = ["### Uncategorized"]
            if cc_uncat > 0:
                lines.append(f"- [ ] CC transactions: {cc_uncat} uncategorized")
            if amz_uncat > 0:
                lines.append(f"- [ ] Amazon orders: {amz_uncat} uncategorized")
            sections.append("\n".join(lines))

    if not sections:
        # No issues — write clean status
        content = (
            "# Finance Pipeline Issues\n\n"
            f"**Last updated:** {timestamp}\n\n"
            "No open issues.\n"
        )
    else:
        content = (
            "# Finance Pipeline Issues\n\n"
            f"**Last updated:** {timestamp}\n\n"
            + "\n\n".join(sections) + "\n"
        )

    ISSUES_PATH.write_text(content)


def cmd_validate():
    """Run balance validation and print results."""
    errors = validate_balances()
    if not errors:
        print(json.dumps({"status": "ok", "message": "All balance checks passed"}, indent=2))
    else:
        print(json.dumps({"status": "errors", "errors": errors}, indent=2))
    log_issues(balance_errors=errors if errors else None)


def cmd_import():
    """Import CSVs into the database (idempotent)."""
    backup_db()
    conn = get_db()

    # Build account name -> id lookup
    accounts = {
        row[0]: row[1]
        for row in conn.execute("SELECT name, id FROM accounts").fetchall()
    }

    # Get already-imported files
    imported = {
        row[0]
        for row in conn.execute("SELECT source_file FROM import_log").fetchall()
    }

    total_new = 0
    files_imported = 0

    for card_dir in sorted(CSV_ROOT.iterdir()):
        if not card_dir.is_dir():
            continue
        account_name = card_dir.name
        account_id = accounts.get(account_name)
        if account_id is None:
            continue

        for csv_file in sorted(card_dir.glob("*.csv")):
            source_file = f"{account_name}/{csv_file.name}"
            if source_file in imported:
                continue

            count = 0
            with open(csv_file, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header is None:
                    continue

                for row_num, row in enumerate(reader, start=1):
                    if len(row) < 3:
                        continue
                    date_val, desc, amount_str = row[0], row[1], row[2]
                    if not date_val or not desc:
                        continue
                    try:
                        amount = float(amount_str)
                    except (ValueError, IndexError):
                        continue

                    # Detect transfers
                    is_transfer = 0
                    desc_upper = desc.upper()
                    for pat in TRANSFER_PATTERNS:
                        if pat.upper() in desc_upper:
                            is_transfer = 1
                            break

                    try:
                        conn.execute(
                            """INSERT OR IGNORE INTO transactions
                               (account_id, date, description, amount, source_file, source_row, is_transfer)
                               VALUES (?, ?, ?, ?, ?, ?, ?)""",
                            (account_id, date_val, desc, amount, source_file, row_num, is_transfer),
                        )
                        if conn.execute("SELECT changes()").fetchone()[0] > 0:
                            count += 1
                    except sqlite3.IntegrityError:
                        pass

            conn.execute(
                "INSERT OR IGNORE INTO import_log(source_file, transaction_count) VALUES (?, ?)",
                (source_file, count),
            )
            total_new += count
            files_imported += 1

    conn.commit()
    conn.close()

    # Run balance validation after import
    balance_errors = validate_balances()

    total_txn = _count_transactions()
    result = {
        "files_imported": files_imported,
        "new_transactions": total_new,
        "total_transactions": total_txn,
    }
    if balance_errors:
        result["balance_validation_errors"] = balance_errors
    print(json.dumps(result, indent=2))


def _parse_money(val):
    """Parse a monetary string, returning None for 'Not Available' or empty."""
    if not val or val == "Not Available":
        return None
    try:
        return float(val.strip("'\""))
    except ValueError:
        return None


def _parse_payment_method(raw):
    """Extract (card_type, card_last4) from payment method string.

    Examples:
        'Visa - 1158'           -> ('Visa', '1158')
        'MasterCard - 7030'     -> ('MasterCard', '7030')
        'Gift Certificate/Card' -> ('Gift Certificate/Card', None)
        'Gift Certificate/Card and Visa - 1158' -> ('Visa', '1158')
        'Bank Account - 437'    -> ('Bank Account', '437')
        'Not Available'         -> (None, None)
    """
    if not raw or raw == "Not Available":
        return None, None
    # Handle mixed payment: "Gift Certificate/Card and Visa - 1158"
    if " and " in raw:
        raw = raw.split(" and ", 1)[1]
    match = re.match(r"^(.+?)\s*-\s*(\d+)$", raw)
    if match:
        return match.group(1).strip(), match.group(2)
    return raw.strip(), None


def cmd_import_amazon():
    """Import Amazon order history CSVs into the database (idempotent)."""
    backup_db()
    conn = get_db()
    # Ensure amazon_orders table exists
    conn.executescript(SCHEMA)

    # Watermark: skip rows at or before the latest order date already imported
    watermark_row = conn.execute(
        "SELECT MAX(order_date) FROM amazon_orders"
    ).fetchone()
    watermark = watermark_row[0] if watermark_row and watermark_row[0] else None

    csv_files = sorted(AMAZON_CSV_ROOT.glob("*.csv"))
    if not csv_files:
        print(json.dumps({"error": f"No CSV files found in {AMAZON_CSV_ROOT}"}))
        return

    total_new = 0
    total_skipped = 0

    for csv_file in csv_files:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse order date
                order_timestamp = row.get("Order Date", "")
                if not order_timestamp:
                    continue
                order_date = order_timestamp[:10]  # YYYY-MM-DD from ISO 8601

                # Fast path: skip if before watermark
                if watermark and order_date <= watermark:
                    total_skipped += 1
                    continue

                order_id = row.get("Order ID", "")
                asin = row.get("ASIN", "")
                if not order_id or not asin:
                    continue

                card_type, card_last4 = _parse_payment_method(
                    row.get("Payment Method Type", "")
                )

                ship_date_raw = row.get("Ship Date", "")
                ship_date = ship_date_raw[:10] if ship_date_raw and ship_date_raw != "Not Available" else None

                quantity_raw = row.get("Original Quantity", "")
                try:
                    quantity = int(quantity_raw) if quantity_raw else None
                except ValueError:
                    quantity = None

                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO amazon_orders
                           (order_id, order_date, order_timestamp, asin,
                            product_name, product_condition, quantity,
                            unit_price, unit_price_tax, subtotal, subtotal_tax,
                            shipping_charge, total_discount, total_amount,
                            currency, payment_method, card_type, card_last4,
                            order_status, ship_date, shipping_address,
                            shipping_option, website)
                           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            order_id,
                            order_date,
                            order_timestamp,
                            asin,
                            row.get("Product Name", ""),
                            row.get("Product Condition", ""),
                            quantity,
                            _parse_money(row.get("Unit Price", "")),
                            _parse_money(row.get("Unit Price Tax", "")),
                            _parse_money(row.get("Shipment Item Subtotal", "")),
                            _parse_money(row.get("Shipment Item Subtotal Tax", "")),
                            _parse_money(row.get("Shipping Charge", "")),
                            _parse_money(row.get("Total Discounts", "")),
                            _parse_money(row.get("Total Amount", "")),
                            row.get("Currency", "USD"),
                            row.get("Payment Method Type", ""),
                            card_type,
                            card_last4,
                            row.get("Order Status", ""),
                            ship_date,
                            row.get("Shipping Address", ""),
                            row.get("Shipping Option", ""),
                            row.get("Website", ""),
                        ),
                    )
                    if conn.execute("SELECT changes()").fetchone()[0] > 0:
                        total_new += 1
                    else:
                        total_skipped += 1
                except sqlite3.IntegrityError:
                    total_skipped += 1

    conn.commit()

    total = conn.execute("SELECT COUNT(*) FROM amazon_orders").fetchone()[0]
    new_watermark = conn.execute(
        "SELECT MAX(order_date) FROM amazon_orders"
    ).fetchone()[0]
    conn.close()

    print(json.dumps({
        "csv_files": len(csv_files),
        "new_orders": total_new,
        "skipped": total_skipped,
        "total_orders": total,
        "watermark": new_watermark,
    }, indent=2))


def cmd_import_payslips():
    """Import payslip YAML files into the database (idempotent)."""
    backup_db()
    conn = get_db()
    conn.executescript(SCHEMA)

    files_scanned = 0
    new_payslips = 0
    skipped = 0
    line_items_inserted = 0

    LINE_ITEM_SECTIONS = [
        "earnings",
        "employee_taxes",
        "pre_tax_deductions",
        "post_tax_deductions",
        "employer_paid_benefits",
    ]

    for employer_dir in sorted(PAYSLIP_ROOT.iterdir()):
        if not employer_dir.is_dir():
            continue
        for yaml_file in sorted(employer_dir.glob("*.yaml")):
            files_scanned += 1
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                continue

            summary = data.get("summary", {}).get("current", {})
            source = data.get("source", {})
            deposit = data.get("deposit", {})
            source_pages = json.dumps(source.get("pages")) if source.get("pages") else None
            source_file = f"{employer_dir.name}/{yaml_file.name}"

            try:
                conn.execute(
                    """INSERT OR IGNORE INTO payslips
                       (employer, employee_id, pay_period_start, pay_period_end,
                        pay_date, pay_type, hours_worked, gross_pay,
                        pre_tax_deductions, employee_taxes, post_tax_deductions,
                        net_pay, total_earnings, total_employer_benefits,
                        deposit_amount, source_file, source_pages, processed_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        data.get("employer"),
                        data.get("employee_id"),
                        data.get("pay_period_start"),
                        data.get("pay_period_end"),
                        data.get("pay_date"),
                        data.get("pay_type"),
                        summary.get("hours_worked"),
                        summary.get("gross_pay", 0),
                        summary.get("pre_tax_deductions"),
                        summary.get("employee_taxes"),
                        summary.get("post_tax_deductions"),
                        summary.get("net_pay", 0),
                        data.get("total_earnings"),
                        data.get("total_employer_paid_benefits"),
                        deposit.get("amount"),
                        source_file,
                        source_pages,
                        source.get("processed_at"),
                    ),
                )
                if conn.execute("SELECT changes()").fetchone()[0] > 0:
                    new_payslips += 1
                    # Get the inserted payslip id
                    payslip_id = conn.execute(
                        "SELECT id FROM payslips WHERE source_file=?",
                        (source_file,),
                    ).fetchone()[0]

                    # Insert line items for each section
                    for section in LINE_ITEM_SECTIONS:
                        items = data.get(section, [])
                        if not items:
                            continue
                        for item in items:
                            conn.execute(
                                """INSERT INTO payslip_line_items
                                   (payslip_id, section, description, amount, ytd, dates, hours, rate)
                                   VALUES (?,?,?,?,?,?,?,?)""",
                                (
                                    payslip_id,
                                    section,
                                    item.get("description", ""),
                                    item.get("amount", 0),
                                    item.get("ytd"),
                                    item.get("dates"),
                                    item.get("hours"),
                                    item.get("rate"),
                                ),
                            )
                            line_items_inserted += 1
                else:
                    skipped += 1
            except sqlite3.IntegrityError:
                skipped += 1

    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM payslips").fetchone()[0]
    conn.close()

    print(json.dumps({
        "files_scanned": files_scanned,
        "new_payslips": new_payslips,
        "skipped_duplicates": skipped,
        "total_payslips": total,
        "line_items_inserted": line_items_inserted,
    }, indent=2))


def cmd_categorize_amazon():
    """Apply keyword rules to uncategorized Amazon orders."""
    conn = get_db()

    # Load rules sorted by priority
    rules = conn.execute("""
        SELECT r.pattern, r.category_id, r.priority
        FROM categorization_rules r
        ORDER BY r.priority, r.id
    """).fetchall()

    # Get uncategorized Amazon orders
    uncategorized = conn.execute(
        "SELECT id, product_name FROM amazon_orders WHERE category_id IS NULL"
    ).fetchall()

    categorized_count = 0
    for order_id, product_name in uncategorized:
        if not product_name:
            continue
        name_upper = product_name.upper()
        for pattern, cat_id, _priority in rules:
            if pattern.upper() in name_upper:
                conn.execute(
                    "UPDATE amazon_orders SET category_id=? WHERE id=?",
                    (cat_id, order_id),
                )
                categorized_count += 1
                break

    conn.commit()

    remaining = conn.execute(
        "SELECT COUNT(*) FROM amazon_orders WHERE category_id IS NULL"
    ).fetchone()[0]

    conn.close()
    print(json.dumps({
        "newly_categorized": categorized_count,
        "remaining_uncategorized": remaining,
    }, indent=2))


def cmd_import_tax():
    """Import tax YAML files into the database (idempotent)."""
    backup_db()
    conn = get_db()
    conn.executescript(SCHEMA)

    new_docs = 0
    skipped = 0
    items_inserted = 0

    # Scan both prepare and archive folders
    for folder_type in ["prepare", "archive"]:
        folder_root = TAX_ROOT / folder_type
        if not folder_root.exists():
            continue
        for year_dir in sorted(folder_root.iterdir()):
            if not year_dir.is_dir() or not year_dir.name.isdigit():
                continue
            for yaml_file in sorted(year_dir.glob("*.yaml")):
                yaml_rel = str(yaml_file.relative_to(VAULT_ROOT))

                # Skip if already imported
                existing = conn.execute(
                    "SELECT id FROM tax_documents WHERE yaml_file=?", (yaml_rel,)
                ).fetchone()
                if existing:
                    skipped += 1
                    continue

                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data:
                    continue

                form_type = data.get("form_type", "")
                tax_year = data.get("tax_year", 0)
                source = data.get("source", {})

                # Extract payer/entity name based on form type
                payer_name = ""
                payer_tin = ""
                if form_type == "W-2":
                    payer_name = data.get("employer", {}).get("name", "")
                    payer_tin = data.get("employer", {}).get("ein", "")
                elif form_type in ("1099-R", "1099-INT", "1099-SA"):
                    payer_name = data.get("payer", {}).get("name", "")
                    payer_tin = data.get("payer", {}).get("tin", "")
                elif form_type == "1098":
                    payer_name = data.get("lender", {}).get("name", "")
                    payer_tin = data.get("lender", {}).get("tin", "")
                elif form_type in ("5498-SA", "5498"):
                    payer_name = data.get("trustee", {}).get("name", "")
                    payer_tin = data.get("trustee", {}).get("tin", "")
                elif form_type == "Schedule-H":
                    payer_name = data.get("employer", {}).get("name", "")
                    payer_tin = data.get("employer", {}).get("ein", "")
                elif form_type == "1040":
                    payer_name = data.get("taxpayer", {}).get("name", "")
                    payer_tin = ""
                elif form_type == "1099-CONSOLIDATED":
                    payer_name = data.get("institution", "")
                    payer_tin = ""

                recipient_ssn = ""
                for key in ["employee", "recipient", "borrower", "taxpayer"]:
                    ssn = data.get(key, {}).get("ssn_last4", "")
                    if ssn:
                        recipient_ssn = ssn
                        break

                filing_status = data.get("filing_status", "")
                validation = data.get("validation", {})
                mismatches = validation.get("mismatches", [])
                validation_ok = 1 if not mismatches else 0

                conn.execute(
                    """INSERT INTO tax_documents
                       (form_type, tax_year, source_folder, payer_name, payer_tin,
                        recipient_ssn_last4, filing_status, source_file, yaml_file,
                        processed_at, validation_ok)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        str(form_type),
                        tax_year,
                        folder_type,
                        payer_name,
                        payer_tin,
                        recipient_ssn,
                        filing_status,
                        source.get("file", ""),
                        yaml_rel,
                        source.get("processed_at", ""),
                        validation_ok,
                    ),
                )

                doc_id = conn.execute(
                    "SELECT id FROM tax_documents WHERE yaml_file=?", (yaml_rel,)
                ).fetchone()[0]
                new_docs += 1

                # Insert line items from boxes/summary/income sections
                items = _extract_tax_line_items(data, form_type)
                for box_name, box_value, box_text, box_bool in items:
                    conn.execute(
                        """INSERT INTO tax_line_items
                           (doc_id, box_name, box_value, box_text, box_bool)
                           VALUES (?,?,?,?,?)""",
                        (doc_id, box_name, box_value, box_text, box_bool),
                    )
                    items_inserted += 1

    conn.commit()
    print(json.dumps({
        "new_documents": new_docs,
        "skipped_existing": skipped,
        "line_items_inserted": items_inserted,
    }, indent=2))


def _extract_tax_line_items(data: dict, form_type: str) -> list:
    """Extract box-level line items from a tax YAML data dict.

    Returns list of (box_name, box_value, box_text, box_bool) tuples.
    """
    items = []

    # Extract from 'boxes' dict (W-2, 1099-R, 1098, 1099-INT, 5498, etc.)
    boxes = data.get("boxes", {})
    for key, val in boxes.items():
        key_str = str(key)
        if isinstance(val, (int, float)):
            items.append((key_str, float(val), None, None))
        elif isinstance(val, bool):
            items.append((key_str, None, None, 1 if val else 0))
        elif isinstance(val, str):
            items.append((key_str, None, val, None))
        elif isinstance(val, dict):
            # Nested dict like box 13 checkboxes
            for subkey, subval in val.items():
                full_key = f"{key_str}.{subkey}"
                if isinstance(subval, bool):
                    items.append((full_key, None, None, 1 if subval else 0))
                elif isinstance(subval, (int, float)):
                    items.append((full_key, float(subval), None, None))
                elif isinstance(subval, str):
                    items.append((full_key, None, subval, None))
        elif isinstance(val, list):
            # List of dicts like box 12 codes
            for i, entry in enumerate(val):
                if isinstance(entry, dict):
                    code = entry.get("code", "")
                    amount = entry.get("amount")
                    desc = entry.get("description", "")
                    box_key = f"{key_str}_{code}" if code else f"{key_str}_{i}"
                    items.append((box_key, float(amount) if amount else None, desc, None))

    # Extract from 'summary' dict (1040)
    summary = data.get("summary", {})
    if isinstance(summary, dict) and form_type == "1040":
        for key, val in summary.items():
            if isinstance(val, (int, float)):
                items.append((f"summary.{key}", float(val), None, None))

    # Extract from 'income' dict (1040)
    income = data.get("income", {})
    if isinstance(income, dict) and form_type == "1040":
        for key, val in income.items():
            if isinstance(val, (int, float)):
                items.append((f"income.{key}", float(val), None, None))

    # Extract from 'forms' dict (1099-CONSOLIDATED)
    forms = data.get("forms", {})
    if isinstance(forms, dict) and form_type == "1099-CONSOLIDATED":
        for sub_form, sub_data in forms.items():
            if isinstance(sub_data, dict):
                for key, val in sub_data.items():
                    box_key = f"{sub_form}.{key}"
                    if isinstance(val, (int, float)):
                        items.append((box_key, float(val), None, None))
                    elif isinstance(val, str):
                        items.append((box_key, None, val, None))
                    elif isinstance(val, dict):
                        # Nested dict like 1099-B short_term/long_term/total
                        for subkey, subval in val.items():
                            deep_key = f"{box_key}.{subkey}"
                            if isinstance(subval, (int, float)):
                                items.append((deep_key, float(subval), None, None))

    # Extract plan_type, account_number as text items
    for text_field in ["plan_type", "account_number", "loan_number", "property_address",
                       "institution", "format"]:
        val = data.get(text_field)
        if val:
            items.append((text_field, None, str(val), None))

    return items


def cmd_import_fidelity():
    """Import Fidelity account YAML files into the database (idempotent)."""
    backup_db()
    conn = get_db()
    conn.executescript(SCHEMA)

    new_snapshots = 0
    new_holdings = 0
    skipped = 0

    yaml_files = sorted(FIDELITY_ROOT.glob("*.yaml"))
    if not yaml_files:
        print("No Fidelity YAML files found.")
        return

    for yaml_file in yaml_files:
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        stmt_date = data.get("statement_date", "")
        source_file = data.get("source", {}).get("file", yaml_file.name)

        # Upsert portfolio snapshot
        existing = conn.execute(
            "SELECT id FROM fidelity_portfolio_snapshots WHERE statement_date=?",
            (stmt_date,)
        ).fetchone()
        if existing:
            skipped += 1
            continue

        portfolio = data.get("portfolio", {})
        income = data.get("income_summary", {})
        conn.execute(
            """INSERT INTO fidelity_portfolio_snapshots
               (statement_date, beginning_value, ending_value, additions,
                subtractions, change_in_investment_value,
                income_taxable, income_tax_deferred, income_tax_free,
                income_total, source_file)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                stmt_date,
                portfolio.get("beginning_value"),
                portfolio.get("ending_value"),
                portfolio.get("additions"),
                portfolio.get("subtractions"),
                portfolio.get("change_in_investment_value"),
                income.get("taxable", {}).get("total"),
                income.get("tax_deferred", {}).get("total"),
                income.get("tax_free", {}).get("total"),
                income.get("grand_total"),
                source_file,
            ),
        )

        # Process each account
        for acct in data.get("accounts", []):
            acct_num = acct.get("account_number", "")
            if not acct_num:
                continue

            # Upsert account record
            existing_acct = conn.execute(
                "SELECT id FROM fidelity_accounts WHERE account_number=?",
                (acct_num,)
            ).fetchone()

            if existing_acct:
                acct_id = existing_acct[0]
                conn.execute(
                    "UPDATE fidelity_accounts SET last_seen=? WHERE id=?",
                    (stmt_date, acct_id),
                )
            else:
                conn.execute(
                    """INSERT INTO fidelity_accounts
                       (account_number, account_name, account_type,
                        tax_status, beneficiary, first_seen, last_seen)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        acct_num,
                        acct.get("account_name", ""),
                        acct.get("account_type", "unknown"),
                        acct.get("tax_status", "taxable"),
                        acct.get("beneficiary", "Yi"),
                        stmt_date,
                        stmt_date,
                    ),
                )
                acct_id = conn.execute(
                    "SELECT id FROM fidelity_accounts WHERE account_number=?",
                    (acct_num,)
                ).fetchone()[0]

            # Insert monthly snapshot
            summary = acct.get("summary", {})
            acct_income = acct.get("income", {})
            conn.execute(
                """INSERT OR IGNORE INTO fidelity_monthly_snapshots
                   (account_id, statement_date, beginning_value, ending_value,
                    additions, subtractions, change_in_investment_value,
                    deposits, withdrawals, exchanges_in, exchanges_out,
                    transfers_between_fidelity,
                    income_dividends, income_interest, income_total,
                    source_file)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    acct_id, stmt_date,
                    summary.get("beginning_value"),
                    summary.get("ending_value"),
                    summary.get("additions"),
                    summary.get("subtractions"),
                    summary.get("change_in_investment_value"),
                    summary.get("deposits"),
                    summary.get("withdrawals"),
                    summary.get("exchanges_in"),
                    summary.get("exchanges_out"),
                    summary.get("transfers_between_fidelity"),
                    acct_income.get("dividends"),
                    acct_income.get("interest"),
                    acct_income.get("total"),
                    source_file,
                ),
            )

            snap_id = conn.execute(
                """SELECT id FROM fidelity_monthly_snapshots
                   WHERE account_id=? AND statement_date=?""",
                (acct_id, stmt_date),
            ).fetchone()[0]
            new_snapshots += 1

            # Insert holdings
            for h in acct.get("holdings", []):
                conn.execute(
                    """INSERT INTO fidelity_holdings
                       (snapshot_id, symbol, description, asset_class,
                        quantity, price, market_value,
                        cost_basis, unrealized_gain_loss)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        snap_id,
                        h.get("symbol"),
                        h.get("description"),
                        h.get("asset_class"),
                        h.get("quantity"),
                        h.get("price"),
                        h.get("market_value"),
                        h.get("cost_basis"),
                        h.get("unrealized_gain_loss"),
                    ),
                )
                new_holdings += 1

    # Second pass: import CMA activity transactions (independent of snapshot skip)
    new_cma_txns = 0
    for yaml_file in yaml_files:
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue
        source_file = data.get("source", {}).get("file", yaml_file.name)
        for acct in data.get("accounts", []):
            activity = acct.get("activity")
            if not activity:
                continue
            for i, txn in enumerate(activity):
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO fidelity_cma_transactions
                           (date, type, description, amount, payee, category,
                            is_transfer, source_file, source_row)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (
                            txn.get("date"),
                            txn.get("type"),
                            txn.get("description"),
                            txn.get("amount"),
                            txn.get("payee"),
                            txn.get("category"),
                            1 if txn.get("is_transfer") else 0,
                            source_file,
                            i,
                        ),
                    )
                    if conn.execute("SELECT changes()").fetchone()[0] > 0:
                        new_cma_txns += 1
                except Exception:
                    pass

    conn.commit()
    print(json.dumps({
        "new_snapshots": new_snapshots,
        "new_holdings": new_holdings,
        "new_cma_transactions": new_cma_txns,
        "skipped_existing": skipped,
    }, indent=2))


def cmd_import_sofi():
    """Import SoFi loan YAML files into the database (idempotent)."""
    backup_db()
    conn = get_db()
    conn.executescript(SCHEMA)

    new_stmts = 0
    skipped = 0

    yaml_files = sorted(SOFI_ROOT.glob("*.yaml"))
    if not yaml_files:
        print("No SoFi loan YAML files found.")
        return

    for yaml_file in yaml_files:
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        stmt_month = data.get("statement_month", "")
        source_file = data.get("source", {}).get("file", yaml_file.name)
        breakdown = data.get("breakdown", {})
        last_txn = data.get("last_transaction") or {}

        try:
            conn.execute(
                """INSERT OR IGNORE INTO sofi_loan_statements
                   (statement_month, current_balance, credit_limit, payment_due,
                    principal, interest, fees, ytd_interest_paid,
                    last_txn_date, last_txn_total, source_file, processed_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    stmt_month,
                    data.get("current_balance"),
                    data.get("credit_limit"),
                    data.get("payment_due"),
                    breakdown.get("principal"),
                    breakdown.get("interest"),
                    breakdown.get("fees", 0),
                    data.get("ytd_interest_paid"),
                    last_txn.get("date"),
                    last_txn.get("total"),
                    source_file,
                    data.get("source", {}).get("processed_at"),
                ),
            )
            if conn.execute("SELECT changes()").fetchone()[0] > 0:
                new_stmts += 1
            else:
                skipped += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    print(json.dumps({
        "new_statements": new_stmts,
        "skipped_existing": skipped,
    }, indent=2))


def cmd_import_becu():
    """Import BECU checking + HELOC YAML files into the database (idempotent)."""
    backup_db()
    conn = get_db()
    conn.executescript(SCHEMA)

    new_check = new_heloc = new_txns = skipped = 0

    yaml_files = sorted(BECU_ROOT.glob("*.yaml"))
    if not yaml_files:
        print("No BECU YAML files found.")
        return

    for yaml_file in yaml_files:
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        stmt_month = data.get("statement_month", "")
        source_file = data.get("source", {}).get("file", yaml_file.name)
        processed_at = data.get("source", {}).get("processed_at")
        checking = data.get("checking", {})
        heloc = data.get("heloc")

        # --- Checking statement ---
        txns = checking.get("transactions", [])
        dep_count = sum(1 for t in txns if t.get("type") == "deposit")
        wdl_count = sum(1 for t in txns if t.get("type") == "withdrawal")

        try:
            conn.execute(
                """INSERT OR IGNORE INTO becu_checking_statements
                   (statement_month, period_start, period_end,
                    beginning_balance, withdrawals_fees, deposits,
                    dividends_interest, ending_balance, apy,
                    avg_daily_balance, ytd_dividends,
                    num_deposits, num_withdrawals,
                    source_file, processed_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    stmt_month,
                    data.get("period_start"),
                    data.get("period_end"),
                    checking.get("beginning_balance"),
                    checking.get("withdrawals_fees"),
                    checking.get("deposits"),
                    checking.get("dividends_interest"),
                    checking.get("ending_balance"),
                    checking.get("apy"),
                    checking.get("average_daily_balance"),
                    checking.get("ytd_dividends"),
                    dep_count,
                    wdl_count,
                    source_file,
                    processed_at,
                ),
            )
            if conn.execute("SELECT changes()").fetchone()[0] > 0:
                stmt_id = conn.execute(
                    "SELECT id FROM becu_checking_statements WHERE statement_month=?",
                    (stmt_month,),
                ).fetchone()[0]
                # Insert transactions
                for txn in txns:
                    conn.execute(
                        """INSERT INTO becu_checking_transactions
                           (statement_id, date, amount, description, type)
                           VALUES (?,?,?,?,?)""",
                        (stmt_id, txn["date"], txn["amount"],
                         txn["description"], txn["type"]),
                    )
                    new_txns += 1
                new_check += 1
            else:
                skipped += 1
        except sqlite3.IntegrityError:
            skipped += 1

        # --- HELOC statement ---
        if heloc:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO becu_heloc_statements
                       (statement_month, period_start, period_end,
                        previous_balance, payments, other_credits,
                        advances, fees_charged, interest_charged,
                        new_balance, credit_limit, available_credit,
                        apr, ytd_interest, ytd_fees,
                        minimum_payment, payment_date,
                        total_interest_this_period,
                        source_file, processed_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        stmt_month,
                        data.get("period_start"),
                        data.get("period_end"),
                        heloc.get("previous_balance"),
                        heloc.get("payments"),
                        heloc.get("other_credits"),
                        heloc.get("advances"),
                        heloc.get("fees_charged"),
                        heloc.get("interest_charged"),
                        heloc.get("new_balance"),
                        heloc.get("credit_limit"),
                        heloc.get("available_credit"),
                        heloc.get("apr"),
                        heloc.get("ytd_interest"),
                        heloc.get("ytd_fees"),
                        heloc.get("minimum_payment"),
                        heloc.get("payment_date"),
                        heloc.get("total_interest_this_period"),
                        source_file,
                        processed_at,
                    ),
                )
                if conn.execute("SELECT changes()").fetchone()[0] > 0:
                    new_heloc += 1
            except sqlite3.IntegrityError:
                pass

    conn.commit()
    print(json.dumps({
        "new_checking_statements": new_check,
        "new_heloc_statements": new_heloc,
        "new_checking_transactions": new_txns,
        "skipped_existing": skipped,
    }, indent=2))


def cmd_import_wellsfargo_car():
    """Import Wells Fargo car loan YAML files into the database (idempotent)."""
    backup_db()
    conn = get_db()
    conn.executescript(SCHEMA)

    new_stmts = 0
    skipped = 0

    yaml_files = sorted(WF_CAR_ROOT.glob("*.yaml"))
    if not yaml_files:
        print("No Wells Fargo car loan YAML files found.")
        return

    for yaml_file in yaml_files:
        with open(yaml_file, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            continue

        stmt_month = data.get("statement_month", "")
        agg = data.get("aggregates", {})
        ytd_info = data.get("ytd_interest") or {}

        try:
            conn.execute(
                """INSERT OR IGNORE INTO wellsfargo_car_statements
                   (statement_month, statement_date, account_number, vehicle,
                    interest_rate, monthly_payment, maturity_date, daily_interest,
                    payoff_amount, payoff_date, payment_due_date, total_amount_due,
                    principal_paid, interest_paid, extra_principal, total_paid,
                    ytd_interest_paid, yaml_file)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    stmt_month,
                    data.get("statement_date"),
                    data.get("account_number"),
                    data.get("vehicle"),
                    data.get("interest_rate"),
                    data.get("monthly_payment"),
                    data.get("maturity_date"),
                    data.get("daily_interest"),
                    data.get("payoff_amount"),
                    data.get("payoff_date"),
                    data.get("payment_due_date"),
                    data.get("total_amount_due"),
                    agg.get("principal_paid"),
                    agg.get("interest_paid"),
                    agg.get("extra_principal"),
                    agg.get("total_paid"),
                    ytd_info.get("amount"),
                    f"Finance/wellsfargo-car-loan/{yaml_file.name}",
                ),
            )
            if conn.execute("SELECT changes()").fetchone()[0] > 0:
                new_stmts += 1
            else:
                skipped += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()
    print(json.dumps({
        "new_statements": new_stmts,
        "skipped_existing": skipped,
    }, indent=2))


def cmd_status():
    """Print database statistics."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    spending = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE is_transfer=0"
    ).fetchone()[0]
    transfers = total - spending
    categorized = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE category_id IS NOT NULL AND is_transfer=0"
    ).fetchone()[0]
    uncategorized = spending - categorized

    date_range = conn.execute(
        "SELECT MIN(date), MAX(date) FROM transactions"
    ).fetchone()

    rule_count = conn.execute("SELECT COUNT(*) FROM categorization_rules").fetchone()[0]
    file_count = conn.execute("SELECT COUNT(*) FROM import_log").fetchone()[0]

    pct = (categorized / spending * 100) if spending > 0 else 0

    # Per-account breakdown
    acct_stats = conn.execute("""
        SELECT a.display_name, COUNT(t.id),
               SUM(CASE WHEN t.is_transfer=0 THEN 1 ELSE 0 END),
               MIN(t.date), MAX(t.date)
        FROM transactions t
        JOIN accounts a ON a.id = t.account_id
        GROUP BY a.id ORDER BY a.display_name
    """).fetchall()

    # Amazon orders stats
    amazon_total = 0
    amazon_categorized = 0
    amazon_date_range = None
    try:
        amazon_total = conn.execute("SELECT COUNT(*) FROM amazon_orders").fetchone()[0]
        amazon_categorized = conn.execute(
            "SELECT COUNT(*) FROM amazon_orders WHERE category_id IS NOT NULL"
        ).fetchone()[0]
        amazon_dr = conn.execute(
            "SELECT MIN(order_date), MAX(order_date) FROM amazon_orders"
        ).fetchone()
        if amazon_dr and amazon_dr[0]:
            amazon_date_range = {"from": amazon_dr[0], "to": amazon_dr[1]}
    except sqlite3.OperationalError:
        pass  # Table doesn't exist yet

    amazon_pct = (amazon_categorized / amazon_total * 100) if amazon_total > 0 else 0

    result = {
        "total_transactions": total,
        "spending_transactions": spending,
        "transfers": transfers,
        "categorized": categorized,
        "uncategorized": uncategorized,
        "categorization_pct": round(pct, 1),
        "date_range": {"from": date_range[0], "to": date_range[1]} if date_range[0] else None,
        "csv_files_imported": file_count,
        "categorization_rules": rule_count,
        "accounts": [
            {
                "name": row[0],
                "total": row[1],
                "spending": row[2],
                "from": row[3],
                "to": row[4],
            }
            for row in acct_stats
        ],
        "amazon_orders": {
            "total": amazon_total,
            "categorized": amazon_categorized,
            "uncategorized": amazon_total - amazon_categorized,
            "categorization_pct": round(amazon_pct, 1),
            "date_range": amazon_date_range,
        },
    }

    # Tax documents stats
    try:
        tax_total = conn.execute("SELECT COUNT(*) FROM tax_documents").fetchone()[0]
        if tax_total > 0:
            tax_items = conn.execute("SELECT COUNT(*) FROM tax_line_items").fetchone()[0]
            tax_by_type = conn.execute("""
                SELECT form_type, COUNT(*) FROM tax_documents
                GROUP BY form_type ORDER BY form_type
            """).fetchall()
            tax_by_year = conn.execute("""
                SELECT tax_year, COUNT(*) FROM tax_documents
                GROUP BY tax_year ORDER BY tax_year
            """).fetchall()
            result["tax_documents"] = {
                "total": tax_total,
                "line_items": tax_items,
                "by_form_type": {row[0]: row[1] for row in tax_by_type},
                "by_year": {row[0]: row[1] for row in tax_by_year},
            }
    except sqlite3.OperationalError:
        pass  # Table doesn't exist yet

    conn.close()
    print(json.dumps(result, indent=2))


def cmd_categorize():
    """Apply keyword rules to uncategorized transactions."""
    conn = get_db()

    # Load rules sorted by priority
    rules = conn.execute("""
        SELECT r.pattern, r.category_id, r.priority
        FROM categorization_rules r
        ORDER BY r.priority, r.id
    """).fetchall()

    # Also auto-categorize transfers
    transfer_cat_ids = {}
    for row in conn.execute("""
        SELECT c.id, c.name FROM categories c
        JOIN categories p ON c.parent_id = p.id
        WHERE p.name = 'Transfers'
    """).fetchall():
        transfer_cat_ids[row[1]] = row[0]

    # Get uncategorized transactions
    uncategorized = conn.execute(
        "SELECT id, description, is_transfer FROM transactions WHERE category_id IS NULL"
    ).fetchall()

    categorized_count = 0
    for txn_id, desc, is_transfer in uncategorized:
        desc_upper = desc.upper()
        matched = False

        for pattern, cat_id, _priority in rules:
            if pattern.upper() in desc_upper:
                conn.execute(
                    "UPDATE transactions SET category_id=? WHERE id=?",
                    (cat_id, txn_id),
                )
                categorized_count += 1
                matched = True
                break

        if not matched and is_transfer:
            # Fallback: assign generic transfer categories
            if "PAYMENT" in desc_upper:
                cat_id = transfer_cat_ids.get("Card Payments")
            elif "ACH" in desc_upper:
                cat_id = transfer_cat_ids.get("ACH Transfers")
            elif "INTEREST" in desc_upper:
                cat_id = transfer_cat_ids.get("Interest Charges")
            else:
                cat_id = None
            if cat_id:
                conn.execute(
                    "UPDATE transactions SET category_id=? WHERE id=?",
                    (cat_id, txn_id),
                )
                categorized_count += 1

    conn.commit()

    remaining = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE category_id IS NULL AND is_transfer=0"
    ).fetchone()[0]

    conn.close()
    print(json.dumps({
        "newly_categorized": categorized_count,
        "remaining_uncategorized": remaining,
    }, indent=2))


def cmd_uncategorized():
    """Show uncategorized transactions grouped by description pattern."""
    conn = get_db()
    rows = conn.execute("""
        SELECT description, COUNT(*) as cnt, SUM(amount) as total,
               MIN(date) as first_date, MAX(date) as last_date
        FROM transactions
        WHERE category_id IS NULL AND is_transfer=0
        GROUP BY description
        ORDER BY cnt DESC, total ASC
    """).fetchall()
    conn.close()

    results = [
        {
            "description": row[0],
            "count": row[1],
            "total": round(row[2], 2),
            "first_date": row[3],
            "last_date": row[4],
        }
        for row in rows
    ]
    print(json.dumps(results, indent=2))


def cmd_add_rule(pattern, category_name):
    """Add a keyword categorization rule."""
    conn = get_db()
    cat = _find_category(conn, category_name)
    if cat is None:
        print(f"ERROR: Category '{category_name}' not found.")
        conn.close()
        sys.exit(1)

    conn.execute(
        """INSERT OR REPLACE INTO categorization_rules
           (pattern, pattern_type, category_id, priority, source)
           VALUES (?, 'keyword', ?, 100, 'manual')""",
        (pattern, cat[0]),
    )
    conn.commit()

    # Apply immediately
    count = _apply_single_rule(conn, pattern, cat[0])
    conn.commit()
    conn.close()
    print(json.dumps({
        "rule_added": pattern,
        "category": category_name,
        "transactions_matched": count,
    }, indent=2))


def cmd_set_category(txn_id, category_name, create_rule=False):
    """Set category for a specific transaction."""
    conn = get_db()
    cat = _find_category(conn, category_name)
    if cat is None:
        print(f"ERROR: Category '{category_name}' not found.")
        conn.close()
        sys.exit(1)

    conn.execute(
        "UPDATE transactions SET category_id=? WHERE id=?",
        (cat[0], int(txn_id)),
    )

    rule_info = None
    if create_rule:
        txn = conn.execute(
            "SELECT description FROM transactions WHERE id=?", (int(txn_id),)
        ).fetchone()
        if txn:
            desc = txn[0]
            # Use first significant word(s) as pattern
            conn.execute(
                """INSERT OR REPLACE INTO categorization_rules
                   (pattern, pattern_type, category_id, priority, source)
                   VALUES (?, 'keyword', ?, 50, 'user_correction')""",
                (desc, cat[0]),
            )
            matched = _apply_single_rule(conn, desc, cat[0])
            rule_info = {"pattern": desc, "also_matched": matched}

    conn.commit()
    conn.close()
    result = {"transaction_id": txn_id, "category": category_name}
    if rule_info:
        result["rule_created"] = rule_info
    print(json.dumps(result, indent=2))


def cmd_query(sql):
    """Execute a SQL query and return results as JSON."""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(sql)
        if cursor.description:
            cols = [d[0] for d in cursor.description]
            rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
            print(json.dumps(rows, indent=2, default=str))
        else:
            conn.commit()
            print(json.dumps({"rows_affected": conn.execute("SELECT changes()").fetchone()[0]}))
    except sqlite3.Error as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_transactions():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    conn.close()
    return count


def _find_category(conn, name):
    """Find category by name (case-insensitive). Returns (id, name) or None."""
    row = conn.execute(
        "SELECT id, name FROM categories WHERE LOWER(name) = LOWER(?)", (name,)
    ).fetchone()
    return row


def _apply_single_rule(conn, pattern, cat_id):
    """Apply a single keyword rule to uncategorized transactions. Returns count."""
    pattern_upper = pattern.upper()
    uncategorized = conn.execute(
        "SELECT id, description FROM transactions WHERE category_id IS NULL"
    ).fetchall()
    count = 0
    for txn_id, desc in uncategorized:
        if pattern_upper in desc.upper():
            conn.execute(
                "UPDATE transactions SET category_id=? WHERE id=?",
                (cat_id, txn_id),
            )
            count += 1
    return count


# ---------------------------------------------------------------------------
# Dashboard, Preflight, Rebuild
# ---------------------------------------------------------------------------


def _count_log_files(source_name):
    """Count files tracked in a processing log. Returns (count, last_run)."""
    log_path = PROCESSING_LOGS.get(source_name)
    if not log_path or not log_path.exists():
        return 0

    try:
        data = json.loads(log_path.read_text())
    except (json.JSONDecodeError, KeyError):
        return 0

    if source_name == "CC Statements":
        # cards -> {card_name -> {processed: {filename: ...}}}
        count = 0
        for card in data.get("cards", {}).values():
            count += len(card.get("processed", {}))
        return count
    elif source_name == "Tax Documents":
        # files -> {filename: {...}}
        return len(data.get("files", {}))
    elif source_name == "Payslips":
        # employers -> {name -> {files_scanned: {filename: ...}}}
        count = 0
        for emp in data.get("employers", {}).values():
            fs = emp.get("files_scanned", {})
            if isinstance(fs, dict):
                count += len(fs)
        return count
    elif source_name == "Fidelity":
        # Flat dict: {filename.pdf: {...}, ...} — no version wrapper
        return len([k for k in data if k.endswith(".pdf")])
    elif source_name in ("SoFi Loan", "BECU", "WF Car Loan"):
        # pdfs -> {filename: {...}}
        return len(data.get("pdfs", {}))
    return 0


def _count_pending_files(source_name):
    """Count PDF files in source dir not yet in processing log."""
    dirs = SOURCE_DIRS.get(source_name, [])
    if isinstance(dirs, Path):
        dirs = [dirs]

    processed = _count_log_files(source_name)

    # Count PDFs in source dirs
    total_pdfs = 0
    for d in dirs:
        if d.exists():
            total_pdfs += len(list(d.rglob("*.pdf")))

    return total_pdfs, max(0, total_pdfs - processed)


def _get_log_last_run(log_path):
    """Extract last_run timestamp from a processing log."""
    if not log_path.exists():
        return None
    try:
        data = json.loads(log_path.read_text())
        # Most logs have a top-level last_run key
        if "last_run" in data:
            return data["last_run"]
        # Fidelity uses flat format — find latest processed_at
        timestamps = []
        for v in data.values():
            if isinstance(v, dict) and "processed_at" in v:
                timestamps.append(v["processed_at"])
        return max(timestamps) if timestamps else None
    except (json.JSONDecodeError, KeyError):
        return None


def cmd_dashboard():
    """Print comprehensive pipeline status as JSON."""
    conn = get_db()
    sources = []

    # DB table configs: source_name -> (table, date_col)
    db_tables = {
        "CC Statements": ("transactions", "date"),
        "Tax Documents": ("tax_documents", "tax_year"),
        "Payslips": ("payslips", "pay_date"),
        "Fidelity": ("fidelity_cma_transactions", "date"),
        "SoFi Loan": ("sofi_loan_statements", "statement_month"),
        "BECU": ("becu_checking_statements", "statement_month"),
        "WF Car Loan": ("wellsfargo_car_statements", "statement_month"),
    }

    for name, log_path in PROCESSING_LOGS.items():
        # Processing log stats
        files_processed = _count_log_files(name)
        last_ingest = _get_log_last_run(log_path)

        # DB row count and date range
        db_rows = 0
        date_range = None
        table, date_col = db_tables.get(name, (None, None))
        if table:
            try:
                db_rows = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                dr = conn.execute(
                    f"SELECT MIN({date_col}), MAX({date_col}) FROM {table}"
                ).fetchone()
                if dr and dr[0]:
                    date_range = f"{dr[0]} to {dr[1]}"
            except sqlite3.OperationalError:
                pass

        # Pending files
        total_pdfs, pending = _count_pending_files(name)

        # Staleness: >7 days since last ingest
        stale = False
        if last_ingest:
            try:
                last_dt = datetime.fromisoformat(last_ingest.replace("Z", "+00:00"))
                stale = (datetime.now(last_dt.tzinfo) - last_dt).days > 7
            except (ValueError, TypeError):
                pass

        sources.append({
            "name": name,
            "files_processed": files_processed,
            "db_rows": db_rows,
            "date_range": date_range,
            "last_ingest": last_ingest,
            "pending_files": pending,
            "stale": stale,
        })

    # Categorization stats
    cc_total = cc_cat = 0
    amz_total = amz_cat = 0
    try:
        cc_total = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE is_transfer=0"
        ).fetchone()[0]
        cc_cat = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE is_transfer=0 AND category_id IS NOT NULL"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        pass
    try:
        amz_total = conn.execute("SELECT COUNT(*) FROM amazon_orders").fetchone()[0]
        amz_cat = conn.execute(
            "SELECT COUNT(*) FROM amazon_orders WHERE category_id IS NOT NULL"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        pass

    cc_pct = round(cc_cat / cc_total * 100, 1) if cc_total else 0
    amz_pct = round(amz_cat / amz_total * 100, 1) if amz_total else 0

    # DB size
    db_size_kb = round(DB_PATH.stat().st_size / 1024) if DB_PATH.exists() else 0

    # Freshness warnings
    warnings = []
    for s in sources:
        if s["stale"]:
            warnings.append(f"{s['name']}: stale (last ingest {s['last_ingest']})")
        if s["pending_files"] > 0:
            warnings.append(f"{s['name']}: {s['pending_files']} new PDFs detected")
    if cc_total - cc_cat > 0:
        warnings.append(f"CC: {cc_total - cc_cat} uncategorized transactions")
    if amz_total - amz_cat > 0:
        warnings.append(f"Amazon: {amz_total - amz_cat} uncategorized orders")

    conn.close()
    result = {
        "sources": sources,
        "categorization": {
            "cc_pct": cc_pct,
            "amazon_pct": amz_pct,
            "cc_uncategorized": cc_total - cc_cat,
            "amazon_uncategorized": amz_total - amz_cat,
        },
        "db_size_kb": db_size_kb,
        "freshness_warnings": warnings,
    }
    print(json.dumps(result, indent=2))


def cmd_preflight():
    """Run pre-flight checks and report readiness as JSON."""
    checks = []
    blocked = []

    # Source dirs
    for name, dirs in SOURCE_DIRS.items():
        if isinstance(dirs, Path):
            dirs = [dirs]
        all_ok = True
        for d in dirs:
            if not d.exists():
                all_ok = False
                checks.append({"name": f"Source: {name}", "status": "blocked",
                                "detail": f"Missing: {d}"})
                blocked.append(f"Source: {name} — {d} not found")
                break
        if all_ok:
            log_count = _count_log_files(name)
            _, pending = _count_pending_files(name)
            checks.append({"name": f"Source: {name}", "status": "ok",
                            "detail": f"{log_count} processed, {pending} new"})

    # DB writable
    db_dir = DB_PATH.parent
    if db_dir.exists() and os.access(str(db_dir), os.W_OK):
        checks.append({"name": "DB writable", "status": "ok"})
    else:
        checks.append({"name": "DB writable", "status": "blocked",
                        "detail": f"{db_dir} not writable"})
        blocked.append("DB directory not writable")

    # Venv
    venv_path = Path(VENV_PYTHON)
    if venv_path.exists():
        checks.append({"name": "Venv", "status": "ok"})
    else:
        checks.append({"name": "Venv", "status": "blocked",
                        "detail": f"{VENV_PYTHON} not found"})
        blocked.append("Python venv not found")

    # Dependencies (pdfminer)
    try:
        subprocess.run(
            [VENV_PYTHON, "-c", "import pdfminer"],
            capture_output=True, timeout=5, check=True,
        )
        checks.append({"name": "Dependencies", "status": "ok"})
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        checks.append({"name": "Dependencies", "status": "blocked",
                        "detail": "pdfminer not importable"})
        blocked.append("pdfminer dependency missing")

    # Processing logs
    for name, log_path in PROCESSING_LOGS.items():
        if log_path.exists():
            checks.append({"name": f"Log: {name}", "status": "ok"})
        else:
            checks.append({"name": f"Log: {name}", "status": "ok",
                            "detail": "will be created"})

    # Rules backup
    if RULES_BACKUP_PATH.exists():
        try:
            rules_data = json.loads(RULES_BACKUP_PATH.read_text())
            if isinstance(rules_data, dict) and "rules" in rules_data:
                count = len(rules_data["rules"])
            elif isinstance(rules_data, list):
                count = len(rules_data)
            else:
                count = 0
            checks.append({"name": "Rules backup", "status": "ok",
                            "detail": f"{count} rules"})
        except (json.JSONDecodeError, KeyError):
            checks.append({"name": "Rules backup", "status": "ok",
                            "detail": "exists but unreadable format"})
    else:
        checks.append({"name": "Rules backup", "status": "warn",
                        "detail": "categorization_rules.json not found"})

    ready = len(blocked) == 0
    print(json.dumps({"ready": ready, "checks": checks, "blocked": blocked}, indent=2))
    return ready


def cmd_rebuild():
    """Full pipeline rebuild: parallel parse → sequential import."""
    args = sys.argv[2:]
    force = "--force" in args
    import_only = "--import-only" in args
    parse_only = "--parse-only" in args

    # Pre-flight gate
    print("=== Pre-flight checks ===")
    ready = cmd_preflight()
    if not ready:
        print("\nERROR: Pre-flight checks failed. Fix blocked items before rebuild.")
        sys.exit(1)
    print()

    # Collect issues across phases for log_issues() at the end
    rebuild_parse_errors = []
    rebuild_balance_errors = None
    rebuild_categorization = None

    # Phase 1: Parallel Parse
    if not import_only:
        print("=== Phase 1: Parallel Parse (PDF → YAML/CSV) ===")
        procs = []
        for name, cmd in INGEST_SCRIPTS:
            full_cmd = list(cmd)
            if force:
                full_cmd.append("--force")
            proc = subprocess.Popen(
                full_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, cwd=str(VAULT_ROOT),
            )
            procs.append((name, proc))
            print(f"  Started: {name}")

        # Collect results
        errors = []
        for i, (name, proc) in enumerate(procs, 1):
            stdout, stderr = proc.communicate()
            status = "done" if proc.returncode == 0 else "FAILED"
            if proc.returncode != 0:
                errors.append(name)
                rebuild_parse_errors.append((name, stderr.strip().split("\n")[-1] if stderr else "unknown error"))
            # Count new files from stdout if possible
            detail = ""
            if stdout:
                lines = stdout.strip().split("\n")
                # Show last meaningful line as summary
                for line in reversed(lines):
                    line = line.strip()
                    if line and not line.startswith("{"):
                        detail = f" — {line}"
                        break
            print(f"  [{i}/{len(procs)}] {name}: {status}{detail}")
            if proc.returncode != 0 and stderr:
                for line in stderr.strip().split("\n")[-3:]:
                    print(f"    stderr: {line}")

        if errors:
            print(f"\nWARNING: {len(errors)} ingest script(s) had errors: {', '.join(errors)}")
            print("Continuing with import phase...\n")
        else:
            print(f"\nAll {len(procs)} ingest scripts completed successfully.\n")

    if parse_only:
        print("=== Parse-only mode: skipping import phase ===")
        return

    # Phase 2: Sequential Import
    print("=== Phase 2: Sequential Import (YAML/CSV → SQLite) ===")
    import_steps = [
        ("Init schema", cmd_init),
        ("Restore rules", cmd_restore_rules),
        ("Import CC transactions", cmd_import),
        ("Categorize CC", cmd_categorize),
        ("Import Amazon orders", cmd_import_amazon),
        ("Categorize Amazon", cmd_categorize_amazon),
        ("Import payslips", cmd_import_payslips),
        ("Import tax documents", cmd_import_tax),
        ("Import Fidelity", cmd_import_fidelity),
        ("Import SoFi", cmd_import_sofi),
        ("Import BECU", cmd_import_becu),
        ("Import WF Car Loan", cmd_import_wellsfargo_car),
        ("Validate balances", cmd_validate),
    ]

    # Capture stdout from import steps to extract issues
    import io
    from contextlib import redirect_stdout

    for i, (step_name, func) in enumerate(import_steps, 1):
        print(f"\n  [{i}/{len(import_steps)}] {step_name}...")
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                func()
            output = buf.getvalue()
            print(output, end="")

            # Extract issues from specific steps
            if step_name == "Validate balances":
                try:
                    data = json.loads(output)
                    if data.get("status") == "errors":
                        rebuild_balance_errors = data["errors"]
                except (json.JSONDecodeError, ValueError):
                    pass
            elif step_name in ("Categorize CC", "Categorize Amazon"):
                try:
                    data = json.loads(output)
                    if rebuild_categorization is None:
                        rebuild_categorization = {}
                    if step_name == "Categorize CC":
                        rebuild_categorization["cc_uncategorized"] = data.get("remaining_uncategorized", 0)
                    else:
                        rebuild_categorization["amazon_uncategorized"] = data.get("remaining_uncategorized", 0)
                except (json.JSONDecodeError, ValueError):
                    pass
        except Exception as e:
            print(f"    ERROR: {e}")
            print(f"    Continuing with next step...")

    # Persist all issues
    log_issues(
        balance_errors=rebuild_balance_errors,
        parse_errors=rebuild_parse_errors if rebuild_parse_errors else None,
        categorization=rebuild_categorization,
    )
    print(f"\n  Issues log: {ISSUES_PATH}")
    print("\n=== Rebuild complete ===")


# ---------------------------------------------------------------------------
# Trip Tagging
# ---------------------------------------------------------------------------

# Patterns that are clearly NOT trip-related (home subscriptions, recurring, etc.)
NON_TRIP_PATTERNS = [
    "AMAZON", "APPLE.COM/BILL", "STARLINK", "COMCAST", "GOOGLE *FI",
    "CLAUDE.AI", "OPENAI", "LEETCODE", "BACKBLAZE", "SQSP*",
    "ADOBE", "W8TECH", "CAMPNAB", "D J*WSJ", "GARMIN",
    "TESLA SUBSCRIPTION", "TESLA SUPERCHARGER",
    "YMCA", "ADVANTAGE PHYSICAL", "VIRGINIA MASON", "NEW VISION",
    "Yu Ding", "ISSAQUAH SCHOOL", "BRIGHT HORIZONS",
    "SAMMAMISH PLATEAU WATE", "CTLP*CSC",
    "GREAT WOLF",  # separate trip
    "FlexiSpot", "eBay", "VERITASVANS", "TOBEYSTUTO",
    "Audible*", "Kindle Svcs",
]


def cmd_add_trip():
    """Register a trip. Usage: add-trip <id> <start> <end> [--name N] [--type T]
    [--booking B] [--keywords k1,k2,...] [--file F] [--notes N]"""
    args = sys.argv[2:]
    if len(args) < 3:
        print("Usage: add-trip <id> <start-date> <end-date> [--name ...] [--type solo|family] "
              "[--booking costco|direct|expedia|chase-points] [--keywords k1,k2,...] [--file path] [--notes ...]")
        sys.exit(1)

    trip_id, start_date, end_date = args[0], args[1], args[2]

    def _get_flag(flag):
        for i, a in enumerate(args):
            if a == flag and i + 1 < len(args):
                return args[i + 1]
        return None

    name = _get_flag("--name") or trip_id
    trip_type = _get_flag("--type")
    booking = _get_flag("--booking")
    keywords = _get_flag("--keywords")
    trip_file = _get_flag("--file")
    notes = _get_flag("--notes")

    # Store keywords as JSON array
    kw_json = json.dumps(keywords.split(",")) if keywords else None

    conn = get_db()
    conn.execute(
        """INSERT OR REPLACE INTO trips(id, name, start_date, end_date, trip_type,
           booking_method, location_keywords, trip_file, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (trip_id, name, start_date, end_date, trip_type, booking, kw_json, trip_file, notes),
    )
    conn.commit()
    conn.close()
    print(f"Trip '{trip_id}' registered: {start_date} to {end_date}")


def cmd_list_trips():
    """List all registered trips."""
    conn = get_db()
    rows = conn.execute(
        """SELECT t.id, t.name, t.start_date, t.end_date, t.trip_type, t.booking_method,
                  COUNT(tx.id) as tagged_txns,
                  ROUND(SUM(CASE WHEN tx.is_transfer=0 THEN ABS(tx.amount) ELSE 0 END), 2) as total_cost
           FROM trips t
           LEFT JOIN transactions tx ON tx.trip_id = t.id
           GROUP BY t.id ORDER BY t.start_date"""
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r[0], "name": r[1], "start_date": r[2], "end_date": r[3],
            "type": r[4], "booking": r[5], "tagged_txns": r[6],
            "total_cost": r[7] or 0,
        })
    print(json.dumps(result, indent=2))


def cmd_tag_trip():
    """Auto-tag transactions for a trip by date range + location keywords.
    Usage: tag-trip <trip-id> [--dry-run] [--include-pre-trip]"""
    if len(sys.argv) < 3:
        print("Usage: tag-trip <trip-id> [--dry-run] [--include-pre-trip]")
        sys.exit(1)

    trip_id = sys.argv[2]
    dry_run = "--dry-run" in sys.argv
    include_pre = "--include-pre-trip" in sys.argv

    conn = get_db()
    trip = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        print(f"Trip '{trip_id}' not found. Use list-trips to see registered trips.")
        conn.close()
        sys.exit(1)

    trip_name = trip[1]
    start_date = trip[2]
    end_date = trip[3]
    kw_json = trip[6]
    keywords = json.loads(kw_json) if kw_json else []

    # Build query: transactions within date range, not already tagged, not transfers
    query = """
        SELECT t.id, t.date, t.description, t.amount, a.name as card,
               COALESCE(c.name, 'Uncategorized') as category, t.is_transfer, t.trip_id
        FROM transactions t
        JOIN accounts a ON a.id = t.account_id
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.date BETWEEN ? AND ?
        ORDER BY t.date, t.description
    """
    rows = conn.execute(query, (start_date, end_date)).fetchall()

    tagged = []
    skipped_non_trip = []
    skipped_already = []

    for r in rows:
        txn_id, date, desc, amount, card, category, is_transfer, existing_trip = r
        desc_upper = desc.upper()

        # Skip if already tagged to another trip
        if existing_trip and existing_trip != trip_id:
            skipped_already.append(r)
            continue

        # Skip non-trip patterns
        is_non_trip = any(pat.upper() in desc_upper for pat in NON_TRIP_PATTERNS)
        if is_non_trip:
            skipped_non_trip.append(r)
            continue

        # Check if description matches location keywords
        matches_location = any(kw.upper() in desc_upper for kw in keywords)

        # Also include travel-category transactions (flights, lodging, rental car, etc.)
        travel_categories = {"Flights", "Lodging", "Rental Car", "Travel", "Parking"}
        is_travel_cat = category in travel_categories

        # Include if: matches location OR is a travel category OR is a restaurant/gas/coffee at trip location
        local_categories = {"Restaurants", "Fast Food", "Coffee", "Groceries", "Gas"}
        is_local_spend = category in local_categories

        if matches_location or is_travel_cat or is_local_spend:
            tagged.append(r)

    # Print results
    print(f"\n=== Auto-tag results for trip '{trip_id}' ({trip_name}) ===")
    print(f"Date range: {start_date} to {end_date}")
    print(f"Location keywords: {keywords}")
    print(f"\n--- WILL TAG ({len(tagged)} transactions) ---")
    total = 0
    for r in tagged:
        amt = abs(r[3]) if r[3] < 0 else -r[3]  # show charges as positive
        total += abs(r[3])
        sign = "" if r[3] < 0 else "(refund) "
        print(f"  {r[1]}  ${abs(r[3]):>9.2f}  {sign}{r[2][:55]:<55}  [{r[5]}]")
    print(f"  {'':>10} ----------")
    print(f"  {'':>10} ${total:>9.2f}  TOTAL")

    if skipped_non_trip:
        print(f"\n--- SKIPPED as non-trip ({len(skipped_non_trip)}) ---")
        for r in skipped_non_trip:
            print(f"  {r[1]}  ${abs(r[3]):>9.2f}  {r[2][:55]}")

    if skipped_already:
        print(f"\n--- SKIPPED as tagged to other trip ({len(skipped_already)}) ---")
        for r in skipped_already:
            print(f"  {r[1]}  ${abs(r[3]):>9.2f}  {r[2][:55]}  [trip: {r[7]}]")

    if dry_run:
        print(f"\n(Dry run — no changes made. Remove --dry-run to apply.)")
    else:
        for r in tagged:
            conn.execute("UPDATE transactions SET trip_id = ? WHERE id = ?", (trip_id, r[0]))
        conn.commit()
        print(f"\nTagged {len(tagged)} transactions to trip '{trip_id}'.")

    conn.close()


def cmd_untag_trip():
    """Remove all trip tags for a trip. Usage: untag-trip <trip-id>"""
    if len(sys.argv) < 3:
        print("Usage: untag-trip <trip-id>")
        sys.exit(1)
    trip_id = sys.argv[2]
    conn = get_db()
    cur = conn.execute("UPDATE transactions SET trip_id = NULL WHERE trip_id = ?", (trip_id,))
    conn.commit()
    print(f"Untagged {cur.rowcount} transactions from trip '{trip_id}'.")
    conn.close()


def cmd_tag_txn():
    """Manually tag a transaction to a trip. Usage: tag-txn <txn-id> <trip-id>"""
    if len(sys.argv) < 4:
        print("Usage: tag-txn <txn-id> <trip-id>")
        sys.exit(1)
    txn_id, trip_id = sys.argv[2], sys.argv[3]
    conn = get_db()
    # Verify trip exists
    if not conn.execute("SELECT 1 FROM trips WHERE id = ?", (trip_id,)).fetchone():
        print(f"Trip '{trip_id}' not found.")
        conn.close()
        sys.exit(1)
    cur = conn.execute("UPDATE transactions SET trip_id = ? WHERE id = ?", (trip_id, txn_id))
    if cur.rowcount == 0:
        print(f"Transaction {txn_id} not found.")
    else:
        row = conn.execute(
            "SELECT date, description, amount FROM transactions WHERE id = ?", (txn_id,)
        ).fetchone()
        print(f"Tagged txn {txn_id} ({row[0]} ${abs(row[2]):.2f} {row[1][:50]}) → trip '{trip_id}'")
    conn.commit()
    conn.close()


def cmd_trip_cost():
    """Show cost breakdown for a trip. Usage: trip-cost <trip-id>"""
    if len(sys.argv) < 3:
        print("Usage: trip-cost <trip-id> [--detail]")
        sys.exit(1)
    trip_id = sys.argv[2]
    detail = "--detail" in sys.argv

    conn = get_db()
    trip = conn.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)).fetchone()
    if not trip:
        print(f"Trip '{trip_id}' not found.")
        conn.close()
        sys.exit(1)

    # Get all tagged transactions
    rows = conn.execute(
        """SELECT t.date, t.description, t.amount, a.name as card,
                  COALESCE(cp.name, c.name, 'Uncategorized') as top_category,
                  COALESCE(c.name, 'Uncategorized') as sub_category,
                  t.is_transfer
           FROM transactions t
           JOIN accounts a ON a.id = t.account_id
           LEFT JOIN categories c ON c.id = t.category_id
           LEFT JOIN categories cp ON cp.id = c.parent_id
           WHERE t.trip_id = ?
           ORDER BY t.date""",
        (trip_id,),
    ).fetchall()

    if not rows:
        print(f"No transactions tagged for trip '{trip_id}'.")
        conn.close()
        return

    # Build breakdown by category
    by_category = {}
    grand_total = 0
    txn_list = []

    for r in rows:
        date, desc, amount, card, top_cat, sub_cat, is_xfer = r
        cost = abs(amount) if amount < 0 else -amount  # charges positive, refunds negative
        if is_xfer:
            continue
        by_category.setdefault(top_cat, {"total": 0, "items": []})
        by_category[top_cat]["total"] += cost
        by_category[top_cat]["items"].append((date, desc, cost, card, sub_cat))
        grand_total += cost
        txn_list.append(r)

    result = {
        "trip_id": trip_id,
        "name": trip[1],
        "dates": f"{trip[2]} to {trip[3]}",
        "type": trip[4],
        "booking_method": trip[5],
        "total_cost": round(grand_total, 2),
        "transaction_count": len(txn_list),
        "breakdown": {},
    }

    for cat in sorted(by_category, key=lambda c: by_category[c]["total"], reverse=True):
        info = by_category[cat]
        cat_data = {"total": round(info["total"], 2), "count": len(info["items"])}
        if detail:
            cat_data["transactions"] = [
                {"date": i[0], "description": i[1][:60], "amount": round(i[2], 2), "card": i[3]}
                for i in info["items"]
            ]
        result["breakdown"][cat] = cat_data

    print(json.dumps(result, indent=2))
    conn.close()


# ---------------------------------------------------------------------------
# Pending transaction matching
# ---------------------------------------------------------------------------

ACCOUNT_TABLE_MAP = {
    # CMA
    "cma": "fidelity_cma_transactions",
    # Credit cards
    "apple-card": "transactions",
    "chase-prime": "transactions",
    "chase-sapphire": "transactions",
    "chase-freedom": "transactions",
    "fidelity-cc": "transactions",
    "bofa-atmos": "transactions",
    # BECU
    "becu-checking": "becu_checking_transactions",
    # Amazon
    "amazon": "amazon_orders",
}

# Map short account names to DB account names (for CC transactions table)
ACCOUNT_NAME_MAP = {
    "apple-card": "apple-card",
    "chase-prime": "chase-prime-1158",
    "chase-sapphire": "chase-sapphire-2341",
    "chase-freedom": "chase-freedom-1350",
    "fidelity-cc": "fidelity-credit-card",
    "bofa-atmos": "bofa-atmos-7982",
}


def cmd_match_pending():
    """Match pending transactions from YAML log against imported DB transactions."""
    if not PENDING_TXN_PATH.exists():
        print(json.dumps({"error": "No pending transactions file found"}))
        return

    with open(PENDING_TXN_PATH, encoding="utf-8") as f:
        entries = yaml.safe_load(f) or []

    if not entries:
        print(json.dumps({"message": "No pending entries", "matched": 0, "stale": 0}))
        return

    # Detect duplicate pending entries (same account + amount + date ±1 day)
    duplicates = []
    pending = [e for e in entries if e.get("status") == "pending"]
    seen = set()
    for e in pending:
        key = (e.get("account", ""), round(float(e.get("amount", 0)), 2), e.get("date", ""))
        if key in seen:
            duplicates.append({
                "date": e.get("date"),
                "account": e.get("account"),
                "amount": e.get("amount"),
                "memo": e.get("memo"),
            })
        seen.add(key)

    conn = get_db()
    matched = 0
    stale = 0
    results = []
    today = datetime.now()

    for entry in entries:
        if entry.get("status") != "pending":
            continue

        account = entry.get("account", "")
        table = ACCOUNT_TABLE_MAP.get(account)
        if not table:
            results.append({
                "entry": entry.get("memo", ""),
                "result": f"unknown account: {account}",
            })
            continue

        target_date = entry.get("date", "")
        target_amount = float(entry.get("amount", 0))
        category = entry.get("category", "")

        # Check for stale (45+ days)
        try:
            entry_date = datetime.strptime(target_date, "%Y-%m-%d")
            if (today - entry_date).days > 45:
                entry["status"] = "stale"
                stale += 1
                results.append({
                    "entry": entry.get("memo", ""),
                    "result": "stale (45+ days)",
                })
                continue
        except ValueError:
            pass

        # Match based on table type
        match_found = False

        if table == "fidelity_cma_transactions":
            rows = conn.execute(
                """SELECT id, date, amount, description, category
                   FROM fidelity_cma_transactions
                   WHERE date BETWEEN date(?, '-5 days') AND date(?, '+5 days')
                     AND ABS(amount - ?) < 1.0""",
                (target_date, target_date, target_amount),
            ).fetchall()

            for row in rows:
                txn_id, txn_date, txn_amount, txn_desc, txn_cat = row
                if txn_cat and txn_cat == category:
                    # Already correctly categorized
                    entry["status"] = "matched"
                    matched += 1
                    match_found = True
                    results.append({
                        "entry": entry.get("memo", ""),
                        "result": f"matched (already categorized): id={txn_id} {txn_date} ${txn_amount}",
                    })
                    break
                elif not txn_cat or txn_cat in ("Uncategorized", "Divorce — Other"):
                    # Update category
                    conn.execute(
                        "UPDATE fidelity_cma_transactions SET category=? WHERE id=?",
                        (category, txn_id),
                    )
                    entry["status"] = "matched"
                    matched += 1
                    match_found = True
                    results.append({
                        "entry": entry.get("memo", ""),
                        "result": f"matched & categorized: id={txn_id} {txn_date} ${txn_amount} → {category}",
                    })
                    break

        elif table == "transactions":
            # CC transactions — need account_id join
            db_account = ACCOUNT_NAME_MAP.get(account)
            if db_account:
                rows = conn.execute(
                    """SELECT t.id, t.date, t.amount, t.description, t.category_id
                       FROM transactions t
                       JOIN accounts a ON a.id = t.account_id
                       WHERE a.name = ?
                         AND t.date BETWEEN date(?, '-5 days') AND date(?, '+5 days')
                         AND ABS(t.amount - ?) < 1.0""",
                    (db_account, target_date, target_date, target_amount),
                ).fetchall()

                for row in rows:
                    txn_id, txn_date, txn_amount, txn_desc, txn_cat_id = row
                    if txn_cat_id is None:
                        # Look up category_id by name
                        cat_row = conn.execute(
                            "SELECT id FROM categories WHERE name=?", (category,)
                        ).fetchone()
                        if cat_row:
                            conn.execute(
                                "UPDATE transactions SET category_id=? WHERE id=?",
                                (cat_row[0], txn_id),
                            )
                            entry["status"] = "matched"
                            matched += 1
                            match_found = True
                            results.append({
                                "entry": entry.get("memo", ""),
                                "result": f"matched & categorized: id={txn_id} {txn_date} ${txn_amount} → {category}",
                            })
                            break
                    else:
                        # Already categorized
                        entry["status"] = "matched"
                        matched += 1
                        match_found = True
                        results.append({
                            "entry": entry.get("memo", ""),
                            "result": f"matched (already categorized): id={txn_id} {txn_date} ${txn_amount}",
                        })
                        break

        elif table == "amazon_orders":
            rows = conn.execute(
                """SELECT id, order_date, total_amount, product_name, category_id
                   FROM amazon_orders
                   WHERE order_date BETWEEN date(?, '-5 days') AND date(?, '+5 days')
                     AND ABS(total_amount - ABS(?)) < 1.0""",
                (target_date, target_date, target_amount),
            ).fetchall()

            for row in rows:
                order_id, order_date, amount, product, cat_id = row
                if cat_id is None:
                    cat_row = conn.execute(
                        "SELECT id FROM categories WHERE name=?", (category,)
                    ).fetchone()
                    if cat_row:
                        conn.execute(
                            "UPDATE amazon_orders SET category_id=? WHERE id=?",
                            (cat_row[0], order_id),
                        )
                        entry["status"] = "matched"
                        matched += 1
                        match_found = True
                        results.append({
                            "entry": entry.get("memo", ""),
                            "result": f"matched & categorized: id={order_id} {order_date} ${amount} → {category}",
                        })
                        break
                else:
                    entry["status"] = "matched"
                    matched += 1
                    match_found = True
                    results.append({
                        "entry": entry.get("memo", ""),
                        "result": f"matched (already categorized): id={order_id} {order_date} ${amount}",
                    })
                    break

        elif table == "becu_checking_transactions":
            rows = conn.execute(
                """SELECT t.id, t.date, t.amount, t.description
                   FROM becu_checking_transactions t
                   WHERE t.date BETWEEN date(?, '-5 days') AND date(?, '+5 days')
                     AND ABS(t.amount - ?) < 1.0""",
                (target_date, target_date, target_amount),
            ).fetchall()

            if rows:
                row = rows[0]
                entry["status"] = "matched"
                matched += 1
                match_found = True
                results.append({
                    "entry": entry.get("memo", ""),
                    "result": f"matched: id={row[0]} {row[1]} ${row[2]}",
                })

        if not match_found:
            results.append({
                "entry": entry.get("memo", ""),
                "result": "no match yet",
            })

    conn.commit()
    conn.close()

    # Write back updated statuses
    with open(PENDING_TXN_PATH, "w", encoding="utf-8") as f:
        f.write("# Manually logged transactions — reconciled during statement ingestion\n")
        f.write("# Usage: /finance log <description>\n")
        f.write("# Matched by: finance_db.py match-pending (runs after imports)\n")
        f.write("# Matching: account + date ±5 days + amount ±$1\n")
        f.write("# Statuses: pending → matched | stale (45+ days unmatched)\n\n")
        yaml.dump(entries, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(json.dumps({
        "total_pending": sum(1 for e in entries if e.get("status") == "pending"),
        "matched": matched,
        "stale": stale,
        "duplicates": duplicates,
        "details": results,
    }, indent=2))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: finance_db.py <command> [args]")
        print("Commands: init, import, import-amazon, import-payslips, import-tax, import-fidelity, import-sofi, import-becu, import-wellsfargo-car,")
        print("          status, dashboard, preflight, rebuild [--force|--import-only|--parse-only],")
        print("          categorize, categorize-amazon, uncategorized, add-rule <pattern> <category>,")
        print("          set-category <id> <category> [--create-rule], query <sql>,")
        print("          backup-rules, restore-rules, validate,")
        print("          add-trip, list-trips, tag-trip, untag-trip, tag-txn, trip-cost,")
        print("          match-pending")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        cmd_init()
    elif cmd == "import":
        cmd_import()
    elif cmd == "import-amazon":
        cmd_import_amazon()
    elif cmd == "import-payslips":
        cmd_import_payslips()
    elif cmd == "import-tax":
        cmd_import_tax()
    elif cmd == "import-fidelity":
        cmd_import_fidelity()
    elif cmd == "import-sofi":
        cmd_import_sofi()
    elif cmd == "import-becu":
        cmd_import_becu()
    elif cmd == "import-wellsfargo-car":
        cmd_import_wellsfargo_car()
    elif cmd == "status":
        cmd_status()
    elif cmd == "categorize":
        cmd_categorize()
    elif cmd == "categorize-amazon":
        cmd_categorize_amazon()
    elif cmd == "uncategorized":
        cmd_uncategorized()
    elif cmd == "add-rule":
        if len(sys.argv) < 4:
            print("Usage: finance_db.py add-rule <pattern> <category>")
            sys.exit(1)
        cmd_add_rule(sys.argv[2], sys.argv[3])
    elif cmd == "set-category":
        if len(sys.argv) < 4:
            print("Usage: finance_db.py set-category <txn_id> <category> [--create-rule]")
            sys.exit(1)
        create_rule = "--create-rule" in sys.argv
        cmd_set_category(sys.argv[2], sys.argv[3], create_rule)
    elif cmd == "validate":
        cmd_validate()
    elif cmd == "dashboard":
        cmd_dashboard()
    elif cmd == "preflight":
        cmd_preflight()
    elif cmd == "rebuild":
        cmd_rebuild()
    elif cmd == "backup-rules":
        cmd_backup_rules()
    elif cmd == "restore-rules":
        cmd_restore_rules()
    elif cmd == "query":
        if len(sys.argv) < 3:
            print("Usage: finance_db.py query <sql>")
            sys.exit(1)
        cmd_query(sys.argv[2])
    elif cmd == "add-trip":
        cmd_add_trip()
    elif cmd == "list-trips":
        cmd_list_trips()
    elif cmd == "tag-trip":
        cmd_tag_trip()
    elif cmd == "untag-trip":
        cmd_untag_trip()
    elif cmd == "tag-txn":
        cmd_tag_txn()
    elif cmd == "trip-cost":
        cmd_trip_cost()
    elif cmd == "match-pending":
        cmd_match_pending()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
