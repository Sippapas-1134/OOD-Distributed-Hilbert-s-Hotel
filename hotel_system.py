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

    def get_node_id_fix(self, c, s):
        return self.ring.get_owner_of_guest(c, s)[1]

    # ---------- ส่วนแขก ----------

    def add_guest(self, c: int, s: int) -> tuple[bool, str]:
        """เพิ่มแขกคนเดียว คำนวณอาคารจากวงแหวนปัจจุบัน"""
        node_id = self.get_node_id_fix(c, s)
        # print(type(node_id), node_id)
        return self.registry.add_guest(c, s, node_id)


    def add_guests_batch(self, c: int, s_start: int, count: int) -> tuple[bool, str, list]:
        return self.registry.add_guests_batch(c, s_start, count, self.get_node_id_fix)

    def remove_guest(self, c: int, s: int) -> tuple[bool, str]:
        return self.registry.remove_guest(c, s)

    def find_by_guest(self, c: int, s: int) -> (tuple[str, int] | None):
        return self.registry.find_by_guest_code(c, s)

    def find_by_address(self, node_id: str, room_no: int):
        return self.registry.find_by_address(node_id, room_no)

    # ---------- ส่วนอาคาร (เรียก rebalance.py ของคนที่ 3) ----------

    def add_building(self, node_id: str):
        return rebalance.add_building(self.ring, self.registry, node_id)

    def remove_building(self, node_id: str):
        return rebalance.remove_building(self.ring, self.registry, node_id)

    # ---------- รายงาน ----------

    def list_occupied_rooms(self) -> list[tuple[str, int, int, int]]:
        """คืน list ของ (node_id, room_no, c, s) เรียง node_id แล้วเรียง room_no"""
        return_list = []
        for node_id in self.ring.nodes:
            for data in self.registry.list_guests_in_building(node_id):
                return_list.append((node_id, *data))
        return return_list

    def load_balance_report(self) -> tuple[bool, dict, str]:
        """
        คืน status bool + dict + message
        dict เช่น:
        {
          "per_building": {node_id: จำนวนแขก, ...},   # รวมอาคารที่มี 0 คนด้วย
          "max": ..., "min": ..., "mean": ..., "std": ...,
          "cv": ... หรือ None ถ้า K == 0
        }
        """
        data_dict = {
            "per_building": {},
            "max": 0,
            "min": 0,
            "mean": 0,
            "std": 0,
            "cv": None
        }
        for node_id in self.ring.nodes:
            data_dict["per_building"][node_id] = len(self.registry.list_guests_in_building(node_id))
        values = list(data_dict["per_building"].values())

        if sum(values) == 0:
            return False, data_dict, "ไม่มีแขกอยู่ในระบบตอนนี้ ไม่คำนวณสถิติของระบบ" # No guest
        
        data_dict["max"] = max(values)
        data_dict["min"] = min(values)
        data_dict["mean"] = statistics.mean(values)
        data_dict["std"] = statistics.pstdev(values)
        data_dict["cv"] = statistics.pvariance(values)
        return True, data_dict, ""

    # ---------- Export CSV ----------

    def export_guests_csv(self, path: str) -> None:
        """คอลัมน์: channel_id, sequence_id, node_id, room_no (UTF-8)"""
        header = ("channel_id", "sequence_id", "node_id", "room_no")
        data = [header]
        for room_data in self.list_occupied_rooms():
            swap_data = (room_data[2], room_data[3], room_data[0], room_data[1])
            data.append(swap_data)

        with open(path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(data)

    def export_migrations_csv(self, path: str, migration_report: rebalance.MigrationReport) -> None:
        """คอลัมน์: c, s, old_node_id, new_node_id, room_no"""
        header = ("c", "s", "old_node_id", "new_node_id", "room_no")
        data = [header]
        for record in migration_report.moves:
            data.append((record.c, record.s, record.old_node_id, record.new_node_id, record.room_no))

        with open(path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(data)


def is_num_more_than_one(num):
    return num.isdigit() and int(num) >= 1

def run_cli():
    """
    เมนูข้อความหลัก -- ทำตามรายการ 8 ข้อใน docstring ด้านบนของไฟล์นี้
    ตัวอย่างโครงเมนู (ให้แก้ไข/เติมเต็มเอง):
    """
    print("=== ระบบโรงแรมอนันต์แบบกระจาย (Consistent Hashing) ===")
    system = None
    migration_report = None
    while True:
        print(
            "\n[1] เริ่มระบบใหม่  [2] เพิ่มแขก  [3] ลบแขก  [4] เพิ่มอาคาร  "
            "[5] ลบอาคาร  [6] ค้นหา  [7] แสดงห้อง  [8] รายงานโหลด  [9] Export CSV  [0] ออก"
        )
        choice = input("เลือกเมนู: ").strip()
        if choice == "0":
            print("ออกจากโปรแกรม")
            break
        elif choice == "1":
            initial_node_ids = input("ใส่ ID ของอาคารเริ่มต้น (ใส่ได้หลายอาคารใช้ space ขั้นแต่ละ ID): ").strip().split(" ")
            v = input("ใส่จำนวน Virtual Node ต่ออาคาร (ค่า V): ").strip("")

            if not is_num_more_than_one(v):
                print("FAILED: ค่า V ต้องเป็นจำนวนเต็มที่ >= 1")
                continue

            try:
                system = HotelSystem(initial_node_ids, int(v))
            except ValueError as error_msg:
                print("FAILED:", error_msg)
                system = None
                continue
            else:
                print("สร้างระบบสำเร็จ")
        elif choice == "2":
            c = input("ใส่ค่า c ของแขก: ").strip()
            if not is_num_more_than_one(c):
                print("FAILED: ค่า c ของแขกต้องเป็นจำนวนเต็ม >= 1")
                continue
            
            s = input("ใส่ค่า s ของแขก(s เริ่มต้นหากเป็นแขกหลายคน): ").strip()
            if not is_num_more_than_one(s):
                print("FAILED: ค่า s ของแขกต้องเป็นจำนวนเต็ม >= 1")
                continue
            
            count = input("ใส่จำนวนแขกที่อยากใส่: ").strip()
            if not is_num_more_than_one(count):
                print("FAILED: ค่า count ของแขกต้องเป็นจำนวนเต็ม >= 1")
                continue

            c = int(c)
            s = int(s)
            count = int(count)
            status, msg = None, None
            if count > 1:
                status, msg, _ = system.add_guests_batch(c, s, count)
            else:
                status, msg = system.add_guest(c, s)

            if not status:
                print("FAILED:", msg)
                continue
            
            if count > 1:
                print(f"เพิ่มลูกค้ารหัส ({c}, {s}) ถึง ({c}, {s + count - 1}) แล้ว")
            else:
                print(f"เพิ่มลูกค้ารหัส ({c}, {s}) แล้ว")
        elif choice == "3":
            c, s = input("ใส่ค่า c และ s ของแขกที่อยากลบออก (ใช้ space ขั้นระหว่างสองค่า): ").strip().split(" ")

            if not is_num_more_than_one(c):
                print("FAILED: ค่า c ของแขกต้องเป็นจำนวนเต็ม >= 1")
                continue
            elif not is_num_more_than_one(s):
                print("FAILED: ค่า s ของแขกต้องเป็นจำนวนเต็ม >= 1")
                continue

            c = int(c)
            s = int(s)
            status, msg = system.remove_guest(c, s)
            if not status:
                print("FAILED:", msg)
                continue
            print(f"ลบลูกค้ารหัส ({c}, {s}) แล้ว")
        elif choice == "4":
            node_id = input("ใส่ ID ของอาคารที่อยากเพิ่ม: ").strip()
            report = system.add_building(node_id)
            if not report.accepted:
                print("FAILED:", report.reason)
                continue
            migration_report = report
            print(f"เพิ่มอาคาร ID {node_id} แล้ว")
        elif choice == "5":
            node_id = input("ใส่ ID ของอาคารที่อยากลบ: ").strip()
            report = system.remove_building(node_id)
            if not report.accepted:
                print("FAILED:", report.reason)
                continue
            migration_report = report
            print(f"ลบอาคาร ID {node_id} แล้ว")
        elif choice == "6":
            mode = input("[1] ค้าหาแขกโดยใช้ ID (c, s) ของแขก  [2] ค้นหาแขกโดยใช้เลขห้องของแขก: ").strip()
            if mode == "1":
                c, s = input("ใส่ค่า c และ s ของแขกที่อยากค้นหา (ใช้ space ขั้นระหว่างสองค่า): ").strip().split(" ")

                if not is_num_more_than_one(c):
                    print("FAILED: ค่า c ของแขกต้องเป็นจำนวนเต็ม >= 1")
                    continue
                elif not is_num_more_than_one(s):
                    print("FAILED: ค่า s ของแขกต้องเป็นจำนวนเต็ม >= 1")
                    continue

                c = int(c)
                s = int(s)
                data = system.find_by_guest(c, s)
                if data is None:
                    print(f"FAILED: ไม่พบแขก ID ({c}, {s})")
                    continue
                print(f"แขก ID ({c}, {s}) อยู่ที่อาคา {data[0]} ห้อง {data[-1]}")
            elif mode == "2":
                node_id, room_no = input("ใส่ค่า ID อาคารและเลขห้องของแขกที่อยากค้นหา (ใช้ space ขั้นระหว่างสองค่า): ").strip().split(" ")
            
                if not is_num_more_than_one(room_no):
                    print("FAILED: เลขห้องต้องเป็นจำนวนเต็ม >= 1")
                    continue

                room_no = int(room_no)
                data = system.find_by_address(node_id, room_no)
                if data is None:
                    print(f"FAILED: ไม่พบแขกที่อาคาร ID {node_id} ห้องเลข {room_no}")
                    continue
                print(f"แขกที่อาคาร {node_id} ห้องเลข {room_no} มี ID คือ ({data[0], data[-1]})")
            else:
                print("FAILED: ไม่มี Mode ในการหาแขกนี้อยู่")
        elif choice == "7":
            rooms = system.list_occupied_rooms()
            seen_nodes = []
            for node_id, room_no, c, s in rooms:
                if node_id not in seen_nodes:
                    print("อาคา:", node_id)
                    seen_nodes.append(node_id)
                print(f"    ห้อง {room_no}: ลูกค้า ID ({c}, {s})")
        elif choice == "8":
            status, data, msg = system.load_balance_report()

            if not status:
                print(msg)
                continue

            print("ต่ออาคาร:")
            for node_id, room_count in data["per_building"].items():
                print(f"    อาคาร {node_id} มีห้อง {room_count} ห้อง")
            print(f"อาคารที่มีห้องมากที่สุดมีทั้งหมด {data["max"]} ห้อง")
            print(f"อาคารที่มีห้องน้อยที่สุดมีทั้งหมด {data["min"]} ห้อง")
            print(f"อาคารทุกอาคารมีห้องเฉลี่ย {data["mean"]} ห้อง")
            print(f"ส่วนเบี่ยงเบนมาตรฐาน: {data["std"]}")
            print(f"cv: {data["cv"]}")
        elif choice == "9":
            report_type = input("[1] Export ข้อมูลแขก [2] Export ข้อมูลการย้ายตึก: ").strip()
            if report_type != "1" and report_type != "2":
                print("FAILED: ไม่มี Report ประเภทนี้")

            path = input("ใส่ Path ที่จะเก็บ CSV (Relative to main.py): ").strip()
            if path[-4:] != ".csv":
                path += ".csv"

            if report_type == "1":
                system.export_guests_csv(path)
            elif report_type == "2":
                if migration_report is None:
                    print("FAILED: ไมมี Migration Report")
                    continue
                else:
                    system.export_migrations_csv(path, migration_report)
            print("เขียนไฟล์ CSV แล้ว")
        else:
            print("FAILED: ไม่มี Option นี้")


if __name__ == "__main__":
    run_cli()
