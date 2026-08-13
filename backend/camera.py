import cv2
import mediapipe as mp
import math
import time
import ctypes
import pyautogui

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ============================================================
# FRIDAY AI - CAMERA + HAND GESTURE CONTROL
# ============================================================

MODEL_PATH = "hand_landmarker.task"


# ============================================================
# SETTINGS
# ============================================================

SEQUENCE_TIMEOUT = 2.5
THUMBS_CONFIRM_TIME = 0.40

# Cursor
SMOOTHING = 0.70
DEAD_ZONE = 2

# Camera margins
CAMERA_MARGIN_X = 0.10
CAMERA_MARGIN_Y = 0.10

# Swipe
SWIPE_DISTANCE = 0.18
SWIPE_TIME_LIMIT = 1.2

# Click cooldown
CLICK_COOLDOWN = 0.70

# Unlock/wake cooldown
WAKE_COOLDOWN = 2.0


# ============================================================
# SCREEN
# ============================================================

SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()


# ============================================================
# GESTURE STATE
# ============================================================

palm_detected = False
palm_time = 0.0

thumbs_start_time = None
lock_triggered = False


# ============================================================
# CURSOR STATE
# ============================================================

previous_x = None
previous_y = None


# ============================================================
# CLICK STATE
# ============================================================

last_click_time = 0.0


# ============================================================
# THREE-FINGER SWIPE STATE
# ============================================================

three_finger_active = False

three_finger_start_y = None
three_finger_start_time = None

last_wake_time = 0.0


# ============================================================
# DISTANCE
# ============================================================

def distance(a, b):
    return math.sqrt(
        (a.x - b.x) ** 2
        + (a.y - b.y) ** 2
        + (a.z - b.z) ** 2
    )


# ============================================================
# FINGER DETECTION
# ============================================================

def finger_extended(hand, tip, pip, mcp):

    wrist = hand[0]

    tip_distance = distance(
        hand[tip],
        wrist
    )

    pip_distance = distance(
        hand[pip],
        wrist
    )

    mcp_distance = distance(
        hand[mcp],
        wrist
    )

    return (
        tip_distance > pip_distance
        and tip_distance > mcp_distance
    )


# ============================================================
# GESTURE CLASSIFIER
# ============================================================

def classify_gesture(hand):

    index_up = finger_extended(
        hand,
        8,
        6,
        5
    )

    middle_up = finger_extended(
        hand,
        12,
        10,
        9
    )

    ring_up = finger_extended(
        hand,
        16,
        14,
        13
    )

    pinky_up = finger_extended(
        hand,
        20,
        18,
        17
    )

    fingers_up = sum([
        index_up,
        middle_up,
        ring_up,
        pinky_up
    ])


    # ========================================================
    # THUMB
    # ========================================================

    thumb_tip = hand[4]
    thumb_ip = hand[3]

    thumb_up = (
        thumb_tip.y < thumb_ip.y
    )


    # ========================================================
    # OPEN PALM
    # ========================================================

    if (
        index_up
        and middle_up
        and ring_up
        and pinky_up
    ):
        return "PALM"


    # ========================================================
    # THUMBS UP
    # ========================================================

    if (
        thumb_up
        and fingers_up == 0
    ):
        return "THUMBS UP"


    # ========================================================
    # FIST
    # ========================================================

    if fingers_up == 0:
        return "FIST"


    # ========================================================
    # ONE FINGER
    # ========================================================

    if (
        index_up
        and not middle_up
        and not ring_up
        and not pinky_up
    ):
        return "ONE"


    # ========================================================
    # TWO FINGERS
    # ========================================================

    if (
        index_up
        and middle_up
        and not ring_up
        and not pinky_up
    ):
        return "TWO"


    # ========================================================
    # THREE FINGERS
    # ========================================================

    if (
        index_up
        and middle_up
        and ring_up
        and not pinky_up
    ):
        return "THREE"


    return "UNKNOWN"


# ============================================================
# SAFE MOUSE MOVE
# ============================================================

def safe_move_mouse(x, y):

    try:

        pyautogui.moveTo(
            int(x),
            int(y),
            duration=0
        )

        return True

    except pyautogui.FailSafeException:

        print(
            "FRIDAY: Mouse safety corner detected."
        )

        return False


# ============================================================
# SAFE LEFT CLICK
# ============================================================

def safe_click():

    try:

        pyautogui.click()

        return True

    except pyautogui.FailSafeException:

        print(
            "FRIDAY: Mouse safety corner detected."
        )

        return False


# ============================================================
# SAFE WAKE / LOCK-SCREEN ACTION
# ============================================================

def wake_lock_screen():

    """
    Safely wakes/advances the Windows lock screen.

    IMPORTANT:
    This does NOT type or store a password/PIN.
    Windows authentication must be performed manually.
    """

    try:

        # Pressing a harmless key can wake/advance
        # the Windows lock screen.

        pyautogui.press("enter")

        return True

    except pyautogui.FailSafeException:

        print(
            "FRIDAY: Mouse safety corner detected."
        )

        return False


# ============================================================
# MEDIAPIPE SETUP
# ============================================================

base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1,
    min_hand_detection_confidence=0.6,
    min_hand_presence_confidence=0.6,
    min_tracking_confidence=0.7
)

detector = vision.HandLandmarker.create_from_options(
    options
)


# ============================================================
# CAMERA SETUP
# ============================================================

cap = cv2.VideoCapture(0)

cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    1280
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    720
)

cap.set(
    cv2.CAP_PROP_FPS,
    60
)


if not cap.isOpened():

    print(
        "ERROR: Could not open camera."
    )

    detector.close()

    raise SystemExit


# ============================================================
# START
# ============================================================

print()
print("==========================================")
print("        FRIDAY AI VISION SYSTEM")
print("==========================================")
print()
print("Camera started.")
print()
print("GESTURES")
print()
print("PALM -> THUMBS UP = LOCK PC")
print("ONE FINGER = MOVE MOUSE")
print("TWO FINGERS = LEFT CLICK")
print("THREE FINGERS + SWIPE UP = WAKE LOCK SCREEN")
print()
print("Password/PIN is NEVER stored or typed.")
print()
print("Cursor smoothing:", SMOOTHING)
print("Swipe distance:", SWIPE_DISTANCE)
print()
print("Press Q to quit.")
print("==========================================")
print()


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        success, frame = cap.read()


        if not success:

            print(
                "ERROR: Failed to read camera."
            )

            break


        # ====================================================
        # MIRROR CAMERA
        # ====================================================

        frame = cv2.flip(
            frame,
            1
        )


        # ====================================================
        # RGB
        # ====================================================

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        # ====================================================
        # MEDIAPIPE IMAGE
        # ====================================================

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )


        # ====================================================
        # DETECT HAND
        # ====================================================

        result = detector.detect(
            mp_image
        )


        gesture_text = "NO HAND"


        # ====================================================
        # HAND DETECTED
        # ====================================================

        if result.hand_landmarks:

            hand = result.hand_landmarks[0]

            gesture = classify_gesture(
                hand
            )

            gesture_text = gesture

            current_time = time.time()


            # =================================================
            # PALM -> THUMBS UP -> LOCK
            # =================================================

            if gesture == "PALM":

                palm_detected = True

                palm_time = current_time

                thumbs_start_time = None

                lock_triggered = False


            elif gesture == "THUMBS UP":

                if (
                    palm_detected
                    and
                    current_time - palm_time
                    <= SEQUENCE_TIMEOUT
                ):

                    if thumbs_start_time is None:

                        thumbs_start_time = (
                            current_time
                        )


                    thumbs_duration = (
                        current_time
                        - thumbs_start_time
                    )


                    cv2.putText(
                        frame,
                        "HOLD TO LOCK",
                        (20, 105),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2
                    )


                    if (
                        thumbs_duration
                        >= THUMBS_CONFIRM_TIME
                        and
                        not lock_triggered
                    ):

                        print()
                        print(
                            "FRIDAY: Palm -> Thumbs Up"
                        )

                        print(
                            "FRIDAY: Locking PC..."
                        )


                        lock_triggered = True

                        palm_detected = False

                        palm_time = 0.0

                        thumbs_start_time = None


                        # Lock Windows

                        ctypes.windll.user32.LockWorkStation()


                else:

                    thumbs_start_time = None


            # =================================================
            # PALM TIMEOUT
            # =================================================

            if (
                palm_detected
                and
                current_time - palm_time
                > SEQUENCE_TIMEOUT
            ):

                palm_detected = False

                palm_time = 0.0

                thumbs_start_time = None


            # =================================================
            # LOCK SEQUENCE STATUS
            # =================================================

            lock_sequence_active = (
                palm_detected
                or
                thumbs_start_time is not None
            )


            # =================================================
            # ONE FINGER = MOUSE
            # =================================================

            if (
                gesture == "ONE"
                and
                not lock_sequence_active
            ):

                index_tip = hand[8]


                camera_x = index_tip.x
                camera_y = index_tip.y


                # ---------------------------------------------
                # CAMERA MARGIN
                # ---------------------------------------------

                camera_x = (
                    camera_x
                    - CAMERA_MARGIN_X
                ) / (
                    1.0
                    - 2.0 * CAMERA_MARGIN_X
                )


                camera_y = (
                    camera_y
                    - CAMERA_MARGIN_Y
                ) / (
                    1.0
                    - 2.0 * CAMERA_MARGIN_Y
                )


                # ---------------------------------------------
                # CLAMP
                # ---------------------------------------------

                camera_x = max(
                    0.0,
                    min(
                        1.0,
                        camera_x
                    )
                )

                camera_y = max(
                    0.0,
                    min(
                        1.0,
                        camera_y
                    )
                )


                # ---------------------------------------------
                # SCREEN POSITION
                # ---------------------------------------------

                target_x = (
                    camera_x
                    * SCREEN_WIDTH
                )

                target_y = (
                    camera_y
                    * SCREEN_HEIGHT
                )


                # ---------------------------------------------
                # INITIALIZE
                # ---------------------------------------------

                if previous_x is None:

                    previous_x = target_x

                    previous_y = target_y


                # ---------------------------------------------
                # DIFFERENCE
                # ---------------------------------------------

                dx = (
                    target_x
                    - previous_x
                )

                dy = (
                    target_y
                    - previous_y
                )


                movement = math.sqrt(
                    dx * dx
                    + dy * dy
                )


                # ---------------------------------------------
                # DEAD ZONE
                # ---------------------------------------------

                if movement > DEAD_ZONE:

                    previous_x += (
                        dx
                        * SMOOTHING
                    )

                    previous_y += (
                        dy
                        * SMOOTHING
                    )


                    # -----------------------------------------
                    # SCREEN LIMIT
                    # -----------------------------------------

                    previous_x = max(
                        1,
                        min(
                            SCREEN_WIDTH - 1,
                            previous_x
                        )
                    )

                    previous_y = max(
                        1,
                        min(
                            SCREEN_HEIGHT - 1,
                            previous_y
                        )
                    )


                    # -----------------------------------------
                    # MOVE
                    # -----------------------------------------

                    safe_move_mouse(
                        previous_x,
                        previous_y
                    )


            else:

                previous_x = None
                previous_y = None


            # =================================================
            # TWO FINGERS = LEFT CLICK
            # =================================================

            if gesture == "TWO":

                if (
                    current_time
                    - last_click_time
                    >= CLICK_COOLDOWN
                ):

                    if safe_click():

                        print(
                            "FRIDAY: LEFT CLICK"
                        )

                    last_click_time = (
                        current_time
                    )


            # =================================================
            # THREE FINGERS = SWIPE UP
            # =================================================

            if gesture == "THREE":

                # ---------------------------------------------
                # START SWIPE
                # ---------------------------------------------

                if not three_finger_active:

                    three_finger_active = True

                    three_finger_start_y = (
                        hand[0].y
                    )

                    three_finger_start_time = (
                        current_time
                    )


                else:

                    current_y = hand[0].y


                    swipe_distance = (
                        three_finger_start_y
                        - current_y
                    )


                    swipe_time = (
                        current_time
                        - three_finger_start_time
                    )


                    # -----------------------------------------
                    # SWIPE UP
                    # -----------------------------------------

                    if (
                        swipe_distance
                        >= SWIPE_DISTANCE
                        and
                        swipe_time
                        <= SWIPE_TIME_LIMIT
                        and
                        current_time
                        - last_wake_time
                        >= WAKE_COOLDOWN
                    ):

                        print()
                        print(
                            "FRIDAY: THREE FINGER SWIPE UP"
                        )

                        print(
                            "FRIDAY: Waking lock screen..."
                        )


                        # Safe action only.
                        # No password or PIN is stored.
                        wake_lock_screen()


                        last_wake_time = (
                            current_time
                        )


                        # Reset swipe

                        three_finger_active = False

                        three_finger_start_y = None

                        three_finger_start_time = None


            else:

                # Reset three-finger tracking

                three_finger_active = False

                three_finger_start_y = None

                three_finger_start_time = None


            # =================================================
            # DRAW LANDMARKS
            # =================================================

            for landmark in hand:

                x = int(
                    landmark.x
                    * frame.shape[1]
                )

                y = int(
                    landmark.y
                    * frame.shape[0]
                )


                cv2.circle(
                    frame,
                    (x, y),
                    5,
                    (0, 255, 0),
                    -1
                )


            # =================================================
            # HAND CONNECTIONS
            # =================================================

            connections = [

                (0, 1),
                (1, 2),
                (2, 3),
                (3, 4),

                (0, 5),
                (5, 6),
                (6, 7),
                (7, 8),

                (5, 9),
                (9, 10),
                (10, 11),
                (11, 12),

                (9, 13),
                (13, 14),
                (14, 15),
                (15, 16),

                (13, 17),
                (17, 18),
                (18, 19),
                (19, 20),

                (0, 17)
            ]


            for start, end in connections:

                x1 = int(
                    hand[start].x
                    * frame.shape[1]
                )

                y1 = int(
                    hand[start].y
                    * frame.shape[0]
                )

                x2 = int(
                    hand[end].x
                    * frame.shape[1]
                )

                y2 = int(
                    hand[end].y
                    * frame.shape[0]
                )


                cv2.line(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )


            # =================================================
            # GESTURE LABEL
            # =================================================

            wrist_x = int(
                hand[0].x
                * frame.shape[1]
            )

            wrist_y = int(
                hand[0].y
                * frame.shape[0]
            )


            cv2.putText(
                frame,
                gesture,
                (
                    wrist_x - 50,
                    wrist_y - 30
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )


        else:

            # =================================================
            # NO HAND
            # =================================================

            previous_x = None
            previous_y = None

            three_finger_active = False

            three_finger_start_y = None

            three_finger_start_time = None


            # Palm timeout

            if palm_detected:

                if (
                    time.time()
                    - palm_time
                    > SEQUENCE_TIMEOUT
                ):

                    palm_detected = False

                    palm_time = 0.0

                    thumbs_start_time = None


        # ====================================================
        # STATUS BAR
        # ====================================================

        cv2.rectangle(
            frame,
            (0, 0),
            (
                frame.shape[1],
                75
            ),
            (0, 0, 0),
            -1
        )


        cv2.putText(
            frame,
            "FRIDAY VISION",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            "Gesture: "
            + gesture_text,
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2
        )


        # ====================================================
        # SHOW CAMERA
        # ====================================================

        cv2.imshow(
            "FRIDAY AI - Vision",
            frame
        )


        # ====================================================
        # QUIT
        # ====================================================

        key = cv2.waitKey(1) & 0xFF


        if key == ord("q"):

            break


except KeyboardInterrupt:

    print()

    print(
        "FRIDAY stopped by user."
    )


finally:

    cap.release()

    cv2.destroyAllWindows()

    detector.close()

    print()

    print(
        "FRIDAY camera stopped."
    )