from flask import Flask, jsonify, Response, request
from flask_cors import CORS
import os
import json
import sqlite3
import time

app = Flask(__name__)
CORS(app)

CAPTURE_FOLDER = "captured_images"
analysis_result_path = os.path.join(CAPTURE_FOLDER, "analysis_result.json")

# ✅ SSE: 실시간 분석 결과 스트리밍
@app.route('/api/analyze-stream')
def stream_analyze():
    def stream():
        last_data = None
        while True:
            time.sleep(1)
            if not os.path.exists(analysis_result_path):
                continue

            with open(analysis_result_path, "r") as json_file:
                current_data = json.load(json_file)

            if current_data != last_data:
                last_data = current_data
                yield f"data: {json.dumps(current_data)}\n\n"

    return Response(stream(), content_type="text/event-stream")

# ✅ 광고 목록 제공 API
@app.route('/api/ads')
def get_ads():
    conn = sqlite3.connect("Smartboard.db")
    cur = conn.cursor()
    cur.execute("SELECT ad_id, title, image_path, target_sex, target_age FROM ad")
    rows = cur.fetchall()
    conn.close()

    ads = [
        {
            "ad_id": row[0],
            "title": row[1],
            "image_path": row[2],
            "target_sex": row[3],
            "target_age": row[4]
        }
        for row in rows
    ]
    return jsonify(ads)

# ✅ 광고 정면 시청 시 view_count 업데이트 API
@app.route('/api/viewed', methods=['POST'])
def update_view_count():
    data = request.get_json()
    ad_id = data.get("ad_id")
    people = data.get("people", [])

    if not ad_id or not isinstance(people, list):
        return jsonify({"message": "Invalid data"}), 400

    try:
        conn = sqlite3.connect("Smartboard.db", timeout=10)
        cursor = conn.cursor()

        for person in people:
            age = person.get("age")
            gender = person.get("gender")
            if age is None or gender is None:
                continue

            # 성별 M/W 변환
            sex = "M" if gender.lower().startswith("m") else "W"
            age_group = min(int(age) // 10, 6)  # 최대 60대까지, 70대 이상도 6에 포함

            # view_count 업데이트 (sex, age_group 컬럼 기반)
            cursor.execute(
                "SELECT view_count FROM ad_stats WHERE ad_id = ? AND sex = ? AND age_group = ?",
                (ad_id, sex, age_group)
            )
            result = cursor.fetchone()

            if result:
                cursor.execute(
                    "UPDATE ad_stats SET view_count = view_count + 1 WHERE ad_id = ? AND sex = ? AND age_group = ?",
                    (ad_id, sex, age_group)
                )
            else:
                cursor.execute(
                    "INSERT INTO ad_stats (ad_id, sex, age_group, view_count) VALUES (?, ?, ?, ?)",
                    (ad_id, sex, age_group, 1)
                )

        conn.commit()
        print(f"✅ 광고 {ad_id} → 총 {len(people)}명 view_count 반영 완료")
        return jsonify({"message": f"View count updated: +{len(people)}", "ad_id": ad_id})

    except sqlite3.OperationalError as e:
        return jsonify({"error": "Database is locked", "details": str(e)}), 500

    finally:
        conn.close()

@app.route('/api/current-ad', methods=['POST'])
def update_current_ad():
    data = request.get_json()
    ad_id = data.get("ad_id")
    
    if not ad_id:
        return jsonify({"error": "Missing ad_id"}), 400
    
    # JSON 저장 경로 (Flask 기준)
    with open("current_ad.json", "w", encoding="utf-8") as f:
        json.dump({"ad_id": ad_id}, f, ensure_ascii=False, indent=2)
    
    return jsonify({"message": f"Current ad_id updated to {ad_id}"}), 200


# ✅ 서버 실행
if __name__ == "__main__":
    app.run(port=5000, debug=True)

