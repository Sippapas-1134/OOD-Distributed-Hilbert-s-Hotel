# Distributed Hilbert's Hotel

โครงงาน Object Oriented Data Structure ภาคการศึกษา 1/2569

ระบบเลือกอาคารด้วย Consistent Hashing และคำนวณเลขห้องด้วย Cantor pairing.
เมื่อเพิ่มแขก แขกเดิมไม่ย้าย เมื่อเพิ่ม/ลบอาคาร เปลี่ยนเฉพาะ node_id ของผู้ได้รับผลกระทบ.

## การติดตั้งและรัน

ใช้ Python 3.10 ขึ้นไป; ทดสอบการทำงานจริงบน Python 3.13.9.
ส่วนหลักใช้ standard library; matplotlib ใช้สร้างกราฟเท่านั้น.

รันคำสั่งจากโฟลเดอร์นี้ (โฟลเดอร์ที่มี Distributed_Hilbert’s_Hotel.py):

```powershell
python -m pip install -r requirements.txt
python -X utf8 "Distributed_Hilbert’s_Hotel.py"
```

ไฟล์ Distributed_Hilbert’s_Hotel.py เป็นทางเข้าชื่อเดิมและเรียกเมนูเดียวกัน.

## การใช้งานเมนู

1. เริ่มระบบ: กรอกรหัสอาคารคั่นด้วยช่องว่าง เช่น A B C (จำนวนรหัสคือ N), ค่า V>=1,
   จำนวนช่องทางเริ่มต้น และจำนวนแขกแต่ละช่องทาง โดย c=1..จำนวนช่องทาง และ s เริ่มที่ 1.
   ใส่จำนวนช่องทาง 0 เพื่อเริ่มแบบไม่มีแขกได้.
2. เพิ่มแขก: ระบุ c, s เริ่มต้น, count>=0. count=0 ไม่เปลี่ยนข้อมูล.
   ถ้ามีรหัสซ้ำในกลุ่มจะปฏิเสธทั้งกลุ่ม.
3. ลบแขก: กรอก c s.
4. เพิ่มอาคาร / 5. ลบอาคาร: ระบุ ID และดูจำนวน/อัตรา/รายการย้าย.
   แสดงสูงสุด 50 รายการ; CSV ส่งออกครบ. ลบอาคารสุดท้ายไม่ได้.
6. ค้นหาด้วย c s หรือ ID อาคารและเลขห้อง.
7. แสดงห้องเรียง node_id และ room_no พร้อมยอดรวม (หน้าจอแสดง 100 รายการแรก).
8. แสดงโหลดทุกอาคาร รวมอาคารว่าง และ max/min/mean/std/CV.
9. ส่งออกข้อมูลแขกหรือรายการย้ายล่าสุดเป็น UTF-8 CSV.
0. ออก; EOF หรือ Ctrl+C ออกได้เช่นกัน.

รหัสอาคารต้องเป็นข้อความไม่ว่าง ไม่มี whitespace และไม่ซ้ำ.
เริ่มระบบใหม่สำเร็จจะล้างแขกและรายการย้ายเก่า; ถ้ากรอกข้อมูลเริ่มใหม่ผิด ระบบเดิมยังอยู่.
เมื่อไม่มีแขก สถิติพื้นฐานเป็น 0 และ CV/อัตราย้ายไม่คำนวณ.

## รันทดสอบ

```powershell
python -X utf8 -m unittest discover -s . -p "test_*.py" -v
```

มีเทสสูตรห้อง, ดัชนีสองทาง, วงแหวนตัวอย่างในโจทย์, collision/wraparound,
การย้ายที่ V>1, ปฏิเสธคำสั่งโดยไม่เปลี่ยนข้อมูล, CV, การเรียง, initialization,
เมนู input ผิด, reset, CSV และการเรียก Distributed_Hilbert’s_Hotel.py จริง.
test_system_regressions.py เป็น regression tests สำหรับปัญหาที่พบในการตรวจโครงงาน.

## ทดลองและสร้างกราฟ

```powershell
python -X utf8 experiments.py --output results
```

- A: K=1,000/10,000/100,000; N=10, V=32.
- B: N=5/10/20; K=10,000, V=32; เพิ่ม/ลบหนึ่งอาคารจากสถานะเริ่มต้นแยกกัน.
- C: V=1/8/32; N=10, K=10,000.
- ทุกชุดใช้ 10 ช่องทาง และ salt 0/1/2 เหมือนกันทั้งสองวิธีในรอบเดียวกัน.
- CSV ดิบมี experiment, K,N,V,salt,round และค่าที่วัด; summary มีมัธยฐานและ min/max.
- เวลาใช้ perf_counter ไม่รวม input/output; ค้นหา 1,000 ครั้งแล้วหารเฉลี่ยต่อครั้ง.
- หน่วยความจำใช้ tracemalloc current/peak เป็น MiB แยกรอบจากการจับเวลา.
- กราฟมีหน่วย/พารามิเตอร์/มัธยฐาน/min-max; environment.json ระบุ Python และเครื่อง.

results/ มี CSV 3 ชุด, CSV สรุป, JSON ดิบ, environment และกราฟ 3 ภาพ.
ตัวเลขเวลาอาจเปลี่ยนตามเครื่องและภาระงาน; migration/load ทำซ้ำด้วย salt เดิมได้.
ConsistentHashSystem ใน experiments.py สืบทอด HotelSystem และเรียก rebalance เดียวกับเมนู.

## โครงสร้างข้อมูลและไฟล์

| ไฟล์ | หน้าที่ |
|---|---|
| hashring.py | HashRing, SHA-256, sorted points, binary search, optional salt |
| guest.py | GuestRecord, Cantor pairing, ดัชนีรหัสแขกและที่อยู่ห้อง |
| rebalance.py | รายการย้ายและเวลาแยกปรับวงแหวน/หาแขก/อัปเดต |
| hotel_system.py | HotelSystem และ text menu |
| Distributed_Hilbert’s_Hotel.py | จุดเริ่มต้น |
| experiments.py | ModHashSystem และการทดลอง/CSV/กราฟ |
| test_*.py | ทดสอบอัตโนมัติ |
| TECHNICAL_REPORT.md | แบบข้อมูล หลักการคำนวณ Big-O และข้อจำกัด |

## ก่อนส่งงาน

ตรวจผลเทสและแนบ results/; ไม่ต้องแนบ environment หรือแพ็กเกจที่ติดตั้ง.
นำเนื้อหาเทคนิคและผลจริงไปจัดรายงาน Word/PDF ที่มีเนื้อหาตรงกัน.
เติมรายชื่อสมาชิก หน้าที่จริง สัดส่วนงานและลายเซ็นตามโจทย์ โดยผู้จัดทำตรวจสอบความถูกต้องเอง.
