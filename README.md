# Distributed Hilbert's Hotel (Consistent Hashing)

โครงงานวิชา Object Oriented Data Structure ภาคการศึกษา 1/2569

## โครงสร้างไฟล์และผู้รับผิดชอบ

ไฟล์ทั้งหมด (รวมไฟล์เทส) อยู่ในโฟลเดอร์รากเดียวกัน ไม่มีโฟลเดอร์ `tests/`

| ไฟล์ | ผู้รับผิดชอบ | หน้าที่ | สถานะ |
|---|---|---|---|
| `hashring.py` | คนที่ 1 | วงแหวน Consistent Hashing, การเลือกอาคาร | เสร็จ ผ่านเทส |
| `guest.py` | คนที่ 2 | ข้อมูลแขก, คำนวณเลขห้อง (Cantor pairing), ดัชนีค้นหา | เสร็จ ผ่านเทส |
| `rebalance.py` | คนที่ 3 | เพิ่ม/ลบอาคาร, คำนวณและบันทึกการย้ายแขก | |
| `experiments.py` | คนที่ 4 | ทดลอง A/B/C, hash mod N, วัดเวลา/หน่วยความจำ, กราฟ | |
| `hotel_system.py`, `main.py` | คนที่ 5 | ตัวเชื่อมทุกส่วน (facade), เมนูข้อความ, export CSV | |
| `test_*.py` | ทุกคน (คนละไฟล์ตามส่วนของตัวเอง) | unit test (`test_guest.py`, `test_hashring.py`, `test_rebalance.py`, `test_hotel_system.py`) | |
| `Distributed_Hilbert's_Hotel.py` | (ระบุผู้รับผิดชอบ) | (ระบุหน้าที่ของไฟล์นี้) | |
| `requirements.txt` | - | รายการแพ็กเกจที่ต้องติดตั้ง | |

แต่ละไฟล์มี docstring บอก TODO และรายละเอียดกติกาที่ต้องทำตามกำกับไว้แล้ว
ค้นหาคำว่า `TODO(คนที่ N)` ในแต่ละไฟล์เพื่อดูว่าต้องเติมส่วนไหน

## รุ่น Python ที่ใช้

Python 3.10 ขึ้นไป (ใช้ syntax `int | None` ต้องการ Python >= 3.10)
ตรวจสอบด้วย:
```
python --version
```

## วิธีติดตั้ง

```
pip install -r requirements.txt
```

ใช้ matplotlib สำหรับกราฟใน `experiments.py` เท่านั้น ไฟล์อื่นในโครงงานนี้
(hashring, guest, rebalance, hotel_system) ใช้แต่ `list`, `dict`, `set`, `hashlib`,
`bisect` ซึ่งเป็น standard library ทั้งหมด

## วิธีรันโปรแกรม

```
python main.py
```

## วิธีรันเทส

ต้องรันจากโฟลเดอร์รากของโปรเจกต์ (โฟลเดอร์ที่มี `guest.py` อยู่)

เทสทั้งหมด:
```
python -m unittest discover -s . -p "test_*.py" -v
```

เทสเฉพาะไฟล์ เช่น guest:
```
python -m unittest test_guest -v
```

หรือถ้าติดตั้ง pytest ไว้:
```
python -m pytest -v
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

## Interface ที่ตกลงกันแล้ว

### guest.py (คนที่ 2 เสร็จแล้ว)

- `GuestRecord(c, s, node_id, room_no)` เป็น dataclass
- `compute_room_no(c, s)` -> `int`  ใช้จำนวนเต็มล้วน raise `ValueError` ถ้า c หรือ s ไม่ใช่จำนวนเต็มบวก
- `GuestRegistry.by_guest_code` : `dict[(c, s)] -> GuestRecord`
- `GuestRegistry.by_address` : `dict[(node_id, room_no)] -> (c, s)`
- `add_guest(c, s, node_id)` -> `(ok, reason)`  รหัสซ้ำหรือไม่ถูกต้องคืน False ไม่ throw
- `add_guests_batch(c, s_start, count, node_id_lookup_fn)` -> `(ok, reason, [(c, s), ...])`
  - ปฏิเสธทั้งกลุ่มถ้ามีรหัสซ้ำแม้แต่รายการเดียว (ไม่เพิ่มบางส่วน)
  - `count == 0` คืน `(True, "ไม่มีการเปลี่ยนแปลง", [])`, `count` ติดลบถูกปฏิเสธ
- `remove_guest(c, s)` -> `(ok, reason)`  ไม่พบแล้วคืน False ไม่ throw
- `find_by_guest_code(c, s)` -> `(node_id, room_no)` หรือ `None`
- `find_by_address(node_id, room_no)` -> `(c, s)` หรือ `None`
- `update_node_of_guest(c, s, new_node_id)` -> `None`
  room_no คงเดิม อัปเดตทั้งสอง dict และ **raise `KeyError` ถ้าไม่พบแขก**
- `list_guests_in_building(node_id)` -> `[(room_no, c, s), ...]` เรียงตาม room_no
- `guest_count()`, `all_guest_codes()`

### ข้อควรระวังตอนเชื่อมไฟล์

- `HashRing.get_owner` คืน tuple `(position, node_id, j)` แต่ `node_id_lookup_fn`
  ที่ส่งเข้า `add_guests_batch` ต้องคืนแค่ `node_id` (str) ฝั่ง `hotel_system.py`
  ต้องหยิบเฉพาะ node_id ออกมาก่อน เช่น
  `lambda c, s: ring.get_owner_of_guest(c, s)[1]`
  (ถ้า `get_owner_of_guest` คืนรูปแบบต่างจากนี้ให้ปรับตามจริง)
- `guest.py` ไม่เรียก `HashRing` เอง การเลือกอาคารเป็นหน้าที่ของ HashRing และ `hotel_system.py`
- `rebalance.py` ควรเรียก `update_node_of_guest` เฉพาะแขกที่มีอยู่จริง
  (ใช้ `all_guest_codes()` เพื่อวนตรวจแขกทุกคน)

### hashring.py (คนที่ 1 เขียนครบ, test_hashring.py เขียนแล้ว)

- `hash_to_position(key)` -> `int` : sha256 -> utf-8 -> 8 ไบต์แรก big-endian (ตำแหน่ง 0 .. 2**64-1)
- `HashRing(V)` เก็บ `points` = list ของ `(position, node_id, j)` เรียงลำดับ และ `nodes` = set ของ node_id
- `add_node(node_id)` -> `bool`  ซ้ำคืน False
- `remove_node(node_id)` -> `bool`  ไม่พบ หรือเป็นอาคารสุดท้าย คืน False
- `get_owner(position)` และ `get_owner_of_guest(c, s)` คืน **tuple `(position, node_id, j)`**
  (ไม่ใช่ str ตามที่ type hint/docstring เขียนไว้) หรือ `None` ถ้าวงแหวนว่าง
  ผู้เรียกต้องใช้ `[1]` เพื่อเอา node_id
- `node_count()` = N, `point_count()` = M = N x V (เป็นเมธอด ต้องเรียกด้วย `()`)

**บั๊กที่เทสเจอใน `get_owner` (ต้องแก้ใน hashring.py ก่อน เทสจึงจะผ่านครบ 25 ข้อ)**

1. `self.node_count == 0` ต้องเป็น `self.node_count() == 0` (ไม่มี `()` เงื่อนไขจะไม่เป็นจริงเลย)
2. `index == self.point_count` ต้องเป็น `index == self.point_count()`
   (ของเดิมทำให้กรณีวนกลับต้นวงแหวน เช่น ตำแหน่ง 90 เกิด `IndexError`)
3. `bisect_left(self.points, (position, 0, 0))` ต้องเป็น `(position, "", -1)`
   (ของเดิมเทียบ `str` กับ `int` เมื่อตำแหน่งชนกัน เกิด `TypeError`)

**ข้อสังเกตเล็กน้อย (ไม่กระทบความถูกต้อง)**
- `set.remove` เป็น O(1) ดังนั้น `remove_node` รวมแล้วเป็น O(M) ไม่ใช่ O(N + M)
- ควรแก้ type hint ของ `get_owner` / `get_owner_of_guest` ให้ตรงกับที่คืนจริง

รันเทสเฉพาะส่วนนี้: `python -m unittest test_hashring -v`
