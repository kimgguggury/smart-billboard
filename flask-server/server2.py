from flask import Flask, jsonify, Response, request,session 
from flask_cors import CORS
import os
import json
import sqlite3
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_super_secret_key"  # 아무 문자열이나 OK (보안 중요 X이면 간단히)
CORS(app, supports_credentials=True)      # ✅ 쿠키 전송 가능하게 만듦
CAPTURE_FOLDER = "captured_images"
analysis_result_path = os.path.join(CAPTURE_FOLDER, "analysis_result.json")
UPLOAD_FOLDER = os.path.join("static", "uploads")

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
            #먼저 연령과 성별에 해당하는 게 있는 지 확인하는 부분
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

# 🔐 회원가입 API
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    company = data.get('company')

    if not email or not password or not company:
        return jsonify({"message": "모든 필드를 입력해야 합니다."}), 400

    try:
        conn = sqlite3.connect("Smartboard.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (email, password, company) VALUES (?, ?, ?)",
            (email, password, company)
        )
        conn.commit()
        return jsonify({"message": "회원가입 성공"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"message": "이미 존재하는 이메일입니다."}), 400
    finally:
        conn.close()


# 🔓 로그인 API
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "이메일과 비밀번호는 필수입니다."}), 400

    conn = sqlite3.connect("Smartboard.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        # 로그인 성공 → 세션에 저장
        from flask import session
        session['user'] = email
        return jsonify({"message": "로그인 성공", "email": email}), 200
    else:
        return jsonify({"message": "이메일 또는 비밀번호 오류"}), 401

# 🔍 로그인 상태 확인
@app.route("/api/check", methods=["GET"])
def check_login():
    from flask import session
    if 'user' in session:
        return jsonify({"loggedIn": True, "email": session["user"]})
    else:
        return jsonify({"loggedIn": False})

# 🔒 로그아웃
@app.route("/api/logout", methods=["POST"])
def logout():
    from flask import session
    session.pop("user", None)
    return jsonify({"message": "로그아웃 완료"})



UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/create_ad', methods=['POST'])
def create_ad():
    try:
        print("📦 받은 데이터:", request.form.get("title"), request.form.get("target_sex"), request.form.get("target_age"), session.get("user"))

        if 'image' not in request.files:
            return jsonify({"message": "이미지 파일이 없습니다."}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({"message": "파일명이 비어 있습니다."}), 400

        if not allowed_file(file.filename):
            return jsonify({"message": "허용되지 않는 파일 형식입니다."}), 400

        title = request.form.get('title')
        target_sex = request.form.get('target_sex')
        target_age = request.form.get('target_age')
        user_email = session.get('user')

        if not title or not target_sex or not target_age:
            return jsonify({"message": "모든 필드를 채워야 합니다."}), 400
        if not user_email:
            return jsonify({"message": "로그인이 필요합니다."}), 401

        conn = sqlite3.connect("Smartboard.db")
        cursor = conn.cursor()

        # 사용자 ID 조회
        cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
        user_row = cursor.fetchone()

        if not user_row:
            print("❌ 사용자 없음:", user_email)
            return jsonify({"message": "사용자 정보를 찾을 수 없습니다."}), 400

        user_id = user_row[0]

       # 파일 저장 경로 (static/uploads/파일명)
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # DB에는 static/를 빼고 상대경로만 저장
        image_path_for_db = f"uploads/{filename}"

        cursor.execute("""
            INSERT INTO ad (title, image_path, target_sex, target_age, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, (title, image_path_for_db, target_sex, target_age, user_id))
        conn.commit()

        print(f"✅ 광고 등록 완료: {title} by {user_email}")
        return jsonify({"message": "광고 등록 완료"}), 201

    except Exception as e:
        print("❌ 예외 발생:", str(e))
        return jsonify({"message": "서버 오류 발생", "error": str(e)}), 500
    finally:
        conn.close()


@app.route('/api/my-ads', methods=['GET'])
def get_my_ads():
    user_email = session.get('user')
    if not user_email:
        return jsonify({"message": "로그인이 필요합니다."}), 401
    conn = sqlite3.connect("Smartboard.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({"message": "사용자 정보를 찾을 수 없습니다."}), 400
    user_id = user_row[0]
    cursor.execute(
        "SELECT ad_id, title, image_path, target_sex, target_age FROM ad WHERE user_id = ?",
        (user_id,)
    )
    rows = cursor.fetchall()
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

@app.route('/api/ad/<int:ad_id>', methods=['PUT'])
def update_ad(ad_id):
    user_email = session.get('user')
    if not user_email:
        return jsonify({"message": "로그인이 필요합니다."}), 401
    conn = sqlite3.connect("Smartboard.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({"message": "사용자 정보를 찾을 수 없습니다."}), 400
    user_id = user_row[0]

    cursor.execute("SELECT user_id FROM ad WHERE ad_id = ?", (ad_id,))
    ad_owner = cursor.fetchone()

    if not ad_owner or int(ad_owner[0]) != int(user_id):  # ← 이렇게 고쳐야 안전!
        conn.close()
        return jsonify({"message": "권한이 없습니다."}), 403
    try:
        title = request.form.get('title')
        target_sex = request.form.get('target_sex')
        target_age = request.form.get('target_age')
        if not title or not target_sex or not target_age:
            return jsonify({"message": "모든 필드를 채워야 합니다."}), 400
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                image_path_for_db = f"uploads/{filename}"
                cursor.execute("""
                    UPDATE ad SET title = ?, target_sex = ?, target_age = ?, image_path = ?
                    WHERE ad_id = ?
                """, (title, target_sex, target_age, image_path_for_db, ad_id))
            else:
                return jsonify({"message": "잘못된 이미지 파일입니다."}), 400
        else:
            cursor.execute("""
                UPDATE ad SET title = ?, target_sex = ?, target_age = ?
                WHERE ad_id = ?
            """, (title, target_sex, target_age, ad_id))
        conn.commit()
        return jsonify({"message": "광고 수정 완료"})
    except Exception as e:
        return jsonify({"message": "서버 오류 발생", "error": str(e)}), 500
    finally:
        conn.close()
@app.route('/api/ad/<int:ad_id>', methods=['DELETE'])
def delete_ad(ad_id):
    user_email = session.get('user')
    if not user_email:
        return jsonify({"message": "로그인이 필요합니다."}), 401

    conn = sqlite3.connect("Smartboard.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        return jsonify({"message": "사용자 정보 없음"}), 400
    user_id = user_row[0]

    cursor.execute("SELECT user_id FROM ad WHERE ad_id = ?", (ad_id,))
    ad_row = cursor.fetchone()
    if not ad_row or int(ad_row[0]) != int(user_id):
        conn.close()
        return jsonify({"message": "권한 없음"}), 403

    cursor.execute("DELETE FROM ad WHERE ad_id = ?", (ad_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "삭제 완료"}), 200


@app.route("/api/ad-view-by-age-gender/<int:ad_id>", methods=["GET"])
def get_ad_view_by_age_and_gender(ad_id):
    conn = sqlite3.connect("Smartboard.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT sex, age_group, view_count
        FROM ad_stats
        WHERE ad_id = ?
    """, (ad_id,))
    rows = cursor.fetchall()
    conn.close()

    # 기본 구조 생성: {'M': [0, 0, ..., 0], 'W': [0, ..., 0]}
    result = {'M': [0]*7, 'W': [0]*7}
    for sex, age_group, count in rows:
        if sex in result and 0 <= age_group <= 6:
            result[sex][age_group] = count

    return jsonify(result)


# ✅ 서버 실행
if __name__ == "__main__":
    app.run(port=5000, debug=True)

