#!/usr/bin/env python3
"""Personal finance database: import credit card CSVs, categorize, query."""

import csv
import json
import os
import re
import shutil
import sqlite3
import sys
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = VAULT_ROOT / "Finance" / "finance.db"
CSV_ROOT = VAULT_ROOT / "Finance" / "credit-card"
AMAZON_CSV_ROOT = Path.home() / "Dropbox" / "0-FinancialStatements" / "amazon"
PAYSLIP_ROOT = VAULT_ROOT / "Finance" / "payslips"

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
"""

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

ACCOUNTS = [
    ("apple-card", "Apple Card"),
    ("chase-prime-1158", "Chase Prime"),
    ("chase-sapphire-2341", "Chase Sapphire"),
    ("chase-freedom-1350", "Chase Freedom"),
    ("fidelity-rewards", "Fidelity Rewards"),
    ("fidelity-credit-card", "Fidelity Credit Card"),
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
    """Create a .bak copy of the database before destructive operations."""
    if DB_PATH.exists():
        bak = DB_PATH.with_suffix(".db.bak")
        shutil.copy2(DB_PATH, bak)
        size_kb = bak.stat().st_size / 1024
        print(f"Backup: {bak.name} ({size_kb:.0f} KB)")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init():
    """Create schema, seed accounts, categories, and rules."""
    backup_db()
    conn = get_db()
    conn.executescript(SCHEMA)

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

    total_txn = _count_transactions()
    print(json.dumps({
        "files_imported": files_imported,
        "new_transactions": total_new,
        "total_transactions": total_txn,
    }, indent=2))


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
# CLI
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: finance_db.py <command> [args]")
        print("Commands: init, import, import-amazon, import-payslips, status, categorize, categorize-amazon,")
        print("          uncategorized, add-rule <pattern> <category>,")
        print("          set-category <id> <category> [--create-rule], query <sql>")
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
    elif cmd == "query":
        if len(sys.argv) < 3:
            print("Usage: finance_db.py query <sql>")
            sys.exit(1)
        cmd_query(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
