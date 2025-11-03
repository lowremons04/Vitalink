# FILE: backend/digit_recognition_backend.py

import sys
import json
import cv2
import imutils
from imutils import contours
import os
import numpy as np
import base64

# --- 7-segment recognition logic (Your proven version) ---
DIGITS_LOOKUP = {
	(1, 1, 1, 0, 1, 1, 1): 0,
	(0, 0, 1, 0, 0, 1, 0): 1,
	(1, 0, 1, 1, 1, 1, 0): 2,
	(1, 0, 1, 1, 0, 1, 1): 3,
	(0, 1, 1, 1, 0, 1, 0): 4,
	(1, 1, 0, 1, 0, 1, 1): 5,
	(1, 1, 0, 1, 1, 1, 1): 6,
	(1, 0, 1, 0, 0, 1, 0): 7,
	(1, 1, 1, 0, 0, 1, 0): 7,
	(1, 1, 1, 1, 1, 1, 1): 8,
	(1, 1, 1, 1, 0, 1, 1): 9
}

def process_image(image_path, crop_x, crop_y, crop_w, crop_h):
    try:
        full_image = cv2.imread(image_path)
        if full_image is None:
            print(json.dumps({"error": "Python script could not load image."}))
            return

        # --- Replicate the Original Scaling Logic ---
        (orig_h, orig_w) = full_image.shape[:2]
        resized_image = imutils.resize(full_image, height=500)
        (resized_h, resized_w) = resized_image.shape[:2]
        ratio = resized_h / float(orig_h)
        scaled_crop_x = int(crop_x * ratio)
        scaled_crop_y = int(crop_y * ratio)
        scaled_crop_w = int(crop_w * ratio)
        scaled_crop_h = int(crop_h * ratio)
        output_image = resized_image.copy()
        
        gray = cv2.cvtColor(resized_image, cv2.COLOR_BGR2GRAY)
        roi_gray = gray[scaled_crop_y : scaled_crop_y + scaled_crop_h, scaled_crop_x : scaled_crop_x + scaled_crop_w]

        # --- PREPROCESSING with CLAHE ---
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced_gray = clahe.apply(roi_gray)
        thresh = cv2.adaptiveThreshold(enhanced_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 21, 10)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # --- Find & Filter Contours ---
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        digitCnts = []
        for c in cnts:
            (x, y, w, h) = cv2.boundingRect(c)
            if h > 20 and (w / float(h) > 0.1 and w / float(h) < 1.0):
                digitCnts.append(c)

        if not digitCnts:
            print(json.dumps({"error": "No valid digit contours found."}))
            return

        # Sort all found contours from top-to-bottom.
        (digitCnts, boundingBoxes) = contours.sort_contours(digitCnts, method="top-to-bottom")
        
        # --- THE FINAL, ROBUST GROUPING LOGIC ---
        # This new algorithm correctly groups digits into lines, even with small tilts.
        grouped_contours = []
        current_line = []
        if not boundingBoxes:
            print(json.dumps({"error": "Sorting contours failed."}))
            return
            
        # Establish the vertical position of the first line
        first_y = boundingBoxes[0][1]
        
        for (c, (x, y, w, h_c)) in zip(digitCnts, boundingBoxes):
            # If the current digit is vertically "close" to the start of the current line, add it
            if y < first_y + h_c:
                current_line.append((c, (x, y, w, h_c)))
            else:
                # If it's far away, the previous line is complete. Sort it left-to-right.
                current_line.sort(key=lambda item: item[1][0])
                grouped_contours.append(current_line)
                
                # Start a new line with the current digit
                current_line = [(c, (x, y, w, h_c))]
                first_y = y # Update the anchor for the new line
        
        # Add the very last line to the groups
        current_line.sort(key=lambda item: item[1][0])
        grouped_contours.append(current_line)

        # --- Recognition Logic (now operates on the correctly grouped digits) ---
        final_readings = []
        for line in grouped_contours:
            line_digits = ""
            for (c, (x, y, w, h_c)) in line:
                aspect_ratio = w / float(h_c); digit = None
                if aspect_ratio < 0.4: digit = 1
                else:
                    roi = thresh[y:y+h_c, x:x+w]
                    on = [0] * 7
                    (roiH, roiW) = roi.shape
                    (dW, dH) = (int(roiW * 0.25), int(roiH * 0.15)); dHC = int(roiH * 0.05)
                    segments = [((0, 0), (w, dH)), ((0, 0), (dW, h_c // 2)), ((w - dW, 0), (w, h_c // 2)), ((0, (h_c // 2) - dHC) , (w, (h_c // 2) + dHC)), ((0, h_c // 2), (dW, h_c)), ((w - dW, h_c // 2), (w, h_c)), ((0, h_c - dH), (w, h_c))]
                    for (i, ((xA, yA), (xB, yB))) in enumerate(segments):
                        yA, yB, xA, xB = int(yA), int(yB), int(xA), int(xB)
                        if yA >= yB or xA >= xB: continue
                        segROI = roi[yA:yB, xA:xB]; total = cv2.countNonZero(segROI); area = (xB - xA) * (yB - yA)
                        if area > 0 and total / float(area) > 0.45: on[i] = 1
                    try: digit = DIGITS_LOOKUP[tuple(on)]
                    except KeyError: pass
                if digit is not None:
                    line_digits += str(digit)
                    final_x = x + scaled_crop_x
                    final_y = y + scaled_crop_y
                    cv2.rectangle(output_image, (final_x, final_y), (final_x + w, final_y + h_c), (0, 255, 0), 2)
                    cv2.putText(output_image, str(digit), (final_x - 10, final_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)
            final_readings.append(line_digits)

        _, buffer = cv2.imencode('.jpg', output_image)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        result = {
            "sys": final_readings[0] if len(final_readings) > 0 else "",
            "dia": final_readings[1] if len(final_readings) > 1 else "",
            "pulse": final_readings[2] if len(final_readings) > 2 else "",
            "annotatedImage": jpg_as_text
        }
        print(json.dumps(result))

    except Exception as e:
        import traceback
        error_message = f"Python script crashed: {e}\n{traceback.format_exc()}"
        print(json.dumps({"error": error_message}))

if __name__ == "__main__":
    if len(sys.argv) == 6:
        image_path = sys.argv[1]
        crop_x = int(sys.argv[2])
        crop_y = int(sys.argv[3])
        crop_w = int(sys.argv[4])
        crop_h = int(sys.argv[5])
        process_image(image_path, crop_x, crop_y, crop_w, crop_h)
    else:
        print(json.dumps({"error": "Incorrect number of arguments passed to Python script."}))