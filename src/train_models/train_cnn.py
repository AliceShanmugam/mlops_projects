from pathlib import Path
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score, accuracy_score
import mlflow

# ================= CONFIG =================
IMAGE_SIZE = 128            
BATCH_SIZE = 16             
EPOCHS = 10                 
LR = 1e-3
NUM_CLASSES = 8
DEVICE = "cpu"

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
def train_cnn(
        data_path: Path, 
        artifacts_dir: Path,
        experiment_name: str = "image_classification_cnn",
        run_name: str ="run_cnn_1"):
    
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            mlflow.set_experiment(experiment_name)
            with mlflow.start_run(run_name=run_name,nested=True):
                df = pd.read_csv(data_path)
                df = df.dropna(subset=["image_path", "label"])
                train_df, val_df = train_test_split(df,test_size=0.2,random_state=42,stratify=df["label"])

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
                # mlflow log params
                mlflow.log_param("num_images", len(df))
                mlflow.log_param("num_classes", len(df["label"].unique()))
                mlflow.log_param("image_size",IMAGE_SIZE)
                mlflow.log_param("batch_size",BATCH_SIZE)
                mlflow.log_param( "epochs",EPOCHS)
                mlflow.log_param("learning_rate",LR)
                mlflow.log_param("num_classes",NUM_CLASSES)
                mlflow.log_param( "device",str(DEVICE))
         
                for epoch in range(EPOCHS):
                    model.train()
                    epoch_loss = 0
                    print("Epoch:",epoch+1, "on ",EPOCHS)
                    for images, labels in train_loader:
                        images = images.to(DEVICE, non_blocking=True)
                        labels = labels.to(DEVICE, non_blocking=True)
                        optimizer.zero_grad()
                        outputs = model(images)
                        loss = criterion(outputs, labels)
                        loss.backward()
                        optimizer.step()
                        epoch_loss += loss.item()
                    mlflow.log_metric("train_loss", epoch_loss / len(train_loader), step=epoch)
                    print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {epoch_loss/len(train_loader):0.4f}")

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
                accuracy = accuracy_score(y_true, y_pred)
                #mlflow log metrics
                mlflow.log_metric("accuracy",accuracy)
                mlflow.log_metric("f1_macro",f1)
                mlflow.log_metric("val_loss",epoch_loss / len(val_loader))
                
                model_path = artifacts_dir / "cnn.pt"
                torch.save(model.state_dict(), model_path)
                # mlflow save cnn model
                mlflow.pytorch.log_model(model,"model",registered_model_name="image_CNN_Model")
            
                metrics = {
                    "model": "cnn_from_scratch",
                    "f1_macro": round(f1, 4),
                    "accuracy": round(accuracy, 4),
                    "image_size": IMAGE_SIZE,
                    "batch_size": BATCH_SIZE,
                    "epochs": EPOCHS,
                    "num_images": len(df),
                    "device": DEVICE,
                    "mlflow_run_id": mlflow.active_run().info.run_id
                }
            
                metrics_path = artifacts_dir / "metrics_cnn.json"
                with open(metrics_path, "w") as f:
                    json.dump(metrics, f, indent=2)
                mlflow.log_artifact(metrics_path, "metrics")
            
                print(f"CNN saved to {model_path}")
                print(f"F1 macro: {f1:0.4f}")
                print(f"accuracy: {accuracy:0.4f}")
                print(f"MLflow: {mlflow.active_run().info.run_id}")

            
                return metrics
