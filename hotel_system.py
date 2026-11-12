"""HotelSystem ใช้ร่วมกันทั้งเมนูและการทดลอง; ตรรกะแยกตามหน้าที่."""
import csv
import statistics

from hashring import HashRing
from guest import GuestRegistry, _is_pos_int
import rebalance


class HotelSystem:
    def __init__(self, initial_node_ids: list[str], v: int, *, salt: str | None = None):
        if not initial_node_ids:
            raise ValueError("ต้องมีอาคารเริ่มต้นอย่างน้อย 1 อาคาร")
        self.ring = HashRing(v, salt=salt)
        for node_id in initial_node_ids:
            if not self.ring.valid_node_id(node_id):
                raise ValueError("รหัสอาคารต้องไม่ว่างและไม่มีช่องว่าง")
            if not self.ring.add_node(node_id):
                raise ValueError(f"รหัสอาคารซ้ำในชุดเริ่มต้น: {node_id}")
        self.registry = GuestRegistry()
        self.last_timing = {"ring_s": 0.0, "find_s": 0.0, "update_s": 0.0}

    def get_node_id_fix(self, c: int, s: int) -> str:
        return self.ring.get_owner_of_guest(c, s)[1]

    def init_guests(self, channels: dict[int, int]) -> None:
        """เริ่ม s=1 ทุกช่องทาง ตรวจทั้งชุดก่อนเพิ่มเพื่อไม่เพิ่มค้างบางส่วน."""
        for c, count in channels.items():
            if (not _is_pos_int(c) or not isinstance(count, int)
                    or isinstance(count, bool) or count < 0):
                raise ValueError("ช่องทางต้องเป็นจำนวนเต็มบวก จำนวนแขกต้องเป็นจำนวนเต็ม >= 0")
        plan = []
        for c, count in channels.items():
            for s in range(1, count + 1):
                if self.registry.find_by_guest_code(c, s) is not None:
                    raise ValueError(f"รหัสแขก ({c},{s}) ซ้ำ ไม่มีการเปลี่ยนแปลง")
                plan.append((c, s, self.get_node_id_fix(c, s)))
        for c, s, node_id in plan:
            self.registry.add_guest(c, s, node_id)

    def guest_count(self) -> int:
        return self.registry.guest_count()

    def add_guest(self, c: int, s: int) -> tuple[bool, str]:
        if not _is_pos_int(c) or not _is_pos_int(s):
            return False, "c และ s ต้องเป็นจำนวนเต็มบวก"
        return self.registry.add_guest(c, s, self.get_node_id_fix(c, s))

    def add_guests_batch(self, c: int, s_start: int, count: int) -> tuple[bool, str, list]:
        return self.registry.add_guests_batch(c, s_start, count, self.get_node_id_fix)

    def remove_guest(self, c: int, s: int) -> tuple[bool, str]:
        return self.registry.remove_guest(c, s)

    def find_by_guest(self, c: int, s: int) -> tuple[str, int] | None:
        return self.registry.find_by_guest_code(c, s)

    def find_by_address(self, node_id: str, room_no: int):
        return self.registry.find_by_address(node_id, room_no)

    def add_building(self, node_id: str) -> rebalance.MigrationReport:
        report = rebalance.add_building(self.ring, self.registry, node_id)
        self.last_timing = report.timings.copy()
        return report

    def remove_building(self, node_id: str) -> rebalance.MigrationReport:
        report = rebalance.remove_building(self.ring, self.registry, node_id)
        self.last_timing = report.timings.copy()
        return report

    def list_occupied_rooms(self) -> list[tuple[str, int, int, int]]:
        """สร้างรายการครั้งเดียว เรียง node_id, room_no: O(K log(K+1))."""
        return sorted((r.node_id, r.room_no, r.c, r.s)
                      for r in self.registry.by_guest_code.values())

    def building_loads(self) -> dict[str, int]:
        """นับครั้งเดียว รวมอาคารว่าง: O(N log(N+1) + K)."""
        loads = dict.fromkeys(sorted(self.ring.nodes), 0)
        for rec in self.registry.by_guest_code.values():
            loads[rec.node_id] += 1
        return loads

    def load_balance_report(self) -> tuple[bool, dict, str]:
        data = {"per_building": self.building_loads(), "max": 0, "min": 0,
                "mean": 0, "std": 0, "cv": None}
        values = list(data["per_building"].values())
        if self.guest_count() == 0:
            return False, data, "ไม่มีแขก สถิติพื้นฐานเป็น 0 ไม่คำนวณ CV"
        data.update(max=max(values), min=min(values), mean=statistics.mean(values),
                    std=statistics.pstdev(values))
        data["cv"] = data["std"] / data["mean"]
        return True, data, ""

    def export_guests_csv(self, path: str) -> None:
        with open(path, "w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("channel_id", "sequence_id", "node_id", "room_no"))
            writer.writerows((c, s, node, room)
                             for node, room, c, s in self.list_occupied_rooms())

    def export_migrations_csv(self, path: str, migration_report: rebalance.MigrationReport) -> None:
        with open(path, "w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("c", "s", "old_node_id", "new_node_id", "room_no"))
            writer.writerows((m.c, m.s, m.old_node_id, m.new_node_id, m.room_no)
                             for m in migration_report.moves)


def _parse_int(text: str, name: str, minimum: int = 1) -> int:
    try:
        value = int(text)
    except ValueError:
        raise ValueError(f"{name} ต้องเป็นจำนวนเต็ม >= {minimum}") from None
    if value < minimum:
        raise ValueError(f"{name} ต้องเป็นจำนวนเต็ม >= {minimum}")
    return value


def _read_int(prompt: str, name: str, minimum: int = 1) -> int:
    return _parse_int(input(prompt).strip(), name, minimum)


def _read_pair(prompt: str) -> tuple[str, str]:
    parts = input(prompt).split()
    if len(parts) != 2:
        raise ValueError("กรุณากรอกข้อมูลให้ครบ 2 ค่า คั่นด้วยช่องว่าง")
    return parts[0], parts[1]


def _read_guest_code(prompt: str) -> tuple[int, int]:
    c, s = _read_pair(prompt)
    return _parse_int(c, "c"), _parse_int(s, "s")


def _show_migration(report: rebalance.MigrationReport, limit: int = 50) -> None:
    print(f"ย้ายทั้งหมด {report.moved_count} คน")
    if report.move_rate is None:
        print("ไม่คำนวณอัตราการย้ายเพราะไม่มีแขก (K=0)")
    else:
        print(f"อัตราการย้าย: {report.move_rate:.6f} ({report.move_rate:.2%})")
    for m in report.moves[:limit]:
        print(f"  ({m.c}, {m.s}): {m.old_node_id} -> {m.new_node_id}, ห้อง {m.room_no}")
    if len(report.moves) > limit:
        print(f"แสดง {limit} จาก {len(report.moves)} รายการ ส่งออก CSV เพื่อดูครบ")


def run_cli():
    print("=== ระบบโรงแรมอนันต์แบบกระจาย (Consistent Hashing) ===")
    system = None
    migration_report = None
    while True:
        print("\n[1] เริ่มระบบใหม่  [2] เพิ่มแขก  [3] ลบแขก  [4] เพิ่มอาคาร  "
              "[5] ลบอาคาร  [6] ค้นหา  [7] แสดงห้อง  [8] รายงานโหลด  [9] Export CSV  [0] ออก")
        try:
            choice = input("เลือกเมนู: ").strip()
            if choice == "0":
                print("ออกจากโปรแกรม")
                break
            if choice not in {str(i) for i in range(1, 10)}:
                print("FAILED: ไม่มี Option นี้")
                continue
            if choice != "1" and system is None:
                print("FAILED: กรุณาเริ่มระบบด้วยเมนู 1 ก่อน")
                continue
            if choice == "1":
                nodes = input("ใส่ ID อาคารเริ่มต้น คั่นด้วยช่องว่าง (N = จำนวน ID): ").split()
                v = _read_int("จำนวน Virtual Node ต่ออาคาร (V): ", "V")
                candidate = HotelSystem(nodes, v)
                channel_count = _read_int("จำนวนช่องทางเริ่มต้น (0 = ยังไม่มีแขก): ", "จำนวนช่องทาง", 0)
                channels = {c: _read_int(f"จำนวนแขกช่องทาง {c} (เริ่ม s=1): ", "จำนวนแขก", 0)
                            for c in range(1, channel_count + 1)}
                candidate.init_guests(channels)
                system = candidate
                migration_report = None
                print(f"สร้างระบบสำเร็จ N={len(nodes)}, V={v}, แขกทั้งหมด {system.guest_count()} คน")
            elif choice == "2":
                c = _read_int("ค่า c ของแขก: ", "c")
                s = _read_int("ค่า s เริ่มต้น: ", "s")
                count = _read_int("จำนวนแขก (0 = ไม่มีการเปลี่ยนแปลง): ", "count", 0)
                ok, reason, added = system.add_guests_batch(c, s, count)
                if not ok:
                    print(f"FAILED: {reason}")
                else:
                    print(f"เพิ่มแขก {len(added)} คนแล้ว" if count else reason)
            elif choice == "3":
                c, s = _read_guest_code("รหัสแขกที่ต้องการลบ: c s: ")
                ok, reason = system.remove_guest(c, s)
                print(f"ลบแขก ({c}, {s}) แล้ว" if ok else f"FAILED: {reason}")
            elif choice in {"4", "5"}:
                node = input("ID อาคาร: ").strip()
                report = (system.add_building if choice == "4" else system.remove_building)(node)
                if not report.accepted:
                    print(f"FAILED: {report.reason}")
                    continue
                migration_report = report
                print(report.reason)
                _show_migration(report)
            elif choice == "6":
                mode = input("[1] ค้นด้วยรหัสแขก [2] ค้นด้วยอาคารและเลขห้อง: ").strip()
                if mode == "1":
                    c, s = _read_guest_code("รหัสแขก: c s: ")
                    address = system.find_by_guest(c, s)
                    print(f"แขก ({c}, {s}) อยู่ที่อาคาร {address[0]} ห้อง {address[1]}"
                          if address else "ไม่พบแขก")
                elif mode == "2":
                    node, room = _read_pair("ID อาคาร และเลขห้อง: ")
                    room = _parse_int(room, "เลขห้อง")
                    code = system.find_by_address(node, room)
                    print(f"อาคาร {node} ห้อง {room}: รหัสแขก {code}" if code else "ไม่พบแขก")
                else:
                    print("FAILED: ไม่มีโหมดค้นหานี้")
            elif choice == "7":
                rooms = system.list_occupied_rooms()
                print(f"ห้องที่มีผู้พักทั้งหมด {len(rooms)} ห้อง")
                for node, room, c, s in rooms[:100]:
                    print(f"อาคาร {node} ห้อง {room}: รหัสแขก ({c}, {s})")
                if len(rooms) > 100:
                    print("แสดง 100 รายการแรก ส่งออก CSV เพื่อดูครบ")
            elif choice == "8":
                _, data, message = system.load_balance_report()
                for node, count in data["per_building"].items():
                    print(f"อาคาร {node}: {count} คน")
                for key in ("max", "min", "mean", "std"):
                    print(f"{key}: {data[key]}")
                print(f"CV: {data['cv']}" if data["cv"] is not None else message)
            elif choice == "9":
                mode = input("[1] Export ข้อมูลแขก [2] Export รายการย้ายล่าสุด: ").strip()
                if mode not in {"1", "2"}:
                    print("FAILED: ไม่มีรายงานประเภทนี้")
                    continue
                if mode == "2" and migration_report is None:
                    print("FAILED: ไม่มี Migration Report กรุณาเพิ่ม/ลบอาคารก่อน")
                    continue
                path = input("Path ไฟล์ CSV: ").strip()
                if not path:
                    raise ValueError("กรุณาระบุชื่อไฟล์ CSV")
                if not path.lower().endswith(".csv"):
                    path += ".csv"
                if mode == "1":
                    system.export_guests_csv(path)
                else:
                    system.export_migrations_csv(path, migration_report)
                print("เขียนไฟล์ CSV แล้ว")
        except ValueError as error:
            print(f"FAILED: {error}")
        except OSError as error:
            print(f"FAILED: เขียนไฟล์ไม่สำเร็จ: {error}")
        except (EOFError, KeyboardInterrupt):
            print("\nออกจากโปรแกรม")
            break


if __name__ == "__main__":
    run_cli()
