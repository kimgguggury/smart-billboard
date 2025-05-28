#이거는 광고 송출하는 기능만 있는거야 건들면 ㅈ돼
import cv2
import time
import os
import json
from deepface import DeepFace
from retinaface import RetinaFace
import dlib

CAPTURE_FOLDER = "captured_images"
os.makedirs(CAPTURE_FOLDER, exist_ok=True)  # ✅ JSON 파일 저장 폴더 생성
analysis_result_path = os.path.join(CAPTURE_FOLDER, "analysis_result.json")
view_analysis_result_path = os.path.join(CAPTURE_FOLDER, "view_analysis_result.json")
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

def analyze_image():
    camera = cv2.VideoCapture(0)
    while True:
        success, frame = camera.read()
        if not success:
            print("카메라에서 프레임을 읽을 수 없습니다.")
            continue

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

            # ✅ DeepFace 분석
            try:
                print("DeepFace 분석 시작...")
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
                print("DeepFace 분석 오류:", e)

        # ✅ 분석 결과 콘솔에 출력
        if current_data:
            print("\n✅ 분석 결과:")
            for person in current_data:
                print(f"  - Age: {person['age']}, Gender: {person['gender']}")
        else:
            print("\n❌ 얼굴을 감지하지 못했습니다.")

        # ✅ 분석 결과를 JSON 파일에 저장
        with open(analysis_result_path, "w", encoding="utf-8") as json_file:
            json.dump(current_data, json_file, ensure_ascii=False, indent=4)
        print(f"\n✅ 분석 결과 JSON 파일에 저장: {analysis_result_path}")

        # ✅ 5초 대기
        time.sleep(5)

    

if __name__ == "__main__":
    print("5초마다 자동으로 분석 결과 JSON 파일에 저장...")
    analyze_image()
