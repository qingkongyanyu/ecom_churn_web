# core/mlp_model.py
"""
ANN-MLP 神经网络模型定义
结构：
    - 输入层: 18 维特征
    - 隐藏层1: 64 神经元 + BatchNorm1d + ReLU + Dropout(0.3)
    - 隐藏层2: 32 神经元 + BatchNorm1d + ReLU + Dropout(0.3)
    - 输出层: 1 神经元 + Sigmoid (输出流失概率)
"""
import torch
import torch.nn as nn


class MLP(nn.Module):
    """多层全连接神经网络，用于用户流失二分类预测"""

    def __init__(self, input_dim: int = 18, dropout_rate: float = 0.3):
        """
        Args:
            input_dim: 输入特征维度，默认18
            dropout_rate: Dropout比例，默认0.3
        """
        super(MLP, self).__init__()

        # 第一隐藏层: 18 -> 64
        self.fc1 = nn.Linear(input_dim, 64)
        self.bn1 = nn.BatchNorm1d(64)
        self.dropout1 = nn.Dropout(dropout_rate)

        # 第二隐藏层: 64 -> 32
        self.fc2 = nn.Linear(64, 32)
        self.bn2 = nn.BatchNorm1d(32)
        self.dropout2 = nn.Dropout(dropout_rate)

        # 输出层: 32 -> 1
        self.fc3 = nn.Linear(32, 1)
        self.sigmoid = nn.Sigmoid()

        # 激活函数
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        前向传播

        Args:
            x: 输入张量，形状 (batch_size, input_dim)

        Returns:
            流失概率张量，形状 (batch_size, 1)，值在 [0, 1] 之间
        """
        # 第一隐藏层
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout1(x)

        # 第二隐藏层
        x = self.fc2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.dropout2(x)

        # 输出层
        x = self.fc3(x)
        x = self.sigmoid(x)

        return x


# 便捷测试代码：验证模型前向传播是否正常
if __name__ == "__main__":
    model = MLP(input_dim=18)
    print(model)

    # 生成随机模拟输入: batch_size=4, 特征维度=18
    dummy_input = torch.randn(4, 18)
    output = model(dummy_input)

    print(f"\n输入形状: {dummy_input.shape}")
    print(f"输出形状: {output.shape}")
    print(f"输出示例 (前5个概率): {output[:5].flatten().tolist()}")
    print("模型定义验证通过 ✅")