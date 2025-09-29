# AI ผู้ช่วยวิเคราะห์อาการ NCD และสุขภาพจิต (Backend)

โปรเจกต์นี้เป็นตัวอย่าง API สำหรับช่วยประเมินอาการเบื้องต้นและติดตามข้อมูลสุขภาพ โดยใช้เทคโนโลยี FastAPI, SQLAlchemy 2.x และ Pydantic v2

## โครงสร้างโดยรวม
```
backend/
  README.md
  requirements.txt
  run.sh
  .env.example
  app/
    db.py
    models.py
    schemas.py
    main.py
    logic/
      triage.py
      trends.py
```

## การเตรียมสภาพแวดล้อม

1. สร้าง virtual environment แล้วติดตั้ง dependency:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. ก๊อปปี้ไฟล์ `.env.example` เป็น `.env` แล้วแก้ไขค่า `DATABASE_URL` หากต้องการ (ค่า default คือ SQLite ในไฟล์ `app.db`).

## การรันเซิร์ฟเวอร์

```bash
./run.sh
```

สคริปต์จะโหลดตัวแปรจาก `.env` (ถ้ามี) แล้วสั่ง `uvicorn` ให้รันแอป FastAPI

## การย้ายโครงสร้างฐานข้อมูล

ตัวอย่างนี้ใช้ SQLite และสร้างตารางอัตโนมัติเมื่อแอปรันครั้งแรกผ่าน `app/models.py`. ในระบบจริงควรใช้เครื่องมือ migration เช่น Alembic.

## Endpoints หลัก

* `GET /health` ตรวจสอบสถานะ API
* `POST /analyze` ประเมินระดับความเร่งด่วนจากข้อมูลอาการ
* `POST /observe` บันทึกข้อมูล observation (ค่าชีววัด, แบบประเมิน ฯลฯ)
* `POST /trend` วิเคราะห์แนวโน้มค่าชีววัด/คะแนนย้อนหลัง

> **หมายเหตุ:** ระบบนี้เป็นเพียงตัวช่วยวิเคราะห์เบื้องต้น ไม่ใช่การวินิจฉัยทางการแพทย์

