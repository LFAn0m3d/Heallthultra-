import streamlit as st
from utils.auth import check_auth

st.set_page_config(page_title="HealthPulse++", layout="wide")

if check_auth():
    st.title("HealthPulse++: NCD Surveillance Platform")
    st.write("ยินดีต้อนรับสู่แดชบอร์ดเฝ้าระวังโรคเรื้อรังระดับจังหวัด")
    st.success("เลือกเมนูด้านซ้ายเพื่อดูข้อมูลแต่ละฟีเจอร์")
else:
    st.warning("กรุณาล็อกอินเพื่อเข้าถึงระบบ")
