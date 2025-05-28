import bz2
with bz2.open("shape_predictor_68_face_landmarks.dat.bz2", "rb") as f_in:
    with open("shape_predictor_68_face_landmarks.dat", "wb") as f_out:
        f_out.write(f_in.read())