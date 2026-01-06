from pathlib import Path
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score

# ================= CONFIG =================
IMAGE_SIZE = 128            
BATCH_SIZE = 16             
EPOCHS = 10                 
LR = 1e-3
NUM_CLASSES = 8


DEVICE = "cpu" #"cuda" if torch.cuda.is_available() else "cpu"

# ================= DATASET =================
class ImageDataset(Dataset):
    def __init__(self, df, transform=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]

        image = Image.open(row.image_path)#.convert("RGB")
        label = int(row.label)

        if self.transform:
            image = self.transform(image)

        return image, label

# ================= MODEL =================
class SimpleCNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),

            nn.Conv2d(64, 128, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * (IMAGE_SIZE // 8) * (IMAGE_SIZE // 8), 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)

# ================= TRAINING =================
def train_cnn(data_path: Path, artifacts_dir: Path):
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    df = df.dropna(subset=["image_path", "label"])

    print(f"Images utilisées : {len(df)}")

    train_df, val_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["label"]
    )

    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5]*3, std=[0.5]*3),
    ])

    train_loader = DataLoader(
        ImageDataset(train_df, transform),
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0
    )

    val_loader = DataLoader(
        ImageDataset(val_df, transform),
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    model = SimpleCNN(NUM_CLASSES).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    # -------- TRAIN LOOP --------
    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0

        for images, labels in train_loader:
            images = images.to(DEVICE, non_blocking=True)
            labels = labels.to(DEVICE, non_blocking=True)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()

        print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {epoch_loss:.4f}")

    # -------- EVAL --------
    model.eval()
    y_true, y_pred = [], []

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(DEVICE, non_blocking=True)
            outputs = model(images)
            preds = outputs.argmax(dim=1).cpu().numpy()

            y_true.extend(labels.numpy())
            y_pred.extend(preds)

    f1 = f1_score(y_true, y_pred, average="macro")

    # -------- SAVE --------
    model_path = artifacts_dir / "cnn.pt"
    torch.save(model.state_dict(), model_path)

    metrics = {
        "model": "cnn_from_scratch",
        "f1_macro": round(f1, 4),
        "image_size": IMAGE_SIZE,
        "batch_size": BATCH_SIZE,
        "epochs": EPOCHS,
        "num_images": len(df),
        "device": DEVICE,
    }

    with open(artifacts_dir / "metrics_cnn.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"CNN saved to {model_path}")
    print(f"F1 macro: {f1:.4f}")

    return metrics
