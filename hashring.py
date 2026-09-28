"""
hashring.py
งานของ: คนที่ 1 -- วงแหวนและการเลือกอาคาร (Consistent Hashing Ring)

หน้าที่ที่ต้องทำ (ดูรายละเอียดกติกาในโจทย์ หัวข้อ 4.3 และ 4.4):
1. คลาส HashRing เก็บ "จุด" (virtual node) ของแต่ละอาคารบนวงแหวน 0 .. 2**64 - 1
2. แฮชต้องคงที่ข้ามการรันโปรแกรม -> ใช้ hashlib.sha256 เท่านั้น ห้ามใช้ hash() ของ Python
3. ข้อความที่นำไปแฮชต้องแยกรูปแบบชัดเจน:
     - แขก:   f"guest:{c}:{s}"
     - จุดอาคาร: f"node:{node_id}:{j}"   โดย j = 0..V-1
4. เก็บจุดแบบเรียงลำดับ (แนะนำ: list ของ tuple (position, node_id, j) + ใช้ bisect
   ตอนแทรก/ค้นหา เพื่อให้ค้นหาได้ O(log M))
5. หา "เจ้าของ" ตำแหน่งแขก = จุดแรกที่ position >= ตำแหน่งแขก
   ถ้าไม่มี (ตำแหน่งแขกมากกว่าทุกจุด) ให้วนกลับไปจุดแรกของวงแหวน (index 0)
6. ถ้าตำแหน่งชนกัน (position เท่ากันหลายจุด) ให้เรียงด้วยคีย์ (position, node_id, j)
   แล้วใช้จุดแรกตามลำดับนี้เป็นเจ้าของ
7. add_node(node_id) ต้องปฏิเสธถ้า node_id มีอยู่แล้ว (ห้ามใส่ virtual node ซ้ำ)
8. remove_node(node_id) ต้องปฏิเสธถ้า node_id ไม่มีอยู่จริง
   และห้ามลบอาคารสุดท้าย (ต้องมี N >= 1 อาคารเสมอ) -> คืนค่า/เหตุผลให้ hotel_system.py
   ไปแจ้งผู้ใช้ต่อ (อย่า raise exception ที่ทำให้โปรแกรมหยุด)

สิ่งที่ 'ห้าม' ทำ (ตามโจทย์):
- ห้ามใช้ไลบรารี consistent hashing สำเร็จรูป
- ห้ามใช้ hash() ของ Python เป็นแฮชหลัก
- ห้ามเปลี่ยนตำแหน่งของจุดที่ยังอยู่ตอนเพิ่ม/ลบอาคารอื่น
- ห้ามเปลี่ยนค่า V ระหว่างรอบเดียวกัน

ทดสอบที่ต้องเขียน (ใน tests/test_hashring.py):
- ใช้ตัวอย่างวงแหวนเล็กในโจทย์ หัวข้อ 9.1 (วงแหวนขนาด 100, V=1,
  A ที่ 20, B ที่ 50, C ที่ 80) มากำหนดตำแหน่งเอง (ไม่ต้องพึ่ง SHA-256 จริง)
  เพื่อตรวจตรรกะ get_owner() ให้ตรงตามตารางในโจทย์
- ทดสอบกรณีวนกลับต้นวงแหวน (ตำแหน่งแขก 90 -> ต้องได้อาคาร A)
- ทดสอบกรณีจุดชนกัน
"""

import hashlib
from bisect import bisect_left, insort

RING_SIZE = 2 ** 64


def hash_to_position(key: str) -> int:
    """
    แปลงข้อความ (string) เป็นตำแหน่งบนวงแหวน 0 .. 2**64 - 1
    ใช้ SHA-256 แล้วตัดมา 64 บิตแรก (8 ไบต์แรก) ตามที่กติกากำหนด
    ต้องระบุวิธีการเข้ารหัสข้อความ (encoding) ในรายงานด้วย (ใช้ utf-8)

    ตัวอย่างการ implement (ปรับ/อธิบายในรายงานได้ตามที่กลุ่มออกแบบ):
        h = hashlib.sha256(key.encode("utf-8")).digest()
        return int.from_bytes(h[:8], byteorder="big")
    """
    # TODO(คนที่ 1): implement ตามที่ระบุไว้ใน docstring ด้านบน
    raise NotImplementedError


class HashRing:
    """
    วงแหวนสำหรับ Consistent Hashing

    self.points: list ของ tuple (position, node_id, j) เรียงตาม (position, node_id, j)
                 ใช้เก็บ virtual node ทุกจุดของทุกอาคาร
    self.nodes:  set ของ node_id ที่มีอยู่ในระบบ ใช้เช็คซ้ำ/มีอยู่จริงแบบเร็ว O(1)
    """

    def __init__(self, num_virtual_nodes_per_building: int):
        self.v = num_virtual_nodes_per_building
        self.points: list[tuple[int, str, int]] = []  # เรียงลำดับเสมอ
        self.nodes: set[str] = set()

    def add_node(self, node_id: str) -> bool:
        """
        เพิ่มอาคาร node_id พร้อม virtual node ทั้ง V จุด
        คืนค่า True ถ้าเพิ่มสำเร็จ, False ถ้า node_id มีอยู่แล้ว (ปฏิเสธการเพิ่ม)
        ต้องแทรกจุดใหม่โดยรักษาลำดับของ self.points ไว้เสมอ (ใช้ insort หรือ bisect_left เอง)
        """
        # TODO(คนที่ 1)
        raise NotImplementedError

    def remove_node(self, node_id: str) -> bool:
        """
        ลบอาคาร node_id พร้อม virtual node ทั้งหมดของอาคารนั้น
        คืนค่า True ถ้าลบสำเร็จ
        คืนค่า False ถ้า node_id ไม่มีอยู่จริง หรือถ้าลบแล้วจะไม่เหลืออาคารเลย (N >= 1)
        ห้ามเปลี่ยนตำแหน่งจุดของอาคารอื่นที่เหลืออยู่
        """
        # TODO(คนที่ 1)
        raise NotImplementedError

    def get_owner(self, position: int) -> str | None:
        """
        หา node_id ที่เป็นเจ้าของตำแหน่ง position
        กติกา: จุดแรกที่ position(จุด) >= position(แขก) ถ้าไม่มีให้วนกลับจุดแรกของวงแหวน (index 0)
        คืนค่า None ถ้าวงแหวนว่าง (ไม่ควรเกิดขึ้นถ้ารักษา N >= 1 ไว้เสมอ)
        แนะนำใช้ bisect_left บน list ของ position ล้วน ๆ (แยกเก็บหรือ derive ทุกครั้งก็ได้
        แต่ให้คำนึงถึง Big-O ตามที่จะวิเคราะห์ในรายงาน)
        """
        # TODO(คนที่ 1)
        raise NotImplementedError

    def get_owner_of_guest(self, c: int, s: int) -> str | None:
        """
        คำนวณตำแหน่งของแขกจาก (c, s) ด้วย hash_to_position("guest:c:s")
        แล้วเรียก get_owner() ต่อ
        """
        # TODO(คนที่ 1)
        raise NotImplementedError

    def node_count(self) -> int:
        return len(self.nodes)

    def point_count(self) -> int:
        """จำนวนจุดทั้งหมดบนวงแหวน = M = N * V"""
        return len(self.points)
