# core/train.py
"""
ANN-MLP 模型训练入口脚本
职责：
    1. 加载预处理数据（调用 dataset.py）
    2. 搭建模型、定义损失函数和优化器
    3. 训练循环 + 早停机制 (EarlyStopping)
    4. 保存最优模型权重
    5. 绘制训练/验证 Loss 曲线
    6. 测试集评估：准确率、AUC、混淆矩阵
"""
import os
import sys
import json
import pickle
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

# 添加项目根目录到 sys.path，以便导入 core 模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.dataset import load_and_preprocess_data
from core.mlp_model import MLP

# ---------- 路径配置 ----------
PROJECT_ROOT = Path(__file__).parent.parent
MODEL_WEIGHT_DIR = PROJECT_ROOT / "model_weight"
RESULT_IMG_DIR = PROJECT_ROOT / "result_img"

MODEL_WEIGHT_DIR.mkdir(exist_ok=True)
RESULT_IMG_DIR.mkdir(exist_ok=True)

# ---------- 超参数 ----------
RANDOM_SEED = 42
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4          # L2 正则化
EPOCHS = 200                 # 最大训练轮次
EARLY_STOPPING_PATIENCE = 15 # 早停耐心值
MODEL_SAVE_PATH = MODEL_WEIGHT_DIR / "ann_churn.pth"

torch.manual_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


# ---------- EarlyStopping 类 ----------
class EarlyStopping:
    """早停机制：监控验证集loss，连续 patience 轮未改善则停止训练"""

    def __init__(self, patience: int = 15, min_delta: float = 1e-4):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = float('inf')
        self.early_stop = False

    def __call__(self, val_loss: float) -> bool:
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            return False  # 未触发早停
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
                return True  # 触发早停
            return False


# ---------- 训练函数 ----------
def train_epoch(model, dataloader, optimizer, criterion):
    """单轮训练"""
    model.train()
    total_loss = 0.0
    for X_batch, y_batch in dataloader:
        optimizer.zero_grad()
        y_pred = model(X_batch)
        loss = criterion(y_pred, y_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * len(X_batch)
    return total_loss / len(dataloader.dataset)


def eval_epoch(model, dataloader, criterion):
    """单轮验证（不更新梯度）"""
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for X_batch, y_batch in dataloader:
            y_pred = model(X_batch)
            loss = criterion(y_pred, y_batch)
            total_loss += loss.item() * len(X_batch)
    return total_loss / len(dataloader.dataset)


# ---------- 测试集评估函数 ----------
def evaluate_test(model, test_ds):
    """在测试集上计算准确率、AUC、混淆矩阵"""
    model.eval()
    test_loader = DataLoader(test_ds, batch_size=64, shuffle=False)

    all_probs = []
    all_labels = []

    with torch.no_grad():
        for X_batch, y_batch in test_loader:
            probs = model(X_batch).numpy().flatten()
            all_probs.extend(probs)
            all_labels.extend(y_batch.numpy().flatten())

    # 二分类阈值 0.5
    preds = (np.array(all_probs) >= 0.5).astype(int)
    labels = np.array(all_labels)

    acc = accuracy_score(labels, preds)
    auc = roc_auc_score(labels, all_probs)
    cm = confusion_matrix(labels, preds)

    return acc, auc, cm, all_probs, labels


# ---------- 主训练流程 ----------
def main():
    print("\n" + "=" * 60)
    print("🚀 电商用户流失预测 ANN-MLP 训练启动")
    print("=" * 60)

    # 1. 加载预处理数据
    train_ds, val_ds, test_ds, feature_cols = load_and_preprocess_data()

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

    print(f"\n📊 DataLoader 就绪:")
    print(f"   训练批次: {len(train_loader)}，验证批次: {len(val_loader)}")

    # 2. 搭建模型
    model = MLP(input_dim=len(feature_cols))
    print(f"\n🧠 模型结构:\n{model}")

    # 3. 定义损失函数和优化器
    criterion = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)

    # 4. 早停初始化
    early_stopping = EarlyStopping(patience=EARLY_STOPPING_PATIENCE)

    # 5. 训练循环
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')
    best_epoch = 0

    print(f"\n🏋️ 开始训练 (最大 {EPOCHS} 轮)...")
    print("-" * 60)

    for epoch in range(1, EPOCHS + 1):
        train_loss = train_epoch(model, train_loader, optimizer, criterion)
        val_loss = eval_epoch(model, val_loader, criterion)

        train_losses.append(train_loss)
        val_losses.append(val_loss)

        # 保存最优模型
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_epoch = epoch
            torch.save(model.state_dict(), MODEL_SAVE_PATH)
            print(f"✅ Epoch {epoch:3d} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f} | 💾 模型已保存 (最优)")
        else:
            print(f"   Epoch {epoch:3d} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")

        # 早停判断
        if early_stopping(val_loss):
            print(f"\n⏹️  Early Stopping 触发于第 {epoch} 轮，停止训练")
            break

    print("-" * 60)
    print(f"✅ 训练完成，最优模型已保存至: {MODEL_SAVE_PATH}")

    # 6. 绘制 Loss 曲线
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, len(train_losses) + 1), train_losses, label='Train Loss', linewidth=2)
    plt.plot(range(1, len(val_losses) + 1), val_losses, label='Validation Loss', linewidth=2)
    plt.xlabel('Epoch')
    plt.ylabel('Loss (BCE)')
    plt.title('Training & Validation Loss Curve')
    plt.legend()
    plt.grid(True, alpha=0.3)

    loss_img_path = RESULT_IMG_DIR / "loss_curve.png"
    plt.savefig(loss_img_path, dpi=300, bbox_inches='tight')
    print(f"📈 Loss 曲线已保存至: {loss_img_path}")
    plt.close()

    # 7. 测试集评估
    print("\n" + "=" * 60)
    print("🧪 测试集评估结果")
    print("=" * 60)

    # 重新加载最优模型权重进行评估
    model.load_state_dict(torch.load(MODEL_SAVE_PATH, map_location=torch.device('cpu'), weights_only=True))
    acc, auc, cm, probs, labels = evaluate_test(model, test_ds)

    print(f"✅ 测试集样本数: {len(test_ds)}")
    print(f"📊 准确率 (Accuracy): {acc:.4f} ({acc*100:.2f}%)")
    print(f"📊 AUC: {auc:.4f}")
    print(f"\n📋 混淆矩阵:")
    print("             预测留存(0)  预测流失(1)")
    print(f"实际留存(0)    {cm[0,0]:>6}      {cm[0,1]:>6}")
    print(f"实际流失(1)    {cm[1,0]:>6}      {cm[1,1]:>6}")

    # 额外输出：每个类别的精确率/召回率辅助信息
    total_0 = cm[0,0] + cm[0,1]
    total_1 = cm[1,0] + cm[1,1]
    if total_0 > 0:
        recall_0 = cm[0,0] / total_0
        print(f"\n📌 留存用户召回率 (Recall_0): {recall_0:.4f}")
    if total_1 > 0:
        recall_1 = cm[1,1] / total_1
        print(f"📌 流失用户召回率 (Recall_1): {recall_1:.4f}")

    # 8. 保存模型指标 JSON（供大屏/后端展示）
    metrics = {
        "accuracy": round(float(acc), 4),
        "auc": round(float(auc), 4),
        "cm": [[int(v) for v in row] for row in cm],
        "best_epoch": best_epoch,
        "best_val_loss": round(float(best_val_loss), 6),
        "epochs_run": len(train_losses),
        "train_samples": len(train_ds),
        "val_samples": len(val_ds),
        "test_samples": len(test_ds),
        "loss_curve": {
            "train": [round(float(v), 6) for v in train_losses],
            "val": [round(float(v), 6) for v in val_losses],
        },
        "feature_cols": feature_cols,
    }
    metrics_path = MODEL_WEIGHT_DIR / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"\n📦 模型指标已保存至: {metrics_path}")

    print("\n" + "=" * 60)
    print("🎉 训练流程全部完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()