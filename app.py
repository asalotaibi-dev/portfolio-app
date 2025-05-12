
import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os

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

st.markdown(f"### 👤 المستخدم الحالي: `{username}`")

# ---------- الاتصال بقاعدة البيانات ----------
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

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cursor = conn.cursor()

# ---------- اختيار الصفحة ----------
page = st.sidebar.radio("📂 اختر الصفحة", ["📥 إدخال عملية جديدة", "📊 عرض العمليات"])

# ---------- إدخال عملية جديدة ----------
if page == "📥 إدخال عملية جديدة":
    st.subheader("📥 إدخال عملية")
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        with col1:
            date_input = st.date_input("📅 التاريخ", value=date.today())
            type_input = st.selectbox("🔁 نوع العملية", ["شراء", "بيع", "توزيعة نقدية", "سحب", "إيداع"])
            amount_input = st.number_input("💵 القيمة", min_value=0.0, step=1.0)
        with col2:
            stock_input = st.text_input("🏷️ اسم السهم (اختياري)")
            qty_input = st.number_input("🔢 الكمية (إن وجدت)", min_value=0.0, step=1.0)
            price_input = st.number_input("💰 السعر (إن وجد)", min_value=0.0, step=0.01)
        description = st.text_area("📝 الوصف")
        submitted = st.form_submit_button("✅ حفظ العملية")

        if submitted:
            stock_id = None
            if stock_input:
                cursor.execute("SELECT StockID FROM Lookup_Stocks WHERE StockName = ?", (stock_input,))
                result = cursor.fetchone()
                if result:
                    stock_id = result[0]
                else:
                    cursor.execute("INSERT INTO Lookup_Stocks (StockName) VALUES (?)", (stock_input,))
                    stock_id = cursor.lastrowid

            cursor.execute("SELECT TypeID FROM Lookup_TransactionTypes WHERE TypeName = ?", (type_input,))
            type_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO Transactions (Date, StockID, TypeID, Quantity, Price, Amount, DebitAccountID, CreditAccountID, Description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(date_input), stock_id, type_id, qty_input or None, price_input or None, amount_input, None, None, description))
            conn.commit()
            st.success("✅ تم حفظ العملية بنجاح")

# ---------- عرض العمليات ----------
elif page == "📊 عرض العمليات":
    st.subheader("📊 سجل العمليات")
    query = """
        SELECT 
            T.TransactionID AS رقم,
            T.Date AS التاريخ,
            LTT.TypeName AS النوع,
            LS.StockName AS السهم,
            T.Quantity AS الكمية,
            T.Price AS السعر,
            T.Amount AS القيمة,
            T.Description AS الوصف
        FROM Transactions T
        LEFT JOIN Lookup_Stocks LS ON T.StockID = LS.StockID
        LEFT JOIN Lookup_TransactionTypes LTT ON T.TypeID = LTT.TypeID
        ORDER BY T.Date DESC, T.TransactionID DESC
    """
    df = pd.read_sql(query, conn)
    st.dataframe(df, use_container_width=True)
