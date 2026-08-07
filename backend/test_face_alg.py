import cv2
import numpy as np
import torch
import torch.nn as nn
import os

print("Testing face recognition pipeline with OpenCV + PyTorch...")

# 1. OpenCV Haar Cascades
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')

# Create synthetic Face A and Face B to test discrimination
def generate_synthetic_face(eye_dist=40, nose_len=30, mouth_w=50, skin_tone=180):
    img = np.ones((200, 200, 3), dtype=np.uint8) * skin_tone
    # Draw oval face boundary
    cv2.ellipse(img, (100, 100), (70, 90), 0, 0, 360, (50, 50, 50), 2)
    # Draw eyes
    lx = 100 - eye_dist // 2
    rx = 100 + eye_dist // 2
    cv2.circle(img, (lx, 70), 12, (30, 30, 30), -1)
    cv2.circle(img, (rx, 70), 12, (30, 30, 30), -1)
    # Draw nose
    cv2.line(img, (100, 75), (100, 75 + nose_len), (40, 40, 40), 3)
    # Draw mouth
    cv2.rectangle(img, (100 - mouth_w//2, 140), (100 + mouth_w//2, 150), (40, 40, 40), -1)
    return img

face_A1 = generate_synthetic_face(eye_dist=40, nose_len=30, mouth_w=50, skin_tone=180)
face_A2 = generate_synthetic_face(eye_dist=42, nose_len=29, mouth_w=48, skin_tone=170) # Same face, slightly different frame
face_B  = generate_synthetic_face(eye_dist=60, nose_len=45, mouth_w=70, skin_tone=130) # Different face structure

# LBP Feature Extractor
def extract_lbp(gray_crop):
    h, w = gray_crop.shape
    # Equalize illumination
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))
    norm_img = clahe.apply(gray_crop)
    
    # Simple LBP implementation
    padded = np.pad(norm_img, 1, mode='edge')
    center = padded[1:-1, 1:-1]
    lbp = np.zeros_like(center, dtype=np.uint8)
    offsets = [(-1,-1), (-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1)]
    for bit, (dy, dx) in enumerate(offsets):
        neighbor = padded[1+dy:h+1+dy, 1+dx:w+1+dx]
        lbp |= ((neighbor >= center).astype(np.uint8) << bit)
    
    # 4x4 spatial grid histogram
    hist_list = []
    gh, gw = h // 4, w // 4
    for r in range(4):
        for c in range(4):
            block = lbp[r*gh:(r+1)*gh, c*gw:(c+1)*gw]
            hist, _ = np.histogram(block.ravel(), bins=16, range=(0, 256))
            hist_list.extend(hist.astype(np.float32))
            
    vec = np.array(hist_list, dtype=np.float32)
    # L2 normalize
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec

def get_face_embedding(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 3)
    if len(faces) == 0:
        # Fallback to cropping center if Haar misses synthetic image
        h, w = gray.shape
        face_roi = gray[20:180, 20:180]
    else:
        x, y, w, h = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        
    face_roi = cv2.resize(face_roi, (128, 128))
    lbp_vec = extract_lbp(face_roi)
    
    # Pad to 512-dim
    embedding = np.zeros(512, dtype=np.float32)
    embedding[:len(lbp_vec)] = lbp_vec
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding /= norm
    return embedding

emb_A1 = get_face_embedding(face_A1)
emb_A2 = get_face_embedding(face_A2)
emb_B  = get_face_embedding(face_B)

sim_A1_A2 = np.dot(emb_A1, emb_A2)
sim_A1_B  = np.dot(emb_A1, emb_B)

print(f"Similarity (Same Person A1 vs A2): {sim_A1_A2:.4f}")
print(f"Similarity (Different Person A1 vs B): {sim_A1_B:.4f}")
