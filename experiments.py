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

# หมายเหตุ: rebalance.py / hotel_system.py ยังไม่เสร็จ จึงทำ ConsistentHashSystem (ตัวแทนบาง ๆ) ในไฟล์นี้
# จาก HashRing + GuestRegistry และ SaltedHashRing (HashRing ไม่มี salt และห้ามแก้ hashring.py)
# เวลาหน่วยวินาที (_s)  หน่วยความจำหน่วย MiB (_mib) เป็นส่วนที่ Python ติดตามด้วย tracemalloc

import csv
import gc
import random
import statistics
import time
import tracemalloc
from bisect import insort

from hashring import HashRing, hash_to_position
from guest import GuestRegistry, compute_room_no
from rebalance import MigrationRecord, MigrationReport

SEARCH_BATCH = 1000   # วัดการค้นหาเป็นชุด 1,000 ครั้ง แล้วหารต่อครั้ง


# ---------- ข้อมูลทดลอง ----------

def make_node_ids(n: int) -> list[str]:
    return [f"B{i:02d}" for i in range(1, n + 1)]


def make_channels(k: int, n_channels: int = 10) -> dict[int, int]:
    """แบ่งแขก k คนให้ 10 ช่องทางใกล้เคียงกัน s เริ่มที่ 1"""
    base, extra = divmod(k, n_channels)
    return {c: base + (1 if c <= extra else 0) for c in range(1, n_channels + 1)}


def load_stats(loads: dict) -> dict:
    """max, min, mean, std, cv = std/mean  ถ้าไม่มีแขก ทุกค่า 0 และ cv=None"""
    counts = list(loads.values())
    if sum(counts) == 0:
        return {"max": 0, "min": 0, "mean": 0.0, "std": 0.0, "cv": None}
    mean = statistics.fmean(counts)
    std = statistics.pstdev(counts)
    return {"max": max(counts), "min": min(counts), "mean": mean, "std": std, "cv": std / mean}


def _report(accepted: bool, reason: str, moves: list, k: int) -> MigrationReport:
    return MigrationReport(accepted, reason, len(moves), None if k == 0 else len(moves) / k, moves)


def check_move_rule(report: MigrationReport, op: str, node_id: str) -> bool:
    """4.4: เพิ่มอาคาร -> ย้ายเข้าอาคารใหม่เท่านั้น / ลบอาคาร -> ย้ายออกจากอาคารที่ลบเท่านั้น"""
    if op == "add":
        return all(m.new_node_id == node_id for m in report.moves)
    return all(m.old_node_id == node_id for m in report.moves)


# ---------- ระบบที่ 1: hash mod N ----------

class ModHashSystem:
    """ระบบเทียบเคียงด้วยวิธี hash mod N (ดูรายละเอียดในหัวข้อ 7.1 ของโจทย์)"""

    def __init__(self, initial_node_ids: list[str], salt: str = ""):
        self.node_ids: list[str] = list(initial_node_ids)
        self.salt = str(salt)
        # เก็บ mapping (c,s) -> node_id ปัจจุบัน เพื่อคำนวณจำนวนคนย้ายด้วยรหัสอาคารจริง
        self.guest_to_node: dict[tuple[int, int], str] = {}
        self.last_timing = {"ring_s": 0.0, "find_s": 0.0, "update_s": 0.0}

    def _hash_guest(self, c: int, s: int) -> int:
        key = f"guest:{c}:{s}:{self.salt}"
        return hash_to_position(key)

    def get_owner_of_guest(self, c: int, s: int) -> str:
        return self.node_ids[self._hash_guest(c, s) % len(self.node_ids)]

    def init_guests(self, channels: dict[int, int]) -> None:
        for c, count in channels.items():
            for s in range(1, count + 1):
                self.guest_to_node[(c, s)] = self.get_owner_of_guest(c, s)

    def guest_count(self) -> int:
        return len(self.guest_to_node)

    def _change(self, change_list, node_id: str) -> MigrationReport:
        """เปลี่ยนรายการอาคารแล้วคำนวณใหม่ให้ทุกคน เทียบรหัสอาคารเดิม/ใหม่ (ไม่ใช่เทียบ index)"""
        t0 = time.perf_counter()
        change_list(node_id)
        t1 = time.perf_counter()
        moves = []
        for (c, s), old in self.guest_to_node.items():
            new = self.get_owner_of_guest(c, s)
            if new != old:
                moves.append(MigrationRecord(c, s, old, new, compute_room_no(c, s)))
        t2 = time.perf_counter()
        for m in moves:
            self.guest_to_node[(m.c, m.s)] = m.new_node_id
        t3 = time.perf_counter()
        self.last_timing = {"ring_s": t1 - t0, "find_s": t2 - t1, "update_s": t3 - t2}
        return _report(True, "สำเร็จ (hash mod N)", moves, self.guest_count())

    def add_building(self, node_id: str) -> MigrationReport:
        if node_id in self.node_ids:
            return _report(False, f"ปฏิเสธ: อาคาร {node_id} มีอยู่แล้ว", [], self.guest_count())
        return self._change(self.node_ids.append, node_id)

    def remove_building(self, node_id: str) -> MigrationReport:
        if node_id not in self.node_ids:
            return _report(False, f"ปฏิเสธ: ไม่มีอาคาร {node_id}", [], self.guest_count())
        if len(self.node_ids) == 1:
            return _report(False, "ปฏิเสธ: ห้ามลบอาคารสุดท้าย", [], self.guest_count())
        return self._change(self.node_ids.remove, node_id)  # รักษาลำดับที่เหลือ

    def building_loads(self) -> dict[str, int]:
        loads = {nid: 0 for nid in self.node_ids}
        for nid in self.guest_to_node.values():
            loads[nid] += 1
        return loads


# ---------- ระบบที่ 2: Consistent Hashing ----------

class SaltedHashRing(HashRing):
    """HashRing ที่เติม salt ต่อท้ายข้อความก่อนแฮช (ส่วนอื่นใช้ของ HashRing เดิม)"""

    def __init__(self, v: int, salt: str = ""):
        super().__init__(v)
        self.salt = str(salt)

    def add_node(self, node_id: str) -> bool:
        if node_id in self.nodes:
            return False
        self.nodes.add(node_id)
        for j in range(self.v):
            insort(self.points, (hash_to_position(f"node:{node_id}:{j}:{self.salt}"), node_id, j))
        return True

    def get_owner_of_guest(self, c: int, s: int):
        return self.get_owner(hash_to_position(f"guest:{c}:{s}:{self.salt}"))


class ConsistentHashSystem:
    """ตัวแทน Consistent Hashing สำหรับทดลอง (interface เหมือน ModHashSystem)"""

    def __init__(self, initial_node_ids: list[str], v: int, salt: str = ""):
        self.ring = SaltedHashRing(v, salt)
        for node_id in initial_node_ids:
            self.ring.add_node(node_id)
        self.registry = GuestRegistry()
        self.last_timing = {"ring_s": 0.0, "find_s": 0.0, "update_s": 0.0}

    def _node_of(self, c: int, s: int) -> str:
        return self.ring.get_owner_of_guest(c, s)[1]   # [1] = node_id

    def init_guests(self, channels: dict[int, int]) -> None:
        for c, count in channels.items():
            ok, reason, _ = self.registry.add_guests_batch(c, 1, count, self._node_of)
            if not ok:
                raise ValueError(reason)

    def guest_count(self) -> int:
        return self.registry.guest_count()

    def list_occupied_rooms(self) -> list[tuple[str, int, int, int]]:
        """(node_id, room_no, c, s) เรียง node_id แล้ว room_no"""
        return [(nid, room, c, s) for nid in sorted(self.ring.nodes)
                for room, c, s in self.registry.list_guests_in_building(nid)]

    def add_building(self, node_id: str) -> MigrationReport:
        k = self.guest_count()
        t0 = time.perf_counter()
        if not self.ring.add_node(node_id):
            return _report(False, f"ปฏิเสธ: อาคาร {node_id} มีอยู่แล้ว", [], k)
        t1 = time.perf_counter()
        moves = []            # แบบ ก: ตรวจแขกทุกคน
        for c, s in self.registry.all_guest_codes():
            rec = self.registry.by_guest_code[(c, s)]
            new = self._node_of(c, s)
            if new != rec.node_id:
                moves.append(MigrationRecord(c, s, rec.node_id, new, rec.room_no))
        t2 = time.perf_counter()
        for m in moves:
            self.registry.update_node_of_guest(m.c, m.s, m.new_node_id)
        t3 = time.perf_counter()
        self.last_timing = {"ring_s": t1 - t0, "find_s": t2 - t1, "update_s": t3 - t2}
        return _report(True, "สำเร็จ (Consistent Hashing)", moves, k)

    def remove_building(self, node_id: str) -> MigrationReport:
        k = self.guest_count()
        if node_id not in self.ring.nodes:
            return _report(False, f"ปฏิเสธ: ไม่มีอาคาร {node_id}", [], k)
        if self.ring.node_count() == 1:
            return _report(False, "ปฏิเสธ: ห้ามลบอาคารสุดท้าย", [], k)
        ta = time.perf_counter()
        victims = self.registry.list_guests_in_building(node_id)   # ต้องรู้ก่อนลบจุดออก
        tb = time.perf_counter()
        self.ring.remove_node(node_id)
        tc = time.perf_counter()
        moves = [MigrationRecord(c, s, node_id, self._node_of(c, s), room) for room, c, s in victims]
        td = time.perf_counter()
        for m in moves:
            self.registry.update_node_of_guest(m.c, m.s, m.new_node_id)
        te = time.perf_counter()
        self.last_timing = {"ring_s": tc - tb, "find_s": (tb - ta) + (td - tc), "update_s": te - td}
        return _report(True, "สำเร็จ (Consistent Hashing)", moves, k)

    def building_loads(self) -> dict[str, int]:
        loads = {nid: 0 for nid in self.ring.nodes}
        for rec in self.registry.by_guest_code.values():
            loads[rec.node_id] += 1
        return loads


# ---------- เครื่องมือวัดผล ----------

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


def _time_batch(fn, queries) -> float | None:
    """เวลาเฉลี่ยต่อครั้ง (วินาที) ของ fn(*q) ทั้งชุด"""
    if not queries:
        return None
    gc.collect()
    start = time.perf_counter()
    for q in queries:
        fn(*q)
    return (time.perf_counter() - start) / len(queries)


def _build_ch(n, v, salt, k) -> ConsistentHashSystem:
    system = ConsistentHashSystem(make_node_ids(n), v, salt)
    system.init_guests(make_channels(k))
    return system


def _build_mod(n, salt, k) -> ModHashSystem:
    system = ModHashSystem(make_node_ids(n), salt)
    system.init_guests(make_channels(k))
    return system


def _build_ring_only(n, v, salt) -> SaltedHashRing:
    ring = SaltedHashRing(v, salt)
    for node_id in make_node_ids(n):
        ring.add_node(node_id)
    return ring


# ---------- การทดลอง (คืน list ของ dict หนึ่งแถวต่อ 1 รอบการวัด) ----------

def run_experiment_A(k_values, n=10, v=32, salts=(0, 1, 2)):
    """ทดลอง A: ผลของขนาดข้อมูล K ต่อเวลาและหน่วยความจำ"""
    rows = []
    for k in k_values:
        channels = make_channels(k)
        for rnd, salt in enumerate(salts, 1):
            gc.collect()
            system, t_ring = timed(ConsistentHashSystem, make_node_ids(n), v, salt)
            _, t_place = timed(system.init_guests, channels)

            codes = system.registry.all_guest_codes()
            rng = random.Random(f"A:{k}:{salt}")
            picks = [rng.choice(codes) for _ in range(SEARCH_BATCH)] if codes else []
            addrs = [system.registry.find_by_guest_code(c, s) for c, s in picks]
            t_code = _time_batch(system.registry.find_by_guest_code, picks)
            t_addr = _time_batch(system.registry.find_by_address, addrs)
            t_calc = _time_batch(system.ring.get_owner_of_guest, picks)

            gc.collect()
            rooms, t_list = timed(system.list_occupied_rooms)

            # รอบวัดหน่วยความจำแยกจากรอบจับเวลา
            _, mem_cur, mem_peak = measure_memory(_build_ch, n, v, salt, k)
            rows.append({
                "experiment": "A", "round": rnd, "salt": salt, "K": k, "N": n, "V": v,
                "method": "consistent",
                "ring_build_s": t_ring, "place_s": t_place,
                "search_by_code_s": t_code, "search_by_address_s": t_addr,
                "search_ring_compute_s": t_calc,
                "list_s": t_list, "listed_count": len(rooms),
                "mem_current_mib": mem_cur, "mem_peak_mib": mem_peak,
            })
    return rows


def _expected_rate(method: str, op: str, n: int):
    """ค่าคาดหวังเมื่อแฮชกระจายสม่ำเสมอ (None = ไม่มีสูตรที่ยืนยันได้)"""
    if method == "consistent":
        return 1 / (n + 1) if op == "add" else 1 / n
    return n / (n + 1) if op == "add" else None


def run_experiment_B(n_values, k=10_000, v=32, salts=(0, 1, 2)):
    """ทดลอง B: เพิ่มอาคารใหม่ B{N+1} และลบอาคารตรงกลาง (ดัชนี N//2) เทียบสองวิธี
    แต่ละกรณีเริ่มจากสถานะเดิมใหม่ ใช้แขก/อาคาร/salt ชุดเดียวกัน"""
    rows = []
    for n in n_values:
        new_id, victim = f"B{n + 1:02d}", make_node_ids(n)[n // 2]
        for rnd, salt in enumerate(salts, 1):
            for method in ("consistent", "mod"):
                for op in ("add", "remove"):
                    system = _build_ch(n, v, salt, k) if method == "consistent" else _build_mod(n, salt, k)
                    target = new_id if op == "add" else victim
                    gc.collect()
                    fn = system.add_building if op == "add" else system.remove_building
                    report, t_total = timed(fn, target)
                    rows.append({
                        "experiment": "B", "round": rnd, "salt": salt, "K": k, "N": n, "V": v,
                        "method": method, "op": op, "target_node": target,
                        "moved_count": report.moved_count, "move_rate": report.move_rate,
                        "expected_rate": _expected_rate(method, op, n),
                        "rule_ok": check_move_rule(report, op, target),
                        "guests_after": system.guest_count(),
                        "time_total_s": t_total,
                        "time_ring_s": system.last_timing["ring_s"],
                        "time_find_s": system.last_timing["find_s"],
                        "time_update_s": system.last_timing["update_s"],
                    })
    return rows


def run_experiment_C(v_values, n=10, k=10_000, salts=(0, 1, 2)):
    """ทดลอง C: ผลของจำนวน virtual node V ต่อความสมดุลโหลด หน่วยความจำ และการย้าย"""
    rows = []
    new_id, victim = f"B{n + 1:02d}", make_node_ids(n)[n // 2]
    for v in v_values:
        for rnd, salt in enumerate(salts, 1):
            system = _build_ch(n, v, salt, k)
            loads = system.building_loads()
            stats = load_stats(loads)
            _, ring_cur, _ = measure_memory(_build_ring_only, n, v, salt)
            _, mem_cur, mem_peak = measure_memory(_build_ch, n, v, salt, k)
            rep_add = system.add_building(new_id)
            rep_rem = _build_ch(n, v, salt, k).remove_building(victim)
            rows.append({
                "experiment": "C", "round": rnd, "salt": salt, "K": k, "N": n, "V": v,
                "method": "consistent",
                "per_building_counts": ";".join(f"{nid}={loads[nid]}" for nid in sorted(loads)),
                "load_max": stats["max"], "load_min": stats["min"], "load_mean": stats["mean"],
                "load_std": stats["std"], "load_cv": stats["cv"],
                "ring_mem_current_mib": ring_cur,
                "mem_current_mib": mem_cur, "mem_peak_mib": mem_peak,
                "add_moved_count": rep_add.moved_count, "add_move_rate": rep_add.move_rate,
                "remove_moved_count": rep_rem.moved_count, "remove_move_rate": rep_rem.move_rate,
            })
    return rows


# ---------- กราฟ ----------

BLUE, ORANGE, GREEN = "#0072B2", "#D55E00", "#009E73"


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("Tahoma", "Leelawadee UI", "Noto Sans Thai", "Sarabun", "TH Sarabun New",
                 "Thonburi", "Loma", "Garuda", "Angsana New", "Arial Unicode MS"):
        if name in have:
            plt.rcParams["font.family"] = name   # ต้องใช้ฟอนต์ที่มีอักษรไทย
            break
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["mathtext.fontset"] = "dejavusans"
    return plt


def _series(rows, x_key, metric, scale=1.0, **where):
    """คืน (x, มัธยฐาน, ต่ำสุด, สูงสุด) ของ metric ข้ามรอบ แยกตาม x"""
    groups = {}
    for r in rows:
        if r.get(metric) is not None and all(r.get(k) == val for k, val in where.items()):
            groups.setdefault(r[x_key], []).append(r[metric] * scale)
    xs = sorted(groups)
    return (xs, [statistics.median(groups[x]) for x in xs],
            [min(groups[x]) for x in xs], [max(groups[x]) for x in xs])


def _line(ax, series, label, color, marker="o", linestyle="-"):
    xs, med, lo, hi = series
    if xs:
        ax.errorbar(xs, med, yerr=[[m - a for m, a in zip(med, lo)], [b - m for m, b in zip(med, hi)]],
                    label=label, color=color, marker=marker, linestyle=linestyle,
                    linewidth=2, markersize=6, capsize=3)


def _finish(fig, axes, title, rows, out_path):
    from matplotlib.ticker import FuncFormatter, NullFormatter
    for ax in axes:
        ax.grid(True, alpha=0.25)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for axis in (ax.xaxis, ax.yaxis):
            if axis.get_scale() == "log":   # ป้ายตัวเลขธรรมดา เลี่ยงเลขชี้กำลังติดลบ
                axis.set_major_formatter(FuncFormatter(lambda val, _: f"{val:g}"))
                axis.set_minor_formatter(NullFormatter())
        ax.legend(frameon=False, fontsize=9)
    salts = sorted({r["salt"] for r in rows})
    fig.suptitle(f"{title}\nค่ามัธยฐาน แท่ง = min–max ของ {len(salts)} รอบ (salt {', '.join(map(str, salts))})",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    fig.clf()


def plot_time_vs_k(results, out_path="time_vs_k.png"):
    """กราฟ (ก): เวลาเทียบ K"""
    plt = _plt()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5))
    ks = sorted({r["K"] for r in results})
    for metric, label, color, mk in [("ring_build_s", "สร้างวงแหวน", GREEN, "s"),
                                     ("place_s", "จัดแขกเริ่มต้น", BLUE, "o"),
                                     ("list_s", "สร้างรายการห้อง (เรียงลำดับ)", ORANGE, "^")]:
        _line(a1, _series(results, "K", metric), label, color, mk)
    for metric, label, color, mk in [("search_by_code_s", "ค้นด้วยรหัสแขก (ดัชนี)", BLUE, "o"),
                                     ("search_by_address_s", "ค้นด้วยที่อยู่ห้อง (ดัชนี)", GREEN, "s"),
                                     ("search_ring_compute_s", "คำนวณอาคารจากวงแหวน", ORANGE, "^")]:
        _line(a2, _series(results, "K", metric, scale=1e6), label, color, mk)
    for ax, ylabel, title in [(a1, "เวลา (วินาที)", "ต้นทุนครั้งเดียว"),
                              (a2, "เวลาต่อการค้นหา 1 ครั้ง (ไมโครวินาที)",
                               f"ค้นหา (เฉลี่ยจากชุด {SEARCH_BATCH} ครั้ง)")]:
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xticks(ks)
        ax.set_xlabel("จำนวนแขก K (คน)"); ax.set_ylabel(ylabel); ax.set_title(title)
    _finish(fig, (a1, a2), f"ทดลอง A: เวลาเทียบขนาดข้อมูล K   (N={results[0]['N']}, V={results[0]['V']})",
            results, out_path)


def plot_migration_rate_vs_n(results, out_path="migration_rate_vs_n.png"):
    """กราฟ (ข): อัตราการย้ายเทียบ N ของสองวิธี (ซ้ายเพิ่มอาคาร ขวาลบอาคาร)"""
    plt = _plt()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, op, title in [(axes[0], "add", "เพิ่ม 1 อาคาร"), (axes[1], "remove", "ลบ 1 อาคาร")]:
        _line(ax, _series(results, "N", "move_rate", method="consistent", op=op),
              "Consistent Hashing (วัดจริง)", BLUE, "o")
        _line(ax, _series(results, "N", "move_rate", method="mod", op=op),
              "hash mod N (วัดจริง)", ORANGE, "s")
        for method, color, label in [("consistent", BLUE, "คาดหวัง CH"), ("mod", ORANGE, "คาดหวัง mod")]:
            xs, med, _, _ = _series(results, "N", "expected_rate", method=method, op=op)
            if xs:
                ax.plot(xs, med, color=color, linestyle="--", linewidth=1.5, label=label)
        ax.set_xticks(sorted({r["N"] for r in results}))
        ax.set_ylim(0, 1.05)
        ax.set_xlabel("จำนวนอาคารก่อนเปลี่ยน N (หลัง)"); ax.set_title(title)
    axes[0].set_ylabel("อัตราการย้าย = แขกที่ย้าย / K (สัดส่วน)")
    _finish(fig, axes, f"ทดลอง B: อัตราการย้ายเทียบจำนวนอาคาร N   (K={results[0]['K']:,}, V={results[0]['V']})",
            results, out_path)


def plot_v_effect(results, out_path="v_effect.png"):
    """กราฟ (ค): ผลของ V ต่อ CV และหน่วยความจำ"""
    plt = _plt()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5))
    vs = sorted({r["V"] for r in results})
    _line(a1, _series(results, "V", "load_cv"), "CV ของโหลด", BLUE)
    a1.set_ylim(bottom=0)
    a1.set_ylabel("CV = ส่วนเบี่ยงเบนมาตรฐาน / ค่าเฉลี่ย (ไม่มีหน่วย ยิ่งต่ำยิ่งสมดุล)")
    a1.set_title("ความสมดุลของโหลด")
    for metric, label, color, mk, ls in [("mem_current_mib", "วงแหวน+แขก (current)", BLUE, "o", "-"),
                                         ("mem_peak_mib", "วงแหวน+แขก (peak)", ORANGE, "s", "-"),
                                         ("ring_mem_current_mib", "วงแหวนอย่างเดียว (current)", GREEN, "^", "--")]:
        _line(a2, _series(results, "V", metric), label, color, mk, ls)
    a2.set_yscale("log")
    a2.set_ylabel("หน่วยความจำที่ Python ติดตาม (MiB, แกน log)")
    a2.set_title("หน่วยความจำ (tracemalloc)")
    for ax in (a1, a2):
        ax.set_xscale("log", base=2); ax.set_xticks(vs); ax.set_xticklabels([str(x) for x in vs])
        ax.minorticks_off()
        ax.set_xlabel("จำนวน virtual node ต่ออาคาร V")
    _finish(fig, (a1, a2), f"ทดลอง C: ผลของจำนวน virtual node V   (N={results[0]['N']}, K={results[0]['K']:,})",
            results, out_path)


# ---------- CSV ----------

def export_experiment_csv(path: str, results) -> None:
    """เขียน CSV (UTF-8) ทุกแถวที่วัดได้ พร้อมพารามิเตอร์ K, N, V, salt, รอบที่
    results = list ของแถว หรือ dict {"A": แถว, "B": แถว, "C": แถว}  (_s = วินาที, _mib = MiB)"""
    rows = [r for v in results.values() for r in v] if isinstance(results, dict) else list(results)
    columns = ["experiment", "round", "salt", "K", "N", "V", "method", "op"]
    columns = [c for c in columns if any(c in r for r in rows)]
    for r in rows:
        columns += [key for key in r if key not in columns]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: ("" if r.get(c) is None else r[c]) for c in columns})