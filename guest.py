"""
guest.py
งานของ: คนที่ 2 -- ข้อมูลแขกและเลขห้อง (Guest / Room / ดัชนีค้นหา)

- compute_room_no(c, s): Cantor pairing function ด้วยจำนวนเต็มล้วน
- GuestRegistry: เก็บแขกทั้งหมด + ดัชนีสองทาง
    by_guest_code : (c, s)             -> GuestRecord
    by_address    : (node_id, room_no) -> (c, s)
  ทุกเมธอดที่แก้ข้อมูลต้องอัปเดตทั้งสอง dict ให้สอดคล้องกันเสมอ

หมายเหตุ: ไฟล์นี้ไม่รู้จัก HashRing เลย การเลือกอาคารเป็นหน้าที่ของ hotel_system.py
ซึ่งต้องส่ง node_id_lookup_fn(c, s) -> node_id (str) เข้ามา
(HashRing.get_owner คืน tuple (position, node_id, j) ดังนั้นฝั่ง hotel_system
ต้องหยิบเฉพาะ node_id ออกมาก่อนส่งเข้ามา เช่น lambda c, s: ring.get_owner_of_guest(c, s)[1])
"""

from dataclasses import dataclass


def _is_pos_int(x) -> bool:
    # bool เป็น subclass ของ int จึงต้องกันออกเอง
    return isinstance(x, int) and not isinstance(x, bool) and x >= 1


def compute_room_no(c: int, s: int) -> int:
    """
    คำนวณเลขห้องจากรหัสแขก (c, s) ด้วย Cantor pairing function
    c, s เป็นจำนวนเต็มบวก (เริ่มที่ 1)
    ตัวอย่าง: (1,1)->1  (2,1)->2  (1,2)->3  (3,1)->4  (2,2)->5
    """
    if not _is_pos_int(c) or not _is_pos_int(s):
        raise ValueError(f"c และ s ต้องเป็นจำนวนเต็มบวก (ได้ c={c!r}, s={s!r})")
    a = c - 1
    b = s - 1
    return ((a + b) * (a + b + 1)) // 2 + b + 1


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

    # ---------- เพิ่ม ----------
    def add_guest(self, c: int, s: int, node_id: str) -> tuple[bool, str]:
        """
        คืน (True, "") ถ้าสำเร็จ
        คืน (False, เหตุผล) ถ้าปฏิเสธ เช่น "(c,s) ซ้ำกับแขกที่มีอยู่แล้ว"
        """
        if not _is_pos_int(c) or not _is_pos_int(s):
            return False, f"รหัสแขก ({c!r},{s!r}) ไม่ถูกต้อง: c และ s ต้องเป็นจำนวนเต็มบวก"
        if (c, s) in self.by_guest_code:
            return False, f"({c},{s}) ซ้ำกับแขกที่มีอยู่แล้ว"
        self._insert(c, s, node_id)
        return True, ""

    def add_guests_batch(
        self, c: int, s_start: int, count: int, node_id_lookup_fn
    ) -> tuple[bool, str, list[tuple[int, int]]]:
        """
        node_id_lookup_fn(c, s) -> node_id  (เรียกเพื่อถามว่าแขกคนนี้อยู่อาคารไหน)
        คืน (True, "", รายชื่อ (c,s) ที่เพิ่มสำเร็จ) หรือ (False, เหตุผล, [])
        ถ้า count == 0 ให้คืน (True, "ไม่มีการเปลี่ยนแปลง", [])
        ตรวจ "ทั้งกลุ่ม" ก่อน แล้วค่อยเพิ่มจริง (all-or-nothing)
        """
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            return False, f"count ต้องเป็นจำนวนเต็มไม่ติดลบ (ได้ {count!r})", []
        if count == 0:
            return True, "ไม่มีการเปลี่ยนแปลง", []
        if not _is_pos_int(c) or not _is_pos_int(s_start):
            return False, f"c={c!r}, s_start={s_start!r} ต้องเป็นจำนวนเต็มบวก", []

        codes = [(c, s) for s in range(s_start, s_start + count)]

        # 1) ตรวจซ้ำทั้งกลุ่มก่อน
        dups = [code for code in codes if code in self.by_guest_code]
        if dups:
            shown = ", ".join(f"({a},{b})" for a, b in dups[:5])
            more = f" และอีก {len(dups) - 5} รายการ" if len(dups) > 5 else ""
            return False, f"ปฏิเสธทั้งกลุ่ม: ซ้ำกับแขกที่มีอยู่แล้ว {shown}{more}", []

        # 2) ถาม node_id ของทุกคนก่อนแก้ข้อมูล
        #    (ถ้า lookup ล้มเหลวกลางทาง registry จะยังไม่ถูกแก้เลย)
        try:
            plan = [(cc, ss, node_id_lookup_fn(cc, ss)) for cc, ss in codes]
        except Exception as e:  # noqa: BLE001
            return False, f"หาอาคารของแขกไม่สำเร็จ ไม่มีการเปลี่ยนแปลง: {e}", []

        # 3) เพิ่มจริง
        for cc, ss, nid in plan:
            self._insert(cc, ss, nid)
        return True, "", codes

    def _insert(self, c: int, s: int, node_id: str) -> None:
        room_no = compute_room_no(c, s)
        self.by_guest_code[(c, s)] = GuestRecord(c, s, node_id, room_no)
        self.by_address[(node_id, room_no)] = (c, s)

    # ---------- ลบ ----------
    def remove_guest(self, c: int, s: int) -> tuple[bool, str]:
        rec = self.by_guest_code.pop((c, s), None)
        if rec is None:
            return False, f"ไม่พบแขก ({c},{s})"
        self.by_address.pop((rec.node_id, rec.room_no), None)
        return True, ""

    # ---------- ค้นหา ----------
    def find_by_guest_code(self, c: int, s: int):
        """คืน (node_id, room_no) หรือ None"""
        rec = self.by_guest_code.get((c, s))
        if rec is None:
            return None
        return rec.node_id, rec.room_no

    def find_by_address(self, node_id: str, room_no: int):
        """คืน (c, s) หรือ None"""
        return self.by_address.get((node_id, room_no))

    # ---------- ย้ายอาคาร ----------
    def update_node_of_guest(self, c: int, s: int, new_node_id: str) -> None:
        """ใช้ตอนย้ายอาคาร room_no คงเดิม เปลี่ยนแค่ node_id เรียกจากตอนเพิ่ม/ลบอาคาร
        ถ้าไม่พบแขกจะ raise KeyError (เป็นความผิดพลาดของผู้เรียก ไม่ควรเกิดในการใช้งานปกติ)"""
        rec = self.by_guest_code.get((c, s))
        if rec is None:
            raise KeyError(f"ไม่พบแขก ({c},{s})")
        if rec.node_id == new_node_id:
            return
        self.by_address.pop((rec.node_id, rec.room_no), None)
        rec.node_id = new_node_id
        self.by_address[(new_node_id, rec.room_no)] = (c, s)

    # ---------- รายการ ----------
    def list_guests_in_building(self, node_id: str) -> list[tuple[int, int, int]]:
        """คืน list ของ (room_no, c, s) เรียงตาม room_no จากน้อยไปมาก"""
        result = [
            (room_no, c, s)
            for (nid, room_no), (c, s) in self.by_address.items()
            if nid == node_id
        ]
        result.sort()
        return result

    def guest_count(self) -> int:
        return len(self.by_guest_code)

    def all_guest_codes(self):
        """คืน iterable ของ (c, s) ทั้งหมด -- ใช้โดยคนที่ 3 ตอนตรวจแขกทุกคน (แบบ ก)"""
        return list(self.by_guest_code.keys())