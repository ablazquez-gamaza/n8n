#!/usr/bin/env python3
import csv
import datetime as dt
import io
import json
import math
import os
import sqlite3
import zipfile
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "planner.db"


def ensure_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS call_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            franja TEXT NOT NULL,
            calls INTEGER NOT NULL,
            FOREIGN KEY(upload_id) REFERENCES uploads(id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS forecasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            upload_id INTEGER NOT NULL,
            day TEXT NOT NULL,
            franja TEXT NOT NULL,
            calls REAL NOT NULL,
            model_version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(upload_id) REFERENCES uploads(id)
        )
        """
    )
    conn.commit()
    conn.close()


def parse_date(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Fecha vacía")
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return dt.datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Fecha inválida: {raw}")


def parse_slot(raw: str) -> str:
    raw = (raw or "").strip()
    try:
        t = dt.datetime.strptime(raw, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"Franja inválida: {raw}") from exc
    if t.minute not in (0, 30):
        raise ValueError(f"Franja no es de 30 minutos: {raw}")
    return t.strftime("%H:%M")


def parse_calls(raw: str) -> int:
    value = int(float(str(raw).strip()))
    if value < 0:
        raise ValueError("LLAMADAS no puede ser negativo")
    return value


def read_csv_rows(file_bytes: bytes):
    sample = file_bytes[:2048]
    encoding = "utf-8-sig"
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        encoding = "latin-1"

    text = file_bytes.decode(encoding)
    reader = csv.DictReader(io.StringIO(text))
    headers = {h.upper().strip(): h for h in (reader.fieldnames or [])}
    required = ["DÍA", "FRANJA", "LLAMADAS"]
    if not all(r in headers for r in required):
        raise ValueError("El CSV debe incluir columnas DÍA, FRANJA y LLAMADAS")

    rows = []
    for row in reader:
        rows.append(
            {
                "day": parse_date(row[headers["DÍA"]]),
                "franja": parse_slot(row[headers["FRANJA"]]),
                "calls": parse_calls(row[headers["LLAMADAS"]]),
            }
        )
    return rows


def read_xlsx_rows(file_bytes: bytes):
    zf = zipfile.ZipFile(io.BytesIO(file_bytes))
    shared_strings = []
    if "xl/sharedStrings.xml" in zf.namelist():
        root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
        ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        for si in root.findall("s:si", ns):
            text = "".join(t.text or "" for t in si.findall(".//s:t", ns))
            shared_strings.append(text)

    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main", "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    first_sheet = workbook.find("s:sheets/s:sheet", ns)
    rel_id = first_sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")

    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_ns = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
    target = None
    for rel in rels.findall("r:Relationship", rel_ns):
        if rel.attrib.get("Id") == rel_id:
            target = rel.attrib.get("Target")
            break
    if not target:
        raise ValueError("No se encontró la hoja en el Excel")

    sheet_path = f"xl/{target}".replace("xl/xl/", "xl/")
    sheet_xml = ET.fromstring(zf.read(sheet_path))

    header_map = {}
    rows = []

    def cell_value(cell):
        t = cell.attrib.get("t")
        v = cell.find("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v")
        if v is None:
            return ""
        raw = v.text or ""
        if t == "s":
            idx = int(raw)
            return shared_strings[idx] if idx < len(shared_strings) else ""
        return raw

    for row in sheet_xml.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row"):
        parsed = {}
        for cell in row.findall("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c"):
            ref = cell.attrib.get("r", "A1")
            col = "".join([c for c in ref if c.isalpha()])
            parsed[col] = cell_value(cell)

        row_num = int(row.attrib.get("r", "1"))
        if row_num == 1:
            for col, val in parsed.items():
                header_map[val.upper().strip()] = col
            continue

        if not header_map:
            continue

        try:
            day_raw = parsed.get(header_map["DÍA"], "")
            if day_raw.replace(".", "", 1).isdigit():
                excel_day = float(day_raw)
                day_date = (dt.date(1899, 12, 30) + dt.timedelta(days=excel_day)).isoformat()
            else:
                day_date = parse_date(day_raw)

            franja_raw = parsed.get(header_map["FRANJA"], "")
            if franja_raw.replace(".", "", 1).isdigit():
                fraction = float(franja_raw)
                minutes = int(round(fraction * 24 * 60))
                hh = minutes // 60
                mm = minutes % 60
                franja = parse_slot(f"{hh:02d}:{mm:02d}")
            else:
                franja = parse_slot(franja_raw)

            rows.append(
                {
                    "day": day_date,
                    "franja": franja,
                    "calls": parse_calls(parsed.get(header_map["LLAMADAS"], "0")),
                }
            )
        except KeyError as exc:
            raise ValueError("El Excel debe incluir DÍA, FRANJA y LLAMADAS") from exc

    if not rows:
        raise ValueError("No se encontraron filas válidas en el Excel")
    return rows


def linear_regression(points):
    n = len(points)
    if n < 2:
        return 0.0
    sx = sum(x for x, _ in points)
    sy = sum(y for _, y in points)
    sxy = sum(x * y for x, y in points)
    sxx = sum(x * x for x, _ in points)
    denominator = (n * sxx) - (sx * sx)
    if denominator == 0:
        return 0.0
    return ((n * sxy) - (sx * sy)) / denominator


def compute_forecast(rows, horizon_days=365):
    by_slot = {}
    by_day = {}
    for r in rows:
        date_obj = dt.date.fromisoformat(r["day"])
        dow = date_obj.weekday()
        key = (dow, r["franja"])
        by_slot.setdefault(key, []).append(r["calls"])
        by_day[r["day"]] = by_day.get(r["day"], 0) + r["calls"]

    slot_avg = {k: sum(v) / len(v) for k, v in by_slot.items()}
    day_items = sorted((dt.date.fromisoformat(d), total) for d, total in by_day.items())
    base_day = day_items[0][0]
    reg_points = [((d - base_day).days, total) for d, total in day_items]
    slope = linear_regression(reg_points)
    baseline = sum(total for _, total in day_items) / max(len(day_items), 1)
    trend_per_day = slope / baseline if baseline else 0.0

    max_hist_date = max(dt.date.fromisoformat(r["day"]) for r in rows)
    forecasts = []
    for offset in range(1, horizon_days + 1):
        target_day = max_hist_date + dt.timedelta(days=offset)
        day_growth = max(0.1, 1 + (trend_per_day * offset))
        for minute in range(0, 24 * 60, 30):
            franja = f"{minute // 60:02d}:{minute % 60:02d}"
            base_calls = slot_avg.get((target_day.weekday(), franja), 0.0)
            calls = round(base_calls * day_growth, 2)
            forecasts.append(
                {
                    "day": target_day.isoformat(),
                    "franja": franja,
                    "calls": calls,
                }
            )
    return forecasts


def erlang_c(traffic, agents):
    if agents <= traffic:
        return 1.0
    numerator = (traffic**agents / math.factorial(agents)) * (agents / (agents - traffic))
    series = sum(traffic**n / math.factorial(n) for n in range(agents))
    return numerator / (series + numerator)


def service_level(traffic, agents, aht_seconds, target_seconds):
    pw = erlang_c(traffic, agents)
    exponent = -(agents - traffic) * (target_seconds / aht_seconds)
    return 1 - (pw * math.exp(exponent))


def required_agents(calls, params):
    interval_seconds = 1800
    effective_calls = max(calls * (1 - params["nda"] / 100), 0)
    offered = (effective_calls * (params["aht"] + params["ata"])) / interval_seconds
    if offered <= 0:
        return 0

    agents = max(1, math.ceil(offered))
    sl_target = params["nds"] / 100
    while agents < 5000:
        occ = offered / agents
        sl = service_level(offered, agents, params["aht"] + params["ata"], params["nds_seconds"])
        asa = (erlang_c(offered, agents) * (params["aht"] + params["ata"])) / max(agents - offered, 1e-6)
        if occ <= params["occupancy"] / 100 and sl >= sl_target and asa <= params["asa"]:
            break
        agents += 1

    shrinkage = (params["absentismo"] + params["descanso"] + params["pausa_visual"]) / 100
    if shrinkage >= 0.95:
        shrinkage = 0.95
    productive = 1 - shrinkage
    return math.ceil(agents / productive)


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path: Path, ctype: str):
        if not path.exists():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            return self._serve_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
        if parsed.path == "/app.js":
            return self._serve_file(STATIC_DIR / "app.js", "application/javascript; charset=utf-8")
        if parsed.path == "/api/history":
            return self.handle_history(parsed)
        if parsed.path == "/api/forecast":
            return self.handle_forecast(parsed)
        self.send_error(404)

    def do_POST(self):
        if self.path == "/api/upload":
            return self.handle_upload()
        if self.path == "/api/fte":
            return self.handle_fte()
        self.send_error(404)

    def parse_multipart(self):
        content_type = self.headers.get("Content-Type", "")
        if "boundary=" not in content_type:
            raise ValueError("Multipart inválido")
        boundary = content_type.split("boundary=", 1)[1].encode()
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        parts = body.split(b"--" + boundary)
        for part in parts:
            if b"filename=" in part:
                header, file_data = part.split(b"\r\n\r\n", 1)
                disposition = header.decode(errors="ignore")
                filename = "archivo"
                if "filename=\"" in disposition:
                    filename = disposition.split("filename=\"", 1)[1].split("\"", 1)[0]
                return filename, file_data.rsplit(b"\r\n", 1)[0]
        raise ValueError("No se recibió archivo")

    def handle_upload(self):
        try:
            filename, file_bytes = self.parse_multipart()
            if filename.lower().endswith(".csv"):
                rows = read_csv_rows(file_bytes)
            elif filename.lower().endswith(".xlsx"):
                rows = read_xlsx_rows(file_bytes)
            else:
                raise ValueError("Solo se permite CSV o XLSX")

            conn = sqlite3.connect(DB_PATH)
            now = dt.datetime.utcnow().isoformat()
            cur = conn.execute(
                "INSERT INTO uploads(filename, created_at) VALUES (?, ?)",
                (filename, now),
            )
            upload_id = cur.lastrowid
            conn.executemany(
                "INSERT INTO call_data(upload_id, day, franja, calls) VALUES (?, ?, ?, ?)",
                [(upload_id, r["day"], r["franja"], r["calls"]) for r in rows],
            )
            forecasts = compute_forecast(rows)
            conn.executemany(
                "INSERT INTO forecasts(upload_id, day, franja, calls, model_version, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                [(upload_id, f["day"], f["franja"], f["calls"], "v1_weekly_trend", now) for f in forecasts],
            )
            conn.commit()
            conn.close()
            self._json({"ok": True, "rows": len(rows), "forecast_rows": len(forecasts), "upload_id": upload_id})
        except Exception as exc:
            self._json({"ok": False, "error": str(exc)}, status=400)

    def handle_history(self, parsed):
        params = parse_qs(parsed.query)
        start = params.get("start", ["0000-01-01"])[0]
        end = params.get("end", ["9999-12-31"])[0]
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT day, SUM(calls) as calls
            FROM call_data
            WHERE day BETWEEN ? AND ?
            GROUP BY day
            ORDER BY day
            """,
            (start, end),
        ).fetchall()
        conn.close()
        self._json([dict(r) for r in rows])

    def handle_forecast(self, parsed):
        params = parse_qs(parsed.query)
        start = params.get("start", ["0000-01-01"])[0]
        end = params.get("end", ["9999-12-31"])[0]
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT day, SUM(calls) as calls
            FROM forecasts
            WHERE day BETWEEN ? AND ?
            GROUP BY day
            ORDER BY day
            """,
            (start, end),
        ).fetchall()
        conn.close()
        self._json([dict(r) for r in rows])

    def handle_fte(self):
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        source = payload.get("source", "forecast")
        start = payload.get("start", "0000-01-01")
        end = payload.get("end", "9999-12-31")
        params = {
            "nda": float(payload.get("nda", 0)),
            "nds": float(payload.get("nds", 80)),
            "nds_seconds": float(payload.get("nds_seconds", 20)),
            "aht": float(payload.get("aht", 300)),
            "absentismo": float(payload.get("absentismo", 8)),
            "descanso": float(payload.get("descanso", 10)),
            "pausa_visual": float(payload.get("pausa_visual", 5)),
            "ata": float(payload.get("ata", 40)),
            "asa": float(payload.get("asa", 20)),
            "occupancy": float(payload.get("occupancy", 85)),
        }
        table = "forecasts" if source == "forecast" else "call_data"

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"""
            SELECT day, franja, SUM(calls) as calls
            FROM {table}
            WHERE day BETWEEN ? AND ?
            GROUP BY day, franja
            ORDER BY day, franja
            """,
            (start, end),
        ).fetchall()
        conn.close()

        details = []
        for r in rows:
            fte = required_agents(r["calls"], params)
            details.append({"day": r["day"], "franja": r["franja"], "calls": r["calls"], "fte": fte})

        peak = max((d["fte"] for d in details), default=0)
        avg = round(sum(d["fte"] for d in details) / len(details), 2) if details else 0
        self._json({"peak_fte": peak, "avg_fte": avg, "intervals": details})


def run():
    ensure_db()
    server = ThreadingHTTPServer(("127.0.0.1", 8080), Handler)
    print("Call Center Planner ejecutándose en http://127.0.0.1:8080")
    server.serve_forever()


if __name__ == "__main__":
    run()
