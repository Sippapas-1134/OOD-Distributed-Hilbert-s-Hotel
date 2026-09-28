"""
hotel_system.py
งานของ: คนที่ 5 -- ส่วนติดต่อผู้ใช้และไฟล์ (เมนู, I/O, CSV)

ไฟล์นี้คือ "ตัวเชื่อม" (facade) ที่รวมทุกส่วนเข้าด้วยกัน:
    hashring.py (คนที่ 1) + guest.py (คนที่ 2) + rebalance.py (คนที่ 3)
แล้วห่อเป็นคลาส HotelSystem ให้เมนูข้อความ (text menu) เรียกใช้ได้ง่าย ๆ

หน้าที่ที่ต้องทำ:

1. คลาส HotelSystem
   - __init__(self, initial_node_ids: list[str], v: int):
       สร้าง HashRing(v) แล้ว add_node ทุกอาคารเริ่มต้น
       สร้าง GuestRegistry() เปล่า
   - init_guests(self, channels: dict[int, int]):
       channels คือ {c: จำนวนแขกในช่องทางนั้น} เริ่ม s ที่ 1 เสมอ
       เรียก registry.add_guests_batch (หรือ add_guest วนลูป) โดยใช้
       ring.get_owner_of_guest เป็น node_id_lookup_fn

2. เมธอดที่ต้องมี (ตรงกับฟังก์ชันบังคับในโจทย์ หัวข้อ 5):
   - add_guest(c, s) / add_guests_batch(c, s_start, count)
   - remove_guest(c, s)
   - add_building(node_id) / remove_building(node_id)  (เรียก rebalance.py)
   - find_by_guest(c, s) / find_by_address(node_id, room_no)
   - list_occupied_rooms() -> เรียง node_id น้อย->มาก แล้ว room_no น้อย->มาก ภายในแต่ละอาคาร
   - load_balance_report() -> คืน dict: จำนวนแขกทุกอาคาร (รวมอาคาร 0 คน), max, min, mean, std, cv
        ถ้า K == 0 ให้ค่าสถิติเป็น 0 ทั้งหมด และระบุว่าไม่คำนวณ CV
   - export_guests_csv(path): คอลัมน์ channel_id, sequence_id, node_id, room_no (UTF-8)
   - export_migrations_csv(path, migration_report): คอลัมน์ c, s, old_node_id, new_node_id, room_no

3. เมนูข้อความ (ฟังก์ชัน main_menu() หรือ run_cli() ในไฟล์นี้ หรือแยกเป็น main.py ก็ได้
   -- คุยกับกลุ่มว่าจะให้ entry point อยู่ไฟล์ไหน) ต้องมีอย่างน้อย:
   [1] เริ่มระบบใหม่ (กำหนด N, V, ช่องทาง+จำนวนแขก)
   [2] เพิ่มแขก (เดี่ยว/กลุ่ม)
   [3] ลบแขก
   [4] เพิ่มอาคาร
   [5] ลบอาคาร
   [6] ค้นหา (รหัสแขก -> ห้อง / ห้อง -> รหัสแขก)
   [7] แสดงรายการห้อง (บอกจำนวนทั้งหมด แสดงผลบนจอบางส่วนได้)
   [8] แสดงรายงานความสมดุลโหลด
   [9] Export CSV
   [0] ออกจากโปรแกรม
   ทุกเมนูต้อง "ปฏิเสธอย่างสุภาพ" ถ้า input ผิดกติกา ห้ามโปรแกรม crash (หัวข้อ 4.5)

4. README.md (ไฟล์แยก) ต้องระบุ: รุ่น Python ที่ใช้, วิธีรันโปรแกรม (python main.py),
   วิธีรันเทส (python -m pytest tests/ หรือ python -m unittest)

หมายเหตุสำคัญ: ไฟล์นี้ "ไม่ควร" มี logic การแฮชหรือการคำนวณห้องเอง
ให้เรียกใช้จาก hashring.py / guest.py / rebalance.py เท่านั้น เพื่อแยกตรรกะหลัก
ออกจากส่วนติดต่อผู้ใช้ตามที่โจทย์กำหนด (หัวข้อ 6)

ทดสอบที่ต้องเขียน (tests/test_hotel_system.py):
- รวมชุดทดสอบ end-to-end: เริ่มระบบ -> เพิ่มแขก -> เพิ่มอาคาร -> ตรวจว่าที่อยู่ห้องแขกเดิมไม่เปลี่ยน
- ทดสอบกรณีขอบทั้งหมดตามหัวข้อ 4.5 ผ่าน HotelSystem โดยตรง (ไม่ผ่านเมนู)
- ทดสอบว่าจำนวนแถวใน CSV ตรงกับจำนวนแขกในระบบ
"""

import csv
import statistics

from hashring import HashRing
from guest import GuestRegistry
import rebalance


class HotelSystem:
    def __init__(self, initial_node_ids: list[str], v: int):
        self.ring = HashRing(v)
        for node_id in initial_node_ids:
            ok = self.ring.add_node(node_id)
            if not ok:
                # อาคารเริ่มต้นซ้ำกัน -- ควรแจ้งเตือนตอนสร้างระบบ
                raise ValueError(f"รหัสอาคารซ้ำในชุดเริ่มต้น: {node_id}")
        self.registry = GuestRegistry()

    # ---------- ส่วนแขก ----------

    def add_guest(self, c: int, s: int) -> tuple[bool, str]:
        """เพิ่มแขกคนเดียว คำนวณอาคารจากวงแหวนปัจจุบัน"""
        # TODO(คนที่ 5): เรียก self.ring.get_owner_of_guest(c, s) แล้วส่งต่อ registry.add_guest
        raise NotImplementedError

    def add_guests_batch(self, c: int, s_start: int, count: int) -> tuple[bool, str, list]:
        # TODO(คนที่ 5): เรียก registry.add_guests_batch โดยส่ง lookup_fn ที่ใช้ ring
        raise NotImplementedError

    def remove_guest(self, c: int, s: int) -> tuple[bool, str]:
        # TODO(คนที่ 5)
        raise NotImplementedError

    def find_by_guest(self, c: int, s: int):
        # TODO(คนที่ 5)
        raise NotImplementedError

    def find_by_address(self, node_id: str, room_no: int):
        # TODO(คนที่ 5)
        raise NotImplementedError

    # ---------- ส่วนอาคาร (เรียก rebalance.py ของคนที่ 3) ----------

    def add_building(self, node_id: str):
        # TODO(คนที่ 5): return rebalance.add_building(self.ring, self.registry, node_id)
        raise NotImplementedError

    def remove_building(self, node_id: str):
        # TODO(คนที่ 5): return rebalance.remove_building(self.ring, self.registry, node_id)
        raise NotImplementedError

    # ---------- รายงาน ----------

    def list_occupied_rooms(self) -> list[tuple[str, int, int, int]]:
        """คืน list ของ (node_id, room_no, c, s) เรียง node_id แล้วเรียง room_no"""
        # TODO(คนที่ 5): วนทุก node_id ใน self.ring.nodes (เรียงลำดับ) แล้วเรียก
        # self.registry.list_guests_in_building(node_id) ต่อ
        raise NotImplementedError

    def load_balance_report(self) -> dict:
        """
        คืน dict เช่น:
        {
          "per_building": {node_id: จำนวนแขก, ...},   # รวมอาคารที่มี 0 คนด้วย
          "max": ..., "min": ..., "mean": ..., "std": ...,
          "cv": ... หรือ None ถ้า K == 0
        }
        """
        # TODO(คนที่ 5)
        raise NotImplementedError

    # ---------- Export CSV ----------

    def export_guests_csv(self, path: str) -> None:
        """คอลัมน์: channel_id, sequence_id, node_id, room_no (UTF-8)"""
        # TODO(คนที่ 5)
        raise NotImplementedError

    def export_migrations_csv(self, path: str, migration_report) -> None:
        """คอลัมน์: c, s, old_node_id, new_node_id, room_no"""
        # TODO(คนที่ 5)
        raise NotImplementedError


def run_cli():
    """
    เมนูข้อความหลัก -- ทำตามรายการ 8 ข้อใน docstring ด้านบนของไฟล์นี้
    ตัวอย่างโครงเมนู (ให้แก้ไข/เติมเต็มเอง):
    """
    print("=== ระบบโรงแรมอนันต์แบบกระจาย (Consistent Hashing) ===")
    system = None
    while True:
        print(
            "\n[1] เริ่มระบบใหม่  [2] เพิ่มแขก  [3] ลบแขก  [4] เพิ่มอาคาร  "
            "[5] ลบอาคาร  [6] ค้นหา  [7] แสดงห้อง  [8] รายงานโหลด  [9] Export CSV  [0] ออก"
        )
        choice = input("เลือกเมนู: ").strip()
        if choice == "0":
            print("ออกจากโปรแกรม")
            break
        # TODO(คนที่ 5): เติม logic ของแต่ละเมนู เรียกใช้ HotelSystem ด้านบน
        # ทุกกรณีต้อง try/except หรือตรวจ input ก่อน ไม่ปล่อยให้โปรแกรม crash
        print("(ยังไม่ implement เมนูนี้)")


if __name__ == "__main__":
    run_cli()
