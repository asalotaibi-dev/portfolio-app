import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# إعداد الاتصال بقاعدة البيانات
conn = sqlite3.connect("aziz.db", check_same_thread=False)
c = conn.cursor()

# التأكد من وجود جدول العمليات
c.execute('''CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    date TEXT,
    type TEXT,
    stock_name TEXT,
    quantity REAL,
    unit_price REAL,
    total REAL,
    description TEXT
)''')
conn.commit()

# المستخدمون المسموح لهم
users = {
    "Aziz": "Aziz#123",
    "SNM": "SNM#123"
}

# إعداد صفحة ستريمليت
st.set_page_config(page_title="تطبيق المحفظة الاستثمارية", layout="wide")

# واجهة تسجيل الدخول
st.sidebar.title("🔐 تسجيل الدخول")
username = st.sidebar.selectbox("👤 اختر اسم المستخدم", list(users.keys()))
password = st.sidebar.text_input("🔑 كلمة المرور", type="password")

# التحقق من كلمة المرور
if password == users[username]:
    st.sidebar.success(f"👤 المستخدم الحالي: :green[{username}]")

    page = st.sidebar.radio("📂 اختر الصفحة", ["🔴 إدخال عملية جديدة", "📊 عرض العمليات"])

    if page == "🔴 إدخال عملية جديدة":
        st.header("📥 إدخال عملية")
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("📅 التاريخ", datetime.today())
            trans_type = st.selectbox("🧾 نوع العملية", ["شراء", "بيع", "توزيع", "مصروف", "إيداع", "سحب"])
            amount = st.number_input("💵 القيمة", min_value=0.0, step=0.01)
        with col2:
            stock_name = st.text_input("✏️ اسم السهم (اختياري)")
            quantity = st.number_input("🔢 الكمية (إن وجد)", min_value=0.0, step=1.0)
            unit_price = st.number_input("💰 السعر (إن وجد)", min_value=0.0, step=0.01)
        description = st.text_area("📝 الوصف")

        if st.button("✅ حفظ العملية"):
            total = quantity * unit_price if trans_type in ["شراء", "بيع"] else amount
            c.execute('INSERT INTO transactions (username, date, type, stock_name, quantity, unit_price, total, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                      (username, date.strftime("%Y-%m-%d"), trans_type, stock_name, quantity, unit_price, total, description))
            conn.commit()
            st.success("✅ تم حفظ العملية بنجاح")

    elif page == "📊 عرض العمليات":
        st.header("📋 العمليات السابقة")
        df = pd.read_sql_query("SELECT * FROM transactions WHERE username = ?", conn, params=(username,))
        if not df.empty:
            df.index += 1
            st.dataframe(df)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 تنزيل Excel", data=csv, file_name="transactions.csv", mime="text/csv")
        else:
            st.info("لا توجد عمليات مسجلة بعد.")
else:
    st.error("❌ كلمة المرور غير صحيحة أو لم يتم إدخالها.")
