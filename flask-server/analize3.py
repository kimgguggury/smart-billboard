import cv2
import time
import os
import json
import requests
from deepface import DeepFace
from retinaface import RetinaFace
import dlib
import numpy as np

# 파일 경로 설정
CAPTURE_FOLDER = "captured_images"
os.makedirs(CAPTURE_FOLDER, exist_ok=True)
analysis_result_path = os.path.join(CAPTURE_FOLDER, "analysis_result.json")
current_ad_path = "current_ad.json"  # 현재 광고 ID 파일

# dlib 각위 검색기 및 랜드링 클래스 로드해서 보유

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

def get_current_ad_id():
    try:
        with open(current_ad_path, "r", encoding="utf-8") as f:
            return json.load(f).get("ad_id")
    except:
        print("❌ current_ad.json 파일 없음")
        return None

def analyze_image():
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("❌ 카메라 열 수 없음")
        return

    print("✅ 시작: 열 번째 고급시 검사")

    try:
        while True:
            success, frame = camera.read()
            if not success:
                print("❌ 카메라 프매임 읽을 수 없음")
                time.sleep(1)
                continue

            # 1. DeepFace + RetinaFace 추적
            results = RetinaFace.detect_faces(frame)
            current_data = []

            for face_id in results:
                face_info = results[face_id]
                x1, y1, x2, y2 = face_info["facial_area"]
                face_img = frame[y1:y2, x1:x2]
                if face_img.size == 0:
                    continue
                try:
                    result = DeepFace.analyze(
                        face_img,
                        actions=["age", "gender"],
                        detector_backend="skip",
                        enforce_detection=False
                    )
                    analyzed_data = {
                        "age": int(result[0]["age"]),
                        "gender": result[0]["dominant_gender"]
                    }
                    current_data.append(analyzed_data)
                except Exception as e:
                    print("❌ DeepFace 분석 오류:", e)

            # 2. 결과 저장
            with open(analysis_result_path, "w", encoding="utf-8") as json_file:
                json.dump(current_data, json_file, ensure_ascii=False, indent=4)
            print(f"✅ 분석 결과 저장 완료: {analysis_result_path}")

            # 3. 정면이면 analyze_view
            print("🕒 15초 대기 후 시선 판단")
            time.sleep(7)
            analyze_view(camera)
            time.sleep(7)

    finally:
        camera.release()
        print("✅ 카메라 해제")

def analyze_view(camera):
    success, frame = camera.read()
    if not success:
        print("❌ 카메라 프매임 읽기 실패 (view)")
        return

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    view_data = []

    for face in faces:
        shape = predictor(gray, face)
        image_points = np.array([
            (shape.part(30).x, shape.part(30).y),
            (shape.part(8).x, shape.part(8).y),
            (shape.part(36).x, shape.part(36).y),
            (shape.part(45).x, shape.part(45).y),
            (shape.part(48).x, shape.part(48).y),
            (shape.part(54).x, shape.part(54).y)
        ], dtype="double")

        model_points = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -330.0, -65.0),
            (-225.0, 170.0, -135.0),
            (225.0, 170.0, -135.0),
            (-150.0, -150.0, -125.0),
            (150.0, -150.0, -125.0)
        ])

        size = frame.shape
        focal_length = size[1]
        center = (size[1] / 2, size[0] / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")
        dist_coeffs = np.zeros((4, 1))

        success, rotation_vector, translation_vector = cv2.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )

        rvec_matrix, _ = cv2.Rodrigues(rotation_vector)
        proj_matrix = np.hstack((rvec_matrix, translation_vector))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)

        pitch, yaw, roll = [angle[0] for angle in euler_angles]
        if pitch > 90: pitch = 180 - pitch
        elif pitch < -90: pitch = -180 - pitch

        print(f"Yaw: {yaw:.2f}, Pitch: {pitch:.2f}")

        if -20 <= yaw <= 20 and -15 <= pitch <= 15:
            print("✅ 정면임 - 분석 시작")
            x, y, w, h = face.left(), face.top(), face.width(), face.height()
            face_img = frame[y:y+h, x:x+w]
            try:
                result = DeepFace.analyze(face_img, actions=["age", "gender"], enforce_detection=False)
                view_data.append({
                    "age": int(result[0]["age"]),
                    "gender": result[0]["dominant_gender"]
                })
            except Exception as e:
                print("❌ DeepFace 분석 오류 (view):", e)
        else:
            print("❌ 안봄")

    # ✅ 서버로 view 정보 전송
    ad_id = get_current_ad_id()
    if ad_id and view_data:
        try:
            response = requests.post(
                "http://localhost:5000/api/viewed",
                json={"ad_id": ad_id, "people": view_data}
            )
            print("📡 view 전송 완료:", response.status_code, response.text)
        except Exception as e:
            print("❌ 서버 전송 실패:", e)
    else:
        print("❌ 정면 없음 또는 광고 ID 없음")

if __name__ == "__main__":
    analyze_image()
