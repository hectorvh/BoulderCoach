import cv2
import mediapipe as mp
import math
import argparse
import time
import requests
import csv
import os

# ---------- CONFIG ----------
ELBOW_EXTEND_THRESHOLD = 165.0
TORSO_ANGLE_THRESHOLD   = 20.0
HIP_DX_THRESHOLD        = 0.08
SMOOTHING_FRAMES        = 5
WEBHOOK_DEBOUNCE_SECS   = 6
# ----------------------------

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def angle_between(a, b, c):
    ab = (a[0]-b[0], a[1]-b[1])
    cb = (c[0]-b[0], c[1]-b[1])
    dot = ab[0]*cb[0] + ab[1]*cb[1]
    mag = math.hypot(*ab) * math.hypot(*cb)
    if mag == 0:
        return 0.0
    cosang = max(-1.0, min(1.0, dot/mag))
    return math.degrees(math.acos(cosang))

def midpoint(p1, p2):
    return ((p1[0]+p2[0])/2.0, (p1[1]+p2[1])/2.0)

def send_webhook(webhook_url, payload):
    try:
        r = requests.post(webhook_url, json=payload, timeout=2.5)
        print(f"[WEBHOOK] Sent: {payload} -> {r.status_code}")
    except Exception as e:
        print("[WEBHOOK] Error sending:", e)

def analyze_frame_landmarks(landmarks):
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    LEFT_KNEE = 25
    RIGHT_KNEE = 26
    LEFT_ELBOW = 13
    RIGHT_ELBOW = 14
    LEFT_WRIST = 15
    RIGHT_WRIST = 16

    def lm(i): return (landmarks[i].x, landmarks[i].y)

    left_shoulder = lm(LEFT_SHOULDER)
    right_shoulder = lm(RIGHT_SHOULDER)
    left_hip = lm(LEFT_HIP)
    right_hip = lm(RIGHT_HIP)
    left_wrist = lm(LEFT_WRIST)
    right_wrist = lm(RIGHT_WRIST)
    left_elbow = lm(LEFT_ELBOW)
    right_elbow = lm(RIGHT_ELBOW)

    shoulder_mid = midpoint(left_shoulder, right_shoulder)
    hip_mid = midpoint(left_hip, right_hip)

    torso_vec = (shoulder_mid[0] - hip_mid[0], shoulder_mid[1] - hip_mid[1])
    vertical_vec = (0.0, -1.0)
    dot = torso_vec[0]*vertical_vec[0] + torso_vec[1]*vertical_vec[1]
    mag = math.hypot(*torso_vec) * math.hypot(*vertical_vec)
    torso_angle = 0.0
    if mag != 0:
        torso_angle = math.degrees(math.acos(max(-1.0, min(1.0, dot/mag))))

    hip_dx_norm = abs(hip_mid[0] - shoulder_mid[0])
    left_elbow_angle = angle_between(left_shoulder, left_elbow, left_wrist)
    right_elbow_angle = angle_between(right_shoulder, right_elbow, right_wrist)

    return {
        "torso_angle": torso_angle,
        "hip_dx_norm": hip_dx_norm,
        "left_elbow_angle": left_elbow_angle,
        "right_elbow_angle": right_elbow_angle
    }

def main(args):
    src = args.source
    webhook = args.webhook_url

    # Abrir fuente de video
    cap = cv2.VideoCapture(0 if src.isdigit() and len(src) == 1 else src)
    if not cap.isOpened():
        print(f"[ERROR] No se pudo abrir la fuente: {src}")
        return
    else:
        print(f"[INFO] Fuente abierta correctamente: {src}")

    pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

    hip_counter = 0
    left_elbow_counter = 0
    right_elbow_counter = 0
    hip_flag = False
    left_elbow_flag = False
    right_elbow_flag = False
    last_webhook_time = {}

    csv_filename = "pose_issues_log.csv"
    with open(csv_filename, mode='w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Tiempo (s)", "Issue", "Torso Angle", "Hip DX Norm", "L Elbow Angle", "R Elbow Angle"])
    print(f"[INFO] Archivo CSV creado: {os.path.abspath(csv_filename)}")

    start_time = time.time()
    print("[INFO] Procesando video... Presiona 'q' para salir.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("[INFO] Fin del video o error de lectura.")
            break

        elapsed_time = time.time() - start_time
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        issues = []

        if results.pose_landmarks:
            info = analyze_frame_landmarks(results.pose_landmarks.landmark)

            hip_issue = (info["torso_angle"] > TORSO_ANGLE_THRESHOLD) or (info["hip_dx_norm"] > HIP_DX_THRESHOLD)
            left_elbow_issue = info["left_elbow_angle"] > ELBOW_EXTEND_THRESHOLD
            right_elbow_issue = info["right_elbow_angle"] > ELBOW_EXTEND_THRESHOLD

            hip_counter = hip_counter + 1 if hip_issue else 0
            left_elbow_counter = left_elbow_counter + 1 if left_elbow_issue else 0
            right_elbow_counter = right_elbow_counter + 1 if right_elbow_issue else 0

            if hip_counter >= SMOOTHING_FRAMES and not hip_flag:
                hip_flag = True
                issues.append(("hips_away", info))
            if left_elbow_counter >= SMOOTHING_FRAMES and not left_elbow_flag:
                left_elbow_flag = True
                issues.append(("left_elbow_overextend", info))
            if right_elbow_counter >= SMOOTHING_FRAMES and not right_elbow_flag:
                right_elbow_flag = True
                issues.append(("right_elbow_overextend", info))

            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            cv2.putText(frame, f"Tiempo: {elapsed_time:.2f}s", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Guardar issues detectados
            for issue_name, dat in issues:
                print(f"[DETECCION] {issue_name} en {elapsed_time:.2f}s")
                with open(csv_filename, mode='a', newline='') as csvfile:
                    csv_writer = csv.writer(csvfile)
                    csv_writer.writerow([
                        f"{elapsed_time:.2f}",
                        issue_name,
                        f"{dat['torso_angle']:.2f}",
                        f"{dat['hip_dx_norm']:.4f}",
                        f"{dat['left_elbow_angle']:.2f}",
                        f"{dat['right_elbow_angle']:.2f}"
                    ])

                now = time.time()
                last = last_webhook_time.get(issue_name, 0)
                if webhook and (now - last) > WEBHOOK_DEBOUNCE_SECS:
                    payload = {
                        "issue": issue_name,
                        "timestamp": now,
                        "video_time_seconds": elapsed_time,
                        "values": dat
                    }
                    send_webhook(webhook, payload)
                    last_webhook_time[issue_name] = now

        cv2.imshow('Pose Analyzer', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=str, default='0')
    parser.add_argument('--webhook_url', type=str, default='')
    args = parser.parse_args()
    main(args)