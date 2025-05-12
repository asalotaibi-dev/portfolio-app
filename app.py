
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO
import os

# إعداد صفحة التطبيق
st.set_page_config(page_title="إدارة محفظة الأسهم", layout="wide")

# ---------- حماية بكلمة سر واسم مستخدم ----------
users = {
    "Aziz": "Aziz#123",
    "SNM": "SNM#123"
}

st.sidebar.header("🔐 تسجيل الدخول")
username = st.sidebar.selectbox("👤 اختر اسم المستخدم", options=list(users.keys()))
password = st.sidebar.text_input("🔑 كلمة المرور", type="password")

if not password or users.get(username) != password:
    st.warning("يرجى إدخال اسم المستخدم وكلمة المرور الصحيحة")
    st.stop()

# تمييز المستخدم في رأس الصفحة
st.markdown(f"### 👤 المستخدم الحالي: `{username}`")

# تحديد قاعدة البيانات الخاصة بالمستخدم
DB_PATH = f"{username.lower()}.db"
if not os.path.exists(DB_PATH):
    with sqlite3.connect(DB_PATH) as init_conn:
        init_cursor = init_conn.cursor()
        init_cursor.execute("""
            CREATE TABLE IF NOT EXISTS Lookup_Stocks (
                StockID INTEGER PRIMARY KEY,
                StockName TEXT NOT NULL
            )
        """)
        init_cursor.execute("""
            CREATE TABLE IF NOT EXISTS Lookup_TransactionTypes (
                TypeID INTEGER PRIMARY KEY,
                TypeName TEXT NOT NULL
            )
        """)
        init_cursor.execute("""
            CREATE TABLE IF NOT EXISTS Transactions (
                TransactionID INTEGER PRIMARY KEY,
                Date TEXT NOT NULL,
                StockID INTEGER,
                TypeID INTEGER,
                Quantity REAL,
                Price REAL,
                Amount REAL,
                DebitAccountID INTEGER,
                CreditAccountID INTEGER,
                Description TEXT,
                FOREIGN KEY (StockID) REFERENCES Lookup_Stocks(StockID),
                FOREIGN KEY (TypeID) REFERENCES Lookup_TransactionTypes(TypeID)
            )
        """)
        init_cursor.executemany("INSERT OR IGNORE INTO Lookup_TransactionTypes VALUES (?, ?)", [
            (1, "شراء"), (2, "بيع"), (3, "توزيعة نقدية"), (4, "سحب"), (5, "إيداع")
        ])
        init_conn.commit()

# الاتصال بقاعدة بيانات المستخدم
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()
