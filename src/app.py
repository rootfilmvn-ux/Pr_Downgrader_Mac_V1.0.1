import os, sys, re, gzip, socket, threading, subprocess
import webview
from flask import Flask, render_template, request, jsonify

if getattr(sys, 'frozen', False):
    TEMPLATE_FOLDER = os.path.join(sys._MEIPASS, 'templates')
else:
    TEMPLATE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
main_window = None

PREMIERE_VERSIONS = {
    "2025": "43",
    "2024": "42",
    "2023": "41",
    "2022": "40",
    "2021": "39",
    "2020": "38"
}

def read_prproj_xml(file_path):
    with open(file_path, "rb") as f:
        magic = f.read(2)
    if magic == b"\x1f\x8b":
        with gzip.open(file_path, "rb") as gz:
            return gz.read().decode("utf-8", errors="replace"), True
    else:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(), False

def detect_version_label(xml_text):
    m = re.search(r'<Project\b[^>]*\bVersion="(\d+)"', xml_text)
    if not m:
        return "Không rõ"
    ver = m.group(1)
    rev_map = {v: f"CC {k}" for k, v in PREMIERE_VERSIONS.items()}
    rev_map["44"] = "CC 2026"
    rev_map["45"] = "CC 2026+"
    return f"{rev_map.get(ver, 'Bản khác')} (Version {ver})"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/select_file", methods=["POST"])
def api_select_file():
    try:
        if main_window is not None:
            result = main_window.create_file_dialog(
                webview.OPEN_DIALOG,
                file_types=("Premiere Project (*.prproj)", "All files (*.*)")
            )
            if result and len(result) > 0:
                file_path = result[0]
                xml_text, _ = read_prproj_xml(file_path)
                ver_label = detect_version_label(xml_text)
                return jsonify({
                    "status": "ok",
                    "file_path": file_path,
                    "file_name": os.path.basename(file_path),
                    "detected_version": ver_label
                })
    except Exception as e:
        return jsonify({"error": f"Không thể đọc file: {str(e)}"}), 500
    return jsonify({"status": "cancelled"})

@app.route("/api/convert", methods=["POST"])
def api_convert():
    data = request.json or {}
    file_path = data.get("file_path", "").strip()
    target_year = str(data.get("year", "")).strip()

    if not file_path or not os.path.exists(file_path):
        return jsonify({"error": "Vui lòng chọn file .prproj hợp lệ trước!"}), 400
    if target_year not in PREMIERE_VERSIONS:
        return jsonify({"error": "Phiên bản năm không hợp lệ!"}), 400

    target_ver = PREMIERE_VERSIONS[target_year]
    try:
        xml_text, is_gzip = read_prproj_xml(file_path)
        new_xml, count = re.subn(
            r'(<Project\b[^>]*\bVersion=")(\d+)(")',
            rf'\g<1>{target_ver}\g<3>',
            xml_text,
            count=1
        )
        if count == 0:
            return jsonify({"error": "Không tìm thấy thẻ Version bên trong file .prproj này!"}), 400

        folder = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        out_name = f"{base_name}_CC{target_year}.prproj"
        out_path = os.path.join(folder, out_name)

        if is_gzip:
            with gzip.open(out_path, "wb") as gz:
                gz.write(new_xml.encode("utf-8"))
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(new_xml)

        return jsonify({
            "status": "ok",
            "out_path": out_path,
            "out_name": out_name,
            "folder": folder
        })
    except Exception as e:
        return jsonify({"error": f"Lỗi chuyển đổi: {str(e)}"}), 500

@app.route("/api/open_folder", methods=["POST"])
def api_open_folder():
    folder = (request.json or {}).get("folder", "")
    if folder and os.path.exists(folder):
        subprocess.run(["open", folder], check=False)
    return jsonify({"status": "ok"})

def find_safe_port():
    for p in [5077, 5078, 5079, 5080]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return 5077

SAFE_PORT = find_safe_port()

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="127.0.0.1", port=SAFE_PORT, threaded=True), daemon=True).start()
    main_window = webview.create_window(
        "ROOT FILM - Premiere Project Downgrader V1.0.1",
        f"http://127.0.0.1:{SAFE_PORT}",
        width=740,
        height=580,
        resizable=False
    )
    webview.start()
    os._exit(0)