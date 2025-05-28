from flask import Flask, jsonify, Response
from flask_cors import CORS
import sqlite3
import cv2
from deepface import DeepFace
from retinaface import RetinaFace

app = Flask(__name__)
CORS(app)  # React에서 API 요청 허용
camera = cv2.VideoCapture(0)

# ✅ 분석 결과 저장 변수 (여러 인물)
age_data_list = []  # ✅ 여러 명의 분석 결과를 저장할 리스트

# ✅ SQLite3에서 광고 목록 가져오기 (독립 API)
@app.route('/api/ads')
def get_ads():
    conn = sqlite3.connect("Smartboard.db")
    cur = conn.cursor()
    cur.execute("SELECT ad_id, title, image_path FROM ad")
    rows = cur.fetchall()
    conn.close()
    ads = [{"ad_id": row[0], "title": row[1], "image_path": row[2]} for row in rows]
    return jsonify(ads)

# ✅ 웹캠 분석 함수 (독립 스레드)
def run_camera():
    global age_data_list, camera
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            try:
                # ✅ RetinaFace로 얼굴 검출
                results = RetinaFace.detect_faces(frame)
                current_data = []  # ✅ 현재 프레임의 얼굴 정보 저장

                for face_id in results:
                    face_info = results[face_id]
                    x1, y1, x2, y2 = face_info["facial_area"]

                    # ✅ 얼굴 잘라내기
                    face_img = frame[y1:y2, x1:x2]
                    if face_img.size == 0:
                        continue

                    # ✅ DeepFace 분석 (5초마다)
                    print("DeepFace 분석 시작...")
                    result = DeepFace.analyze(
                        face_img,
                        actions=["age", "gender"],
                        detector_backend="skip",
                        enforce_detection=False
                    )

                    # ✅ 현재 얼굴의 나이/성별 저장
                    analyzed_data = {
                        "age": int(result[0]["age"]),
                        "gender": result[0]["dominant_gender"]
                    }
                    current_data.append(analyzed_data)
                    print(f"Analyzed: Age: {analyzed_data['age']}, Gender: {analyzed_data['gender']}")

                # ✅ 전체 얼굴 데이터 업데이트 (스레드 안전)
                age_data_list = current_data

                # ✅ 프레임을 스트리밍으로 전달
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    
            except Exception as e:
                print("Error in DeepFace analysis:", e)

@app.route('/api/camera')
def video_feed():
    return Response(run_camera(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/analyze')
def get_analysis():
    return jsonify(age_data_list)  # ✅ 여러 명의 분석 결과 전달

if __name__ == "__main__":
    app.run(port=5000, debug=True)


