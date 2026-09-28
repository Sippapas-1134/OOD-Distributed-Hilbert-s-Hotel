"""
rebalance.py
งานของ: คนที่ 3 -- การเพิ่ม/ลบอาคารและการย้ายแขก

ไฟล์นี้เป็นตัวเชื่อมระหว่าง hashring.py (คนที่ 1) กับ guest.py (คนที่ 2)
hotel_system.py (คนที่ 5) จะเรียกใช้ฟังก์ชันในไฟล์นี้เป็นหลักตอนผู้ใช้สั่งเพิ่ม/ลบอาคาร

หน้าที่ที่ต้องทำ (ดูกติกาในโจทย์ หัวข้อ 4.4, 4.7):

1. add_building(ring, registry, node_id) -> MigrationReport
   ขั้นตอน:
     a) เรียก ring.add_node(node_id) -- ถ้าคืน False (อาคารซ้ำ) ให้หยุดและคืน
        MigrationReport ที่บอกว่า "ปฏิเสธ: อาคารนี้มีอยู่แล้ว" โดยไม่มีใครย้าย
     b) หาแขกที่ต้องย้าย: ใช้ "แบบ ก" ตามที่โจทย์อนุญาต (ตรวจแขกทุกคน K คน คำนวณ
        อาคารใหม่ผ่าน ring.get_owner_of_guest(c, s) แล้วเทียบกับอาคารเดิม)
        ถ้า node_id ใหม่ต่างจากเดิม -> เป็นคนที่ย้าย
        ** กติกาสำคัญ: เมื่อเพิ่มอาคาร คนที่ย้ายต้องย้าย "เข้าอาคารใหม่เท่านั้น" **
        (ถ้าพบว่ามีคนย้ายไปอาคารอื่นที่ไม่ใช่อาคารใหม่ แสดงว่า logic ผิด ต้องดักด้วย assert
        ในเทส ไม่ใช่ในโค้ด production)
     c) สำหรับทุกคนที่ย้าย: เรียก registry.update_node_of_guest(c, s, new_node_id)
        และบันทึกลงรายการย้าย (c, s, old_node_id, new_node_id, room_no)
     d) คืน MigrationReport พร้อม จำนวนย้าย, อัตราย้าย (K>0 เท่านั้น), รายการย้ายละเอียด

2. remove_building(ring, registry, node_id) -> MigrationReport
   ขั้นตอนคล้ายกัน แต่ก่อนอื่นต้องเช็ค:
     - ถ้า node_id ไม่มีอยู่จริง -> ปฏิเสธ ไม่มีใครย้าย ไม่ throw exception
     - ถ้าลบแล้วจะไม่เหลืออาคารเลย (N จะกลายเป็น 0) -> ปฏิเสธ ตามกติกา N >= 1
   ถ้าผ่านทั้งสองเงื่อนไข: เรียก ring.remove_node(node_id) แล้วหาแขกที่ต้องย้าย
   (คือแขกที่เคยอยู่อาคารที่ถูกลบเท่านั้น) แล้วคำนวณอาคารใหม่ให้เฉพาะกลุ่มนี้ผ่านวงแหวน
   ** กติกาสำคัญ: เมื่อถอนอาคาร แขกในอาคารอื่นต้อง "ไม่ย้าย" เลย **
   (ดังนั้นจริง ๆ แล้วไม่จำเป็นต้องตรวจแขกทุกคนแบบตอนเพิ่มอาคาร แค่ตรวจเฉพาะแขกของ
   อาคารที่ถูกลบก็พอ -- ควรใช้ registry.list_guests_in_building(node_id) ก่อนเรียก
   ring.remove_node เพื่อรู้ว่าใครอยู่อาคารนี้บ้าง)

3. MigrationReport: โครงสร้างผลลัพธ์ที่ใช้ร่วมกันทั้งไฟล์นี้และ hotel_system.py / experiments.py
   ให้เป็นรูปแบบเดียวกันเสมอ (ดู dataclass ด้านล่าง) -- ถ้าจะแก้ฟิลด์ ต้องคุยกับคนที่ 4, 5 ก่อน
   เพราะเขาจะนำ field พวกนี้ไปใช้ทำกราฟ/CSV ต่อ

4. จำนวนแขกที่ย้าย ต้องนับเป็น "จำนวนรหัสแขก" ไม่ใช่จำนวน virtual node ที่เปลี่ยน

5. Big-O ที่ต้องวิเคราะห์ในรายงาน (แยกตามขั้นตอน):
     a) การปรับวงแหวน (เรียก ring.add_node / remove_node)
     b) การหาแขกที่ได้รับผลกระทบ (วนดู K คน + ค้นหาบนวงแหวนแต่ละคน O(log M))
     c) การปรับข้อมูล/ดัชนีของแขกที่ย้าย (registry.update_node_of_guest ต่อคน)
   ถ้าเลือกทำ "แบบ ข" (หาเฉพาะช่วงที่ได้รับผลกระทบ) เป็นงานเพิ่มเติม ให้แยกฟังก์ชัน
   ใหม่ต่างหาก (เช่น add_building_v2) และห้ามนำตัวเลขมาปนกับแบบ ก ตอนวิเคราะห์

ทดสอบที่ต้องเขียน (tests/test_rebalance.py):
- ใช้ตัวอย่างวงแหวนเล็กในโจทย์ หัวข้อ 9.1 ทุกกรณี:
    * เริ่มจาก A,B,C แล้วเพิ่ม D -> ต้องมีคนย้าย 2 คน (เฉพาะคนที่ย้ายเข้า D)
    * เริ่มจาก A,B,C แล้วลบ B -> ต้องมีคนย้าย 3 คน (เฉพาะคนที่เคยอยู่ B)
    * room_no ของทุกคนที่ย้ายต้องเท่าเดิม เปลี่ยนแค่ node_id
- ทดสอบปฏิเสธ: เพิ่มอาคารซ้ำ, ลบอาคารที่ไม่มี, ลบอาคารสุดท้าย
- ทดสอบว่าจำนวนแขกรวมในระบบไม่เพิ่มไม่ลดหลังย้าย (invariant check)
"""

from dataclasses import dataclass, field


@dataclass
class MigrationRecord:
    c: int
    s: int
    old_node_id: str | None
    new_node_id: str
    room_no: int


@dataclass
class MigrationReport:
    accepted: bool
    reason: str  # เหตุผล ถ้า accepted=False, หรือคำอธิบายสั้น ๆ ถ้า accepted=True
    moved_count: int
    move_rate: float | None  # None ถ้า K == 0 (ไม่คำนวณอัตรา)
    moves: list[MigrationRecord] = field(default_factory=list)


def add_building(ring, registry, node_id: str) -> MigrationReport:
    """
    ring: instance ของ hashring.HashRing (คนที่ 1)
    registry: instance ของ guest.GuestRegistry (คนที่ 2)
    node_id: รหัสอาคารใหม่ที่จะเพิ่ม
    """
    # TODO(คนที่ 3): ทำตามขั้นตอน 1) ใน docstring ด้านบน
    raise NotImplementedError


def remove_building(ring, registry, node_id: str) -> MigrationReport:
    """เหมือน add_building แต่เป็นการลบอาคาร ดูขั้นตอน 2) ใน docstring ด้านบน"""
    # TODO(คนที่ 3): ทำตามขั้นตอน 2) ใน docstring ด้านบน
    raise NotImplementedError
