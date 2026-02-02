import mysql.connector
import pandas as pd
from config.settings import *

def get_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def ensure_table():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS study_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject VARCHAR(100),
            topic VARCHAR(255),
            hours FLOAT,
            problems INT,
            date DATE
        )
    """)
    conn.commit()
    conn.close()

def insert_log(subject, topic, hours, problems, date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO study_logs (subject, topic, hours, problems, date) VALUES (%s,%s,%s,%s,%s)",
        (subject, topic, hours, problems, date)
    )
    conn.commit()
    conn.close()

def fetch_logs(subject):
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM study_logs WHERE subject=%s", conn, params=[subject])
    conn.close()
    return df
