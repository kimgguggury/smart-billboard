import cv2
from deepface import DeepFace
from retinaface import RetinaFace

cap = cv2.VideoCapture(0)
print("Webcam is running. Please look straight at the camera.")

while True:
    ret, frame = cap.read()
    ages = []
    if not ret:
        break

   
    # RetinaFace로 얼굴 검출 (결과는 딕셔너리)
    results = RetinaFace.detect_faces(frame)

    for face_id in results:
        face_info = results[face_id]
        x1, y1, x2, y2 = face_info["facial_area"]  # [x1, y1, x2, y2]

        # 얼굴 잘라내기
        face_img = frame[y1:y2, x1:x2]

        if face_img.size == 0:
            continue

        # DeepFace 분석
        result = DeepFace.analyze(
            face_img,
            actions=["age", "gender"],
            detector_backend="skip",
            enforce_detection=False
        )

        age = int(result[0]["age"])
        gender = result[0]["dominant_gender"]
        label = f"{gender}, {age}"

        print(age,gender)
        # 원본 프레임에 바운딩박스 + 텍스트 출력
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        ages.append(age//10)
   

    cv2.imshow("Smart Ad Board - Group Analysis", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Q pressed. Exiting...")
        break

cap.release()
cv2.destroyAllWindows()
