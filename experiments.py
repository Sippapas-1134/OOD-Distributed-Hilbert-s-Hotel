"""
experiments.py
งานของ: คนที่ 4 -- การทดลองและกราฟ (เปรียบเทียบ Consistent Hashing กับ hash mod N)

ไฟล์นี้ "ไม่ควร" แก้ hashring.py / guest.py / rebalance.py โดยตรง
แต่เรียกใช้ hotel_system.HotelSystem (ของคนที่ 5) เป็นตัวแทน Consistent Hashing
และ implement ModHashSystem แยกต่างหากในไฟล์นี้ (หรือไฟล์ mod_hash.py ใหม่) สำหรับ hash mod N

หน้าที่ที่ต้องทำ:

1. ModHashSystem: ระบบเทียบเคียงด้วยวิธี hash mod N
   - เก็บรายการรหัสอาคารตามลำดับที่เพิ่ม (list ธรรมดา ไม่ใช่วงแหวน)
   - เลือกอาคารด้วย index = H(guest) mod N  (ใช้ hash_to_position เดียวกับ hashring.py
     เพื่อให้ยุติธรรม ไม่ใช้ hash() ของ Python)
   - เพิ่มอาคาร: ต่อท้าย list
   - ลบอาคาร: เอารหัสนั้นออก โดยรักษาลำดับของอาคารที่เหลือ (list.remove หรือ filter)
   - ต้องคำนวณแขกที่ย้ายด้วย "รหัสอาคารจริง" ไม่ใช่เทียบแค่ index
     (เพราะ index ของอาคารเดิมจะเลื่อนเมื่อลบอาคารตัวกลาง ๆ ออกไป)

2. run_experiment_A(...): ทดสอบขนาดข้อมูล K = 1,000 / 10,000 / 100,000 (N=10, V=32 คงที่)
   วัด: เวลาจัดแขกเริ่มต้น, เวลาค้นหา (เฉลี่ยจาก 1,000 ครั้ง), เวลาสร้างรายการห้อง (เรียงลำดับ),
   หน่วยความจำ (tracemalloc)

3. run_experiment_B(...): ทดสอบจำนวนอาคาร N = 5 / 10 / 20 (K=10,000, V=32 คงที่)
   เพิ่ม 1 อาคาร และลบ 1 อาคาร แล้ววัด: จำนวนย้าย, อัตราย้าย, เวลา
   ทำทั้งด้วย Consistent Hashing และ hash mod N ด้วยชุดแขก/อาคาร/แฮชเดียวกัน

4. run_experiment_C(...): ทดสอบจำนวน virtual node V = 1 / 8 / 32 (N=10, K=10,000 คงที่)
   วัด: จำนวนแขกต่ออาคาร, CV (ความสมดุล), หน่วยความจำ, จำนวนย้าย

5. กติกาการวัดที่ต้องทำตาม (โจทย์หัวข้อ 7.2):
   - ใช้ time.perf_counter() แยกเวลาแต่ละขั้นตอน (สร้างวงแหวน / จัดแขก / ค้นหา / เรียงลำดับ /
     เพิ่มลบอาคาร) ไม่รวมเวลารับ input หรือแสดงผล/เขียนไฟล์
   - วัดการค้นหาเป็นชุด 1,000 ครั้ง แล้วหารเฉลี่ยต่อครั้ง
   - ทำ 3 รอบ เปลี่ยน salt (เช่น 0, 1, 2) ต่อท้ายข้อความก่อนแฮช แล้วรายงานค่ามัธยฐานของ 3 รอบ
     ใช้ salt เดียวกันกับทั้งสองวิธีในรอบเดียวกัน (เพื่อเทียบกันแฟร์)
   - ใช้ tracemalloc วัด current/peak เป็น MiB แยกรอบวัดหน่วยความจำออกจากรอบจับเวลา
   - CV = ส่วนเบี่ยงเบนมาตรฐาน / ค่าเฉลี่ย ถ้า K==0 ให้แสดง 0 และไม่คำนวณ

6. ฟังก์ชันสร้างกราฟ (แนะนำใช้ matplotlib):
   - plot_time_vs_k(results) -> กราฟ (ก) เวลาเทียบ K
   - plot_migration_rate_vs_n(results) -> กราฟ (ข) อัตราการย้ายเทียบ N ของทั้งสองวิธี
   - plot_v_effect(results) -> กราฟ (ค) ผลของ V ต่อ CV และหน่วยความจำ
   ทุกกราฟต้องมีชื่อแกน หน่วย และพารามิเตอร์กำกับ พร้อมแสดงความแปรปรวน 3 รอบ
   (เช่น error bar จาก min-max หรือ mean ± range)

7. export_experiment_csv(path, results): บันทึกผลการทดลองทุกค่าที่วัดได้ พร้อม
   พารามิเตอร์ (K, N, V, salt, รอบที่) ของแต่ละแถว เพื่อให้คนอื่นตรวจสอบซ้ำได้

หมายเหตุ: ควรเริ่มเขียนฟังก์ชัน ModHashSystem, การวัดเวลา/หน่วยความจำ และโครงกราฟไปพลางก่อน
ระหว่างรอคนที่ 1-3 ทำ HashRing/GuestRegistry/rebalance ให้เสร็จ เพราะ logic การวัดผล
ไม่ได้ขึ้นกับ implementation ภายในของทั้งสามไฟล์นั้นโดยตรง (เรียกผ่าน interface ของ
hotel_system.HotelSystem เท่านั้น)

ทดสอบ/ตรวจสอบที่ควรทำ:
- ModHashSystem กับ HotelSystem ต้องใช้รหัสแขกและรหัสอาคารชุดเดียวกันในการเทียบแต่ละคู่ทดลอง
- ตรวจว่าเปลี่ยน salt แล้วอัตราการย้ายเปลี่ยนไปตามที่คาด (ไม่ใช่ค่าคงที่ทุกรอบ)
"""

import time
import tracemalloc
import statistics

from hashring import hash_to_position


class ModHashSystem:
    """ระบบเทียบเคียงด้วยวิธี hash mod N (ดูรายละเอียดในหัวข้อ 7.1 ของโจทย์)"""

    def __init__(self, initial_node_ids: list[str], salt: str = ""):
        self.node_ids: list[str] = list(initial_node_ids)
        self.salt = salt
        # เก็บ mapping (c,s) -> node_id ปัจจุบัน เพื่อคำนวณจำนวนคนย้ายด้วยรหัสอาคารจริง
        self.guest_to_node: dict[tuple[int, int], str] = {}

    def _hash_guest(self, c: int, s: int) -> int:
        key = f"guest:{c}:{s}:{self.salt}"
        return hash_to_position(key)

    def get_owner_of_guest(self, c: int, s: int) -> str:
        # TODO(คนที่ 4): index = self._hash_guest(c, s) % len(self.node_ids)
        raise NotImplementedError

    def add_building(self, node_id: str):
        # TODO(คนที่ 4): ต่อท้าย list แล้วคำนวณใหม่ให้ทุกคน (K คน) เทียบ node_id เดิม/ใหม่
        # คืนรูปแบบผลลัพธ์เดียวกับ rebalance.MigrationReport เพื่อให้ export/plot ใช้ร่วมกันได้
        raise NotImplementedError

    def remove_building(self, node_id: str):
        # TODO(คนที่ 4): เอาออกจาก list โดยรักษาลำดับที่เหลือ แล้วคำนวณใหม่ให้ทุกคน
        raise NotImplementedError


def timed(fn, *args, **kwargs):
    """helper: จับเวลาการทำงานของฟังก์ชันด้วย perf_counter คืน (ผลลัพธ์, วินาที)"""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed


def measure_memory(fn, *args, **kwargs):
    """helper: วัดหน่วยความจำด้วย tracemalloc คืน (ผลลัพธ์, current_mib, peak_mib)"""
    tracemalloc.start()
    result = fn(*args, **kwargs)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    mib = 1024 * 1024
    return result, current / mib, peak / mib


def run_experiment_A(k_values, n=10, v=32, salts=(0, 1, 2)):
    """ทดลอง A: ผลของขนาดข้อมูล K ต่อเวลาและหน่วยความจำ"""
    # TODO(คนที่ 4)
    raise NotImplementedError


def run_experiment_B(n_values, k=10_000, v=32, salts=(0, 1, 2)):
    """ทดลอง B: ผลของจำนวนอาคาร N ต่อจำนวน/อัตราการย้าย เทียบสองวิธี"""
    # TODO(คนที่ 4)
    raise NotImplementedError


def run_experiment_C(v_values, n=10, k=10_000, salts=(0, 1, 2)):
    """ทดลอง C: ผลของจำนวน virtual node V ต่อความสมดุลโหลดและหน่วยความจำ"""
    # TODO(คนที่ 4)
    raise NotImplementedError


def plot_time_vs_k(results, out_path="time_vs_k.png"):
    # TODO(คนที่ 4): ใช้ matplotlib วาดกราฟ (ก) พร้อมหน่วยและพารามิเตอร์
    raise NotImplementedError


def plot_migration_rate_vs_n(results, out_path="migration_rate_vs_n.png"):
    # TODO(คนที่ 4): กราฟ (ข)
    raise NotImplementedError


def plot_v_effect(results, out_path="v_effect.png"):
    # TODO(คนที่ 4): กราฟ (ค)
    raise NotImplementedError


def export_experiment_csv(path: str, results) -> None:
    # TODO(คนที่ 4): เขียน CSV พร้อมพารามิเตอร์ K, N, V, salt, รอบที่ ของทุกแถว
    raise NotImplementedError
