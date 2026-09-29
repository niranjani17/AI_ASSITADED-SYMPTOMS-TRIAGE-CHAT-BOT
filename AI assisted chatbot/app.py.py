import sqlite3, time
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static")
DB, STAFF_PASS = "phc.db", "phc123"   # change the password

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

with db() as c:
    c.execute("""CREATE TABLE IF NOT EXISTS cases(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age_group TEXT, input_by TEXT,
        symptoms TEXT, duration TEXT, severity TEXT, level TEXT, reasons TEXT,
        status TEXT DEFAULT 'Waiting', created REAL)""")

EMERGENCY = {"chest", "breathing", "unconscious", "bleeding", "stroke", "seizure", "sos"}

def triage(s, duration, severity, age):
    s = set(s)
    red = sorted(s & EMERGENCY)
    if red:
        return "emergency", red                      # red-flag rule
    r = []
    if severity == "high": r.append("severe discomfort")
    if "fever" in s and duration in ("3-7d", "7d+"): r.append("fever 3+ days")
    if "fever" in s and age in ("child", "elder"): r.append("fever in child/elderly")
    if "vomiting" in s and severity != "low": r.append("persistent vomiting")
    if duration == "7d+": r.append("long duration")
    return ("urgent", r) if r else ("routine", ["mild symptoms"])

@app.route("/")
def home(): return send_from_directory("static", "index.html")

@app.route("/sw.js")
def sw(): return send_from_directory("static", "sw.js")

@app.route("/dashboard")
def dash(): return send_from_directory("static", "dashboard.html")

@app.post("/api/submit")
def submit():
    d = request.json
    level, reasons = triage(d.get("symptoms", []), d.get("duration"), d.get("severity"), d.get("age"))
    with db() as c:
        c.execute("INSERT INTO cases(name,age_group,input_by,symptoms,duration,severity,level,reasons,created) VALUES(?,?,?,?,?,?,?,?,?)",
                  (d.get("name") or "Anonymous", d.get("age"), d.get("who"), ",".join(d.get("symptoms", [])),
                   d.get("duration"), d.get("severity"), level, ", ".join(reasons), time.time()))
    return jsonify(level=level)

def auth(): return request.headers.get("X-Pass") == STAFF_PASS

@app.get("/api/cases")
def cases():
    if not auth(): return jsonify(error="unauthorized"), 401
    order = "CASE level WHEN 'emergency' THEN 0 WHEN 'urgent' THEN 1 ELSE 2 END, created"
    rows = db().execute(f"SELECT * FROM cases WHERE status!='Done' ORDER BY {order}").fetchall()
    return jsonify([dict(r) for r in rows])

@app.post("/api/cases/<int:i>/status")
def status(i):
    if not auth(): return jsonify(error="unauthorized"), 401
    with db() as c: c.execute("UPDATE cases SET status=? WHERE id=?", (request.json["status"], i))
    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)