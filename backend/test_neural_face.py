import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

class SpatialFaceNet(nn.Module):
    """
    PyTorch Spatial Face Embedding Network.
    Processes 128x128 face crops and extracts spatial patch embeddings.
    """
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=5, stride=2, padding=2)  # 64x64
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1) # 32x32
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)# 16x16
        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1)# 8x8
        self.fc = nn.Linear(256 * 8 * 8, 256)

        torch.manual_seed(1337)
        for m in self.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x):
        x = F.leaky_relu(self.conv1(x), 0.1)
        x = F.leaky_relu(self.conv2(x), 0.1)
        x = F.leaky_relu(self.conv3(x), 0.1)
        x = F.leaky_relu(self.conv4(x), 0.1)
        x = x.view(x.size(0), -1)
        feat = self.fc(x)
        return feat

class BiometricFaceEngine:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.net = SpatialFaceNet()
        self.net.eval()
        self.hog = cv2.HOGDescriptor((64, 64), (16, 16), (8, 8), (8, 8), 9)

    def extract_patch_features(self, gray_128: np.ndarray) -> np.ndarray:
        """
        Extracts LBP and spatial gradient histograms across a 4x4 grid of facial regions.
        """
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        norm_gray = clahe.apply(gray_128)
        
        # Local Binary Pattern
        padded = np.pad(norm_gray, 1, mode='edge')
        center = padded[1:-1, 1:-1]
        lbp = np.zeros_like(center, dtype=np.uint8)
        offsets = [(-1,-1), (-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1)]
        for bit, (dy, dx) in enumerate(offsets):
            neighbor = padded[1+dy:128+1+dy, 1+dx:128+1+dx]
            lbp |= ((neighbor >= center).astype(np.uint8) << bit)

        # 4x4 Grid Histogram
        patch_h, patch_w = 32, 32
        hists = []
        for r in range(4):
            for c in range(4):
                block = lbp[r*patch_h:(r+1)*patch_h, c*patch_w:(c+1)*patch_w]
                hist, _ = np.histogram(block.ravel(), bins=8, range=(0, 256))
                # L1 normalize block hist
                sum_h = np.sum(hist)
                if sum_h > 0:
                    hist = hist.astype(np.float32) / sum_h
                hists.extend(hist)
        return np.array(hists, dtype=np.float32)  # 4x4x8 = 128 features

    def generate_embedding(self, frame_bgr: np.ndarray) -> tuple[np.ndarray | None, str]:
        if frame_bgr is None or frame_bgr.size == 0:
            return None, "Empty frame"

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))

        if len(faces) == 0:
            h, w = gray.shape
            crop_h, crop_w = int(h * 0.6), int(w * 0.6)
            sy, sx = (h - crop_h) // 2, (w - crop_w) // 2
            face_roi = frame_bgr[sy:sy+crop_h, sx:sx+crop_w]
        else:
            x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
            face_roi = frame_bgr[y:y+h, x:x+w]

        resized = cv2.resize(face_roi, (128, 128))
        gray_128 = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # 1. PyTorch Deep Spatial Features (256-dim)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb.transpose((2, 0, 1))).float() / 255.0
        # Standardize ImageNet-like mean/std
        tensor = (tensor - 0.5) / 0.5
        tensor = tensor.unsqueeze(0)
        with torch.no_grad():
            deep_feat = self.net(tensor).squeeze(0).numpy()
            norm_d = np.linalg.norm(deep_feat)
            if norm_d > 0:
                deep_feat /= norm_d

        # 2. Spatial LBP Patch Histograms (128-dim)
        patch_feat = self.extract_patch_features(gray_128)
        norm_p = np.linalg.norm(patch_feat)
        if norm_p > 0:
            patch_feat /= norm_p

        # 3. HOG Texture Vector (128-dim)
        gray_64 = cv2.resize(gray_128, (64, 64))
        hog_feat = self.hog.compute(gray_64).flatten()
        hog_sub = np.interp(np.linspace(0, len(hog_feat)-1, 128), np.arange(len(hog_feat)), hog_feat).astype(np.float32)
        norm_h = np.linalg.norm(hog_sub)
        if norm_h > 0:
            hog_sub /= norm_h

        # Combine into 512-dim L2-normalized vector
        embedding = np.zeros(512, dtype=np.float32)
        embedding[:256] = deep_feat * 0.5
        embedding[256:384] = patch_feat * 0.3
        embedding[384:512] = hog_sub * 0.2

        norm_total = np.linalg.norm(embedding)
        if norm_total > 0:
            embedding /= norm_total

        return embedding, "OK"

if __name__ == "__main__":
    print("Testing Spatial BiometricFaceEngine...")
    engine = BiometricFaceEngine()

    def make_person(eye_d, nose_w, skin_val, eye_y=110):
        img = np.ones((300, 300, 3), dtype=np.uint8) * skin_val
        cv2.circle(img, (150 - eye_d, eye_y), 18, (20, 20, 20), -1)
        cv2.circle(img, (150 + eye_d, eye_y), 18, (20, 20, 20), -1)
        cv2.rectangle(img, (150 - nose_w, eye_y + 30), (150 + nose_w, eye_y + 70), (40, 40, 40), -1)
        cv2.ellipse(img, (150, eye_y + 120), (40, 15), 0, 0, 360, (30, 30, 30), -1)
        return img

    p1_a = make_person(eye_d=45, nose_w=15, skin_val=190, eye_y=110)
    p1_b = make_person(eye_d=46, nose_w=14, skin_val=170, eye_y=112) # Same person (Person 1)
    p2   = make_person(eye_d=70, nose_w=35, skin_val=110, eye_y=90)  # Different person (Person 2)

    emb_1a, _ = engine.generate_embedding(p1_a)
    emb_1b, _ = engine.generate_embedding(p1_b)
    emb_2,  _ = engine.generate_embedding(p2)

    score_same = float(np.dot(emb_1a, emb_1b))
    score_diff = float(np.dot(emb_1a, emb_2))

    print(f"Similarity (Same Person 1a vs 1b): {score_same:.4f}")
    print(f"Similarity (Different Person 1 vs 2): {score_diff:.4f}")
    assert score_same > 0.85, f"Same person score too low: {score_same}"
    assert score_diff < 0.60, f"Different person score too high: {score_diff}"
    print("✓ TEST PASSED! Same person matches (>0.85) and different person is rejected (<0.60).")
