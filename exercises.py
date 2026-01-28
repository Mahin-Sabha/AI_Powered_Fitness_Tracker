import numpy as np

def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    return np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))

class ExerciseLogic:
    def __init__(self):
        self.count = 0
        self.stage = None
        self.feedback = "Correct Form"

    def detect_form(self, landmarks):
        # To be overridden by subclasses
        return True

    def count_reps(self, landmarks):
        # To be overridden by subclasses
        pass

    def give_feedback(self):
        return self.feedback

class DumbbellHighCurl(ExerciseLogic):
    def detect_form(self, landmarks):
        # Check if elbows are at sides (elbow y close to shoulder y)
        shoulder = landmarks[12]
        elbow = landmarks[14]
        if abs(elbow.y - shoulder.y) < 0.1:  # Threshold for elbow position
            self.feedback = "Correct Form"
            return True
        else:
            self.feedback = "Incorrect Form"
            return False

    def count_reps(self, landmarks, form_correct):
        if not form_correct:
            return  # Do not count reps if form is incorrect
        shoulder = landmarks[12]
        elbow = landmarks[14]
        wrist = landmarks[16]
        angle = calculate_angle(shoulder, elbow, wrist)

        if angle > 160:
            self.stage = "down"
        if self.stage == "down" and angle < 45:
            self.stage = "up"
            self.count += 1

class LateralRaise(ExerciseLogic):
    def detect_form(self, landmarks):
        shoulder = landmarks[12]  # Right shoulder
        elbow = landmarks[14]
        hip = landmarks[24]

        angle = calculate_angle(elbow, shoulder, hip)

        # Correct if arm is raised sideways (not forward)
        if angle > 30:
            self.feedback = "Correct Form"
            return True
        else:
            self.feedback = "Incorrect Form"
            return False

    def count_reps(self, landmarks, form_correct):
        if not form_correct:
            return

        shoulder = landmarks[12]
        elbow = landmarks[14]
        hip = landmarks[24]
        angle = calculate_angle(elbow, shoulder, hip)

        # Initialize stage
        if self.stage is None:
            self.stage = "down" if angle < 40 else "up"

        # Rep logic
        if self.stage == "down" and angle > 80:
            self.stage = "up"
            self.count += 1
        elif self.stage == "up" and angle < 40:
            self.stage = "down"

class HammerCurl(ExerciseLogic):
    def detect_form(self, landmarks):
        shoulder = landmarks[12]
        elbow = landmarks[14]
        wrist = landmarks[16]

        elbow_angle = calculate_angle(shoulder, elbow, wrist)

        # Elbow should stay near body & arm bending
        if elbow_angle < 160:
            self.feedback = "Correct Form"
            return True
        else:
            self.feedback = "Incorrect Form"
            return False

    def count_reps(self, landmarks, form_correct):
        if not form_correct:
            return

        shoulder = landmarks[12]
        elbow = landmarks[14]
        wrist = landmarks[16]
        angle = calculate_angle(shoulder, elbow, wrist)

        # Initialize stage
        if self.stage is None:
            self.stage = "down" if angle > 160 else "up"

        # Rep counting logic
        if self.stage == "down" and angle < 50:
            self.stage = "up"
            self.count += 1
        elif self.stage == "up" and angle > 160:
            self.stage = "down"
            
class FrontRaise(ExerciseLogic):
    def detect_form(self, landmarks):
        shoulder = landmarks[12]   # Right shoulder
        elbow = landmarks[14]
        hip = landmarks[24]

        angle = calculate_angle(elbow, shoulder, hip)

        # Correct if arm is lifted forward
        if angle > 20:
            self.feedback = "Correct Form"
            return True
        else:
            self.feedback = "Incorrect Form"
            return False

    def count_reps(self, landmarks, form_correct):
        if not form_correct:
            return

        shoulder = landmarks[12]
        elbow = landmarks[14]
        hip = landmarks[24]
        angle = calculate_angle(elbow, shoulder, hip)

        # Initialize stage
        if self.stage is None:
            self.stage = "down" if angle < 30 else "up"

        # Rep counting logic
        if self.stage == "down" and angle > 80:
            self.stage = "up"
            self.count += 1
        elif self.stage == "up" and angle < 30:
            self.stage = "down"

class StandingSideLegRaise(ExerciseLogic):
    def detect_form(self, landmarks):
        # Check if leg is raised sideways using hip angle
        shoulder = landmarks[12]  # Right shoulder
        hip = landmarks[24]  # Right hip
        ankle = landmarks[28]
        angle = calculate_angle(shoulder, hip, ankle)

        # Form correct if leg is raised (angle < 120 degrees, indicating leg is up)
        if angle < 120:
            self.feedback = "Correct Form"
            return True
        else:
            self.feedback = "Incorrect Form"
            return False

    def count_reps(self, landmarks, form_correct):
        if not form_correct:
            return

        shoulder = landmarks[12]
        hip = landmarks[24]
        ankle = landmarks[28]
        angle = calculate_angle(shoulder, hip, ankle)

        # Initialize stage
        if self.stage is None:
            self.stage = "down" if angle > 160 else "up"

        # Rep counting logic
        if self.stage == "down" and angle < 120:
            self.stage = "up"
            self.count += 1
        elif self.stage == "up" and angle > 160:
            self.stage = "down"
