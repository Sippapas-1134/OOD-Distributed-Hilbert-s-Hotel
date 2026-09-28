"""
guest.py
งานของ: คนที่ 2 -- ข้อมูลแขกและเลขห้อง (Guest / Room / ดัชนีค้นหา)

หน้าที่ที่ต้องทำ (ดูกติกาในโจทย์ หัวข้อ 4.1, 4.2):
1. ฟังก์ชัน compute_room_no(c, s) คำนวณเลขห้องจาก Cantor pairing function
   ตามสูตรที่โจทย์กำหนด (a = c-1, b = s-1):
     room_no = ((a+b)*(a+b+1))//2 + b + 1
   ต้องคำนวณด้วยจำนวนเต็มล้วน ห้ามแปลงเป็นทศนิยม (ใช้ // เท่านั้น)
   ตรวจกับตารางตัวอย่างในโจทย์:
     (1,1)->1  (2,1)->2  (1,2)->3  (3,1)->4  (2,2)->5

2. คลาส GuestRegistry เก็บข้อมูลแขกทั้งหมดในระบบ และดัชนีค้นหาสองทาง:
     - self.by_guest_code : dict[(c, s)] -> {"node_id": ..., "room_no": ...}
     - self.by_address    : dict[(node_id, room_no)] -> (c, s)
   ต้องดูแลให้ทั้งสอง dict สอดคล้องกันเสมอ (เพิ่ม/ลบ/ย้าย ต้องอัปเดตทั้งคู่)

3. add_guest(c, s, node_id) : เพิ่มแขกคนเดียว
   - ปฏิเสธถ้า (c, s) มีอยู่แล้ว (return False พร้อมเหตุผล ไม่ throw exception)
   - คำนวณ room_no จาก compute_room_no แล้วบันทึกทั้งสอง dict

4. add_guests_batch(c, s_start, count, node_id_lookup_fn):
   - เพิ่มแขกเป็นกลุ่ม: รหัส c เดียวกัน ลำดับเริ่ม s_start ถึง s_start+count-1
   - count ต้องเป็นจำนวนเต็มไม่ติดลบ (0 = ไม่ทำอะไรเลย)
   - ถ้ามีรายการใดรายการหนึ่งในกลุ่มชนกับแขกที่มีอยู่แล้ว -> ปฏิเสธ "ทั้งกลุ่ม"
     (ห้ามเพิ่มบางส่วน) และคงข้อมูลเดิมไว้ทั้งหมด
   - node_id_lookup_fn: ฟังก์ชันที่ hotel_system.py ส่งเข้ามาเพื่อถามว่าคนนี้ควรอยู่อาคารไหน
     (เพราะการเลือกอาคารเป็นหน้าที่ของ HashRing ไม่ใช่ของไฟล์นี้)

5. remove_guest(c, s): ลบแขกออก (ลบข้อมูลการเข้าพัก ไม่ต้องสร้างห้องว่างแทน)
   - ถ้าไม่พบ ให้คืนค่า False พร้อมข้อความแจ้ง ไม่ throw exception
   - ถ้าเพิ่มรหัสเดิมกลับมาใหม่ทีหลัง ให้ถือเป็นแขกใหม่ (คำนวณจากวงแหวนปัจจุบัน
     ผ่าน add_guest ตามปกติ ไม่ต้องมี logic พิเศษในไฟล์นี้)

6. find_by_guest_code(c, s) -> คืน (node_id, room_no) หรือ None ถ้าไม่พบ
   find_by_address(node_id, room_no) -> คืน (c, s) หรือ None ถ้าไม่พบ

7. update_node_of_guest(c, s, new_node_id): ใช้ตอนแขกย้ายอาคาร (เรียกจาก hotel_system.py
   ตอนเพิ่ม/ลบอาคาร) -- room_no ต้องคงเดิม เปลี่ยนแค่ node_id
   ต้องอัปเดตทั้ง by_guest_code และ by_address (ลบ address เก่า ใส่ address ใหม่)

8. list_guests_in_building(node_id) -> list ของ (room_no, c, s) เรียงตาม room_no
   (ใช้ตอนคนที่ 5 ทำฟังก์ชันแสดงรายการห้อง)

ทดสอบที่ต้องเขียน (tests/test_guest.py):
- ตรวจเลขห้องตามตารางตัวอย่างในโจทย์
- ตรวจว่ารหัสแขกต่างกัน ไม่เคยได้ room_no ซ้ำกัน (สุ่มทดสอบจำนวนมาก)
- ปฏิเสธรหัสซ้ำ ทั้งแบบเดี่ยวและแบบกลุ่ม (batch ที่ซ้ำแค่ 1 รายการ ต้องถูกปฏิเสธทั้งกลุ่ม)
- ลบแขกที่ไม่มีอยู่ -> ไม่ throw exception, คืนค่า False
"""

from dataclasses import dataclass


def compute_room_no(c: int, s: int) -> int:
    """
    คำนวณเลขห้องจากรหัสแขก (c, s) ด้วย Cantor pairing function
    c, s เป็นจำนวนเต็มบวก (เริ่มที่ 1)
    """
    # TODO(คนที่ 2): a = c - 1, b = s - 1 แล้วคำนวณตามสูตรในโจทย์ ด้วยจำนวนเต็มล้วน
    raise NotImplementedError


@dataclass
class GuestRecord:
    c: int
    s: int
    node_id: str
    room_no: int


class GuestRegistry:
    def __init__(self):
        self.by_guest_code: dict[tuple[int, int], GuestRecord] = {}
        self.by_address: dict[tuple[str, int], tuple[int, int]] = {}

    def add_guest(self, c: int, s: int, node_id: str) -> tuple[bool, str]:
        """
        คืน (True, "") ถ้าสำเร็จ
        คืน (False, เหตุผล) ถ้าปฏิเสธ เช่น "(c,s) ซ้ำกับแขกที่มีอยู่แล้ว"
        """
        # TODO(คนที่ 2)
        raise NotImplementedError

    def add_guests_batch(
        self, c: int, s_start: int, count: int, node_id_lookup_fn
    ) -> tuple[bool, str, list[tuple[int, int]]]:
        """
        node_id_lookup_fn(c, s) -> node_id  (เรียกเพื่อถามว่าแขกคนนี้อยู่อาคารไหน)
        คืน (True, "", รายชื่อ (c,s) ที่เพิ่มสำเร็จ) หรือ (False, เหตุผล, [])
        ถ้า count == 0 ให้คืน (True, "ไม่มีการเปลี่ยนแปลง", [])
        ต้องตรวจสอบ "ทั้งกลุ่ม" ว่าไม่มีใครซ้ำ ก่อนจะเริ่มเพิ่มจริงแม้แต่คนเดียว
        """
        # TODO(คนที่ 2)
        raise NotImplementedError

    def remove_guest(self, c: int, s: int) -> tuple[bool, str]:
        # TODO(คนที่ 2)
        raise NotImplementedError

    def find_by_guest_code(self, c: int, s: int):
        """คืน (node_id, room_no) หรือ None"""
        # TODO(คนที่ 2)
        raise NotImplementedError

    def find_by_address(self, node_id: str, room_no: int):
        """คืน (c, s) หรือ None"""
        # TODO(คนที่ 2)
        raise NotImplementedError

    def update_node_of_guest(self, c: int, s: int, new_node_id: str) -> None:
        """ใช้ตอนย้ายอาคาร room_no คงเดิม เปลี่ยนแค่ node_id เรียกจากตอนเพิ่ม/ลบอาคาร"""
        # TODO(คนที่ 2)
        raise NotImplementedError

    def list_guests_in_building(self, node_id: str) -> list[tuple[int, int, int]]:
        """คืน list ของ (room_no, c, s) เรียงตาม room_no จากน้อยไปมาก"""
        # TODO(คนที่ 2)
        raise NotImplementedError

    def guest_count(self) -> int:
        return len(self.by_guest_code)

    def all_guest_codes(self):
        """คืน iterable ของ (c, s) ทั้งหมด -- ใช้โดยคนที่ 3 ตอนตรวจแขกทุกคน (แบบ ก)"""
        return list(self.by_guest_code.keys())
