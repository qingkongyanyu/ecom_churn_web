# core/dataset.py
"""
数据集加载与预处理模块（训练阶段使用）
职责：读取原始CSV、类别编码、标准化、划分数据集、保存预处理pkl文件
"""
import pickle
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from pathlib import Path

# ---------- 项目根路径 ----------
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "churn_data.csv"
MODEL_WEIGHT_DIR = PROJECT_ROOT / "model_weight"
MODEL_WEIGHT_DIR.mkdir(exist_ok=True)

# ---------- 固定超参 ----------
RANDOM_SEED = 42
TEST_SIZE = 0.1
VAL_SIZE = 0.2   # 相对于剩余数据 (即训练:验证:测试 = 7:2:1)
CAT_COLS = ['gender', 'age_range', 'device', 'operative_system', 'source']
TARGET_COL = 'churn'
DROP_COLS = ['user_id']


class EcomChurnDataset(Dataset):
    """自定义PyTorch Dataset，封装特征和标签张量"""
    def __init__(self, X: np.ndarray, y: np.ndarray):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.float32).view(-1, 1)  # 保持二维，BCELoss需要

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def load_and_preprocess_data():
    """
    核心数据预处理流程：
    1. 读取CSV，丢弃user_id
    2. 识别分类特征，用LabelEncoder编码（保存编码器）
    3. 分离X/y，按7:2:1分层抽样划分
    4. 用训练集拟合StandardScaler（保存scaler）
    5. 保存feature_cols.pkl确保推理时特征顺序一致
    6. 返回三个Dataset对象
    """
    print("=" * 50)
    print("开始数据预处理...")

    # 1. 读取数据
    df = pd.read_csv(DATA_PATH)
    print(f"原始数据形状: {df.shape}")

    # 2. 丢弃无用列
    df_features = df.drop(columns=DROP_COLS, axis=1)
    print(f"丢弃 {DROP_COLS} 后特征列数: {df_features.shape[1]}")

    # 3. 分离特征和标签
    X = df_features.drop(columns=[TARGET_COL], axis=1)
    y = df_features[TARGET_COL].values
    feature_cols = X.columns.tolist()  # 保存列顺序！！！

    print(f"训练特征共 {len(feature_cols)} 列: {feature_cols}")

    # 4. 分类特征 LabelEncoder 编码
    encoders = {}
    X_encoded = X.copy()
    for col in CAT_COLS:
        le = LabelEncoder()
        X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
        encoders[col] = le
        print(f"  [{col}] 编码完成，类别数: {len(le.classes_)}")

    X_array = X_encoded.values.astype(np.float32)

    # 5. 分层抽样划分 7:2:1
    # 先分出 70% 训练，30% 临时集
    X_train, X_temp, y_train, y_temp = train_test_split(
        X_array, y,
        test_size=(VAL_SIZE + TEST_SIZE),
        stratify=y,
        random_state=RANDOM_SEED
    )
    # 再从临时集中分出 2/3 验证，1/3 测试 (即占总体的 20% 和 10%)
    val_ratio = VAL_SIZE / (VAL_SIZE + TEST_SIZE)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp,
        test_size=(1 - val_ratio),
        stratify=y_temp,
        random_state=RANDOM_SEED
    )

    print(f"划分结果 -> 训练: {len(X_train)}, 验证: {len(X_val)}, 测试: {len(X_test)}")

    # 6. 标准化 (只在训练集上fit)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)
    print("标准化完成，均值/方差已保存至scaler")

    # 7. 保存预处理产物到 model_weight/
    with open(MODEL_WEIGHT_DIR / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(MODEL_WEIGHT_DIR / "encoders.pkl", "wb") as f:
        pickle.dump(encoders, f)
    with open(MODEL_WEIGHT_DIR / "feature_cols.pkl", "wb") as f:
        pickle.dump(feature_cols, f)

    print(f"预处理产物已保存至: {MODEL_WEIGHT_DIR}")
    print("=" * 50)

    # 8. 封装为Dataset对象返回
    train_ds = EcomChurnDataset(X_train_scaled, y_train)
    val_ds = EcomChurnDataset(X_val_scaled, y_val)
    test_ds = EcomChurnDataset(X_test_scaled, y_test)

    return train_ds, val_ds, test_ds, feature_cols


# 便捷测试函数（可直接运行查看数据加载是否正常）
if __name__ == "__main__":
    train_ds, val_ds, test_ds, cols = load_and_preprocess_data()
    print(f"训练集样本数: {len(train_ds)}")
    print(f"验证集样本数: {len(val_ds)}")
    print(f"测试集样本数: {len(test_ds)}")
    sample_x, sample_y = train_ds[0]
    print(f"单样本特征形状: {sample_x.shape}, 标签: {sample_y.item()}")