# Distributed Hilbert's Hotel (Consistent Hashing)

โครงงานวิชา Object Oriented Data Structure ภาคการศึกษา 1/2569

## โครงสร้างไฟล์และผู้รับผิดชอบ

| ไฟล์ | ผู้รับผิดชอบ | หน้าที่ |
|---|---|---|
| `hashring.py` | คนที่ 1 | วงแหวน Consistent Hashing, การเลือกอาคาร |
| `guest.py` | คนที่ 2 | ข้อมูลแขก, คำนวณเลขห้อง (Cantor pairing), ดัชนีค้นหา |
| `rebalance.py` | คนที่ 3 | เพิ่ม/ลบอาคาร, คำนวณและบันทึกการย้ายแขก |
| `experiments.py` | คนที่ 4 | ทดลอง A/B/C, hash mod N, วัดเวลา/หน่วยความจำ, กราฟ |
| `hotel_system.py`, `main.py` | คนที่ 5 | ตัวเชื่อมทุกส่วน (facade), เมนูข้อความ, export CSV |
| `tests/` | ทุกคน (คนละไฟล์ตามส่วนของตัวเอง) | unit test |

แต่ละไฟล์มี docstring บอก TODO และรายละเอียดกติกาที่ต้องทำตามกำกับไว้แล้ว
ค้นหาคำว่า `TODO(คนที่ N)` ในแต่ละไฟล์เพื่อดูว่าต้องเติมส่วนไหน

## รุ่น Python ที่ใช้

Python 3.10 ขึ้นไป (ใช้ syntax `int | None` ต้องการ Python >= 3.10)
ตรวจสอบด้วย:
```
python --version
```

## วิธีติดตั้ง (ถ้าต้องใช้ matplotlib สำหรับกราฟใน experiments.py)

```
pip install matplotlib
```

ไฟล์อื่นในโครงงานนี้ (hashring, guest, rebalance, hotel_system) ใช้แต่
`list`, `dict`, `set`, `hashlib`, `bisect` ซึ่งเป็น standard library ทั้งหมด
ไม่ต้องติดตั้งอะไรเพิ่ม

## วิธีรันโปรแกรม

```
python main.py
```

## วิธีรันเทสทั้งหมด

```
python -m unittest discover -s tests -p "test_*.py" -v
```

หรือถ้าติดตั้ง pytest ไว้:
```
python -m pytest tests/ -v
```

## วิธีรันการทดลอง (หลังจากฟังก์ชันบังคับผ่านการทดสอบแล้ว)

```
python -c "import experiments; experiments.run_experiment_A([1000, 10000, 100000])"
```
(ปรับตามฟังก์ชันจริงที่คนที่ 4 เขียนเสร็จ)

## ลำดับการพัฒนาที่แนะนำ

1. คนที่ 1 ทำ `hashring.py` ให้เสร็จก่อน (คนอื่นทุกคนต้องใช้)
2. คนที่ 2 ทำ `guest.py` ขนานกันไปได้เลย (ไม่ต้องรอคนที่ 1)
3. คนที่ 3 เริ่ม `rebalance.py` ได้เมื่อ hashring.py และ guest.py มี interface
   (ชื่อฟังก์ชัน/พารามิเตอร์) ที่ตกลงกันแล้ว แม้ตัว implementation จะยังไม่เสร็จ
   (ใช้ `raise NotImplementedError` ตามโครงที่วางไว้ไปก่อนได้)
4. คนที่ 5 ทำ `hotel_system.py` ขนานไปได้เช่นกัน โดยอิงจาก interface เดียวกัน
5. คนที่ 4 เตรียม `ModHashSystem`, ฟังก์ชันวัดเวลา/หน่วยความจำ และโครงกราฟไปพลางก่อน
   แล้วค่อยรันการทดลองจริงเมื่อฟังก์ชันบังคับข้อ 1-4 ผ่านเทสหมดแล้ว

**ก่อนเริ่มเขียนจริง ให้ทั้งกลุ่มตกลงกันเรื่องนี้ก่อน:**
- รูปแบบข้อมูลแขกที่ส่งต่อกัน (ดู `GuestRecord` ใน `guest.py`)
- ชื่อเมธอดของ `HashRing` ที่คนอื่นจะเรียกใช้ (`add_node`, `remove_node`, `get_owner`,
  `get_owner_of_guest`)
- โครงสร้าง `MigrationReport` ใน `rebalance.py` (คนที่ 4, 5 จะเอาไปใช้ทำกราฟ/CSV ต่อ)
