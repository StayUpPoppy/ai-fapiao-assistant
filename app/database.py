import sqlite3
from contextlib import closing

from app.config import DB_PATH


def get_db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database() -> None:
    with closing(get_db_connection()) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT NOT NULL UNIQUE,
                document_type TEXT NOT NULL,
                invoice_date TEXT,
                buyer_name TEXT,
                seller_name TEXT,
                amount_excl_tax REAL,
                tax_amount REAL,
                amount_incl_tax REAL,
                items_text TEXT,
                review_status TEXT,
                review_notes TEXT,
                prepayment_amount REAL NOT NULL DEFAULT 0,
                paid_amount REAL NOT NULL DEFAULT 0,
                due_date TEXT,
                payment_status TEXT NOT NULL DEFAULT '未付款',
                owner TEXT,
                source_filename TEXT,
                raw_dify_output TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT NOT NULL,
                order_type TEXT NOT NULL,
                contract_number TEXT,
                counterparty_name TEXT,
                order_date TEXT,
                delivery_date TEXT,
                order_amount REAL NOT NULL,
                settlement_method TEXT,
                payment_terms TEXT,
                prepayment_amount REAL NOT NULL DEFAULT 0,
                paid_amount REAL NOT NULL DEFAULT 0,
                payment_status TEXT NOT NULL,
                due_date TEXT,
                owner TEXT,
                review_status TEXT NOT NULL DEFAULT '待人工确认',
                review_notes TEXT,
                source_filename TEXT,
                raw_dify_output TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(order_type, order_number)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS invoice_order_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                order_number TEXT NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                UNIQUE(invoice_id, order_number)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS notification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                channel TEXT NOT NULL,
                event_key TEXT NOT NULL,
                reminder_status TEXT NOT NULL,
                due_date TEXT NOT NULL,
                sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices(id),
                UNIQUE(invoice_id, channel, event_key)
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS order_notification_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                channel TEXT NOT NULL,
                event_key TEXT NOT NULL,
                reminder_status TEXT NOT NULL,
                due_date TEXT NOT NULL,
                sent_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                UNIQUE(order_id, channel, event_key)
            )
        """)

        connection.commit()
