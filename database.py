import sqlite3
import pandas as pd
from datetime import datetime


def get_connection():
    """
    Returns a connection to the SQLite database.

    Returns:
        sqlite3.Connection: Active connection to domains.db
    """

    con = sqlite3.connect("domains.db")
    return con


def create_table():
    """
    Creates all required tables in the database if they don't already exist.

    Tables created:
        dns_records: Stores A, MX, NS records per domain
        ssl_certs: Stores SSL certificate data per domain
        fetch_history: Audit log of every pipeline run

    Returns:
        None
    """
    con = get_connection()
    cur = con.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS dns_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT,
                record_type TEXT,
                value TEXT,
                fetched_at TEXT,
                UNIQUE(domain,record_type ,value)
                )
            ''')

    cur.execute('''CREATE TABLE IF NOT EXISTS ssl_certs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT UNIQUE,
                issuer TEXT,
                exp_date TEXT,
                days_until_expiry INT,
                fetched_at TEXT
                )
            ''')

    cur.execute('''CREATE TABLE IF NOT EXISTS fetch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_at TEXT,
                dns_rows_added INT,
                ssl_rows_added INT
                )
            ''')

    con.commit()

    print("All tables checked/created SUCCESS")


def insert_dns_records(records):
    """Inserts a list of DNS records into the dns_records table.

    Uses INSERT OR REPLACE to avoid duplicates based on
    the UNIQUE constraint on (domain, record_type, value).

    Args:
        records: List of dicts with keys domain, record_type,
                 value, fetched_at

    Returns:
        None
    """
    con = get_connection()
    cur = con.cursor()

    sql = '''
        INSERT OR REPLACE INTO dns_records (domain, record_type, value, fetched_at)
        VALUES (:domain, :record_type, :value, :fetched_at)
    '''

    cur.executemany(sql, records)
    con.commit()
    print(f"Successfully inserted {cur.rowcount} DNS records.")


def insert_ssl_records(records):
    """Inserts a list of SSL certificate records into the ssl_certs table.

    Uses INSERT OR REPLACE to update existing rows when a domain
    is fetched again, keeping fetched_at current.

    Args:
        records: List of dicts with keys domain, issuer, exp_date,
                 days_until_expiry, fetched_at

    Returns:
        None
    """
    con = get_connection()
    cur = con.cursor()

    sql = '''
        INSERT OR REPLACE INTO ssl_certs (domain,issuer ,exp_date ,days_until_expiry ,fetched_at )
        VALUES(:domain ,:issuer ,:exp_date ,:days_until_expiry, :fetched_at)
        '''
    cur.executemany(sql, records)
    con.commit()
    print(f"Successfully inserted {cur.rowcount} SSL Certificates")


def log_fetch_run(dns_count, ssl_count):
    """Logs a completed pipeline run to the fetch_history table.

    Records the timestamp and how many DNS and SSL rows were
    processed in this run. Acts as an audit trail.

    Args:
        dns_count: Number of DNS records inserted in this run
        ssl_count: Number of SSL records inserted in this run

    Returns:
        None
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = get_connection()
    cur = con.cursor()

    sql = '''
    INSERT OR REPLACE INTO fetch_history(
    run_at,dns_rows_added,
    ssl_rows_added)
    VALUES(? , ? , ?)
    '''
    cur.execute(sql, (current_time, dns_count, ssl_count))
    con.commit()
    print(
        f"Audit log saved: Added {dns_count} DNS records and {ssl_count} SSL records.")


def get_ssl_data():
    """Retrieves all rows from the ssl_certs table.

    Returns:
        pandas.DataFrame: All SSL certificate records
    """
    con = get_connection()

    sql = '''SELECT * FROM ssl_certs'''
    return pd.read_sql_query(sql, con)


def get_dns_data():
    """Retrieves all rows from the dns_records table.

    Returns:
        pandas.DataFrame: All DNS records
    """
    con = get_connection()

    sql = '''SELECT * FROM dns_records'''
    return pd.read_sql_query(sql, con)
