# backend/main.py
"""
FastAPI 推理后端服务
职责：
    1. 启动时加载模型权重、scaler、encoders、feature_cols
    2. 提供 /predict POST 接口，接收前端 JSON 入参
    3. 完成编码、标准化、模型推理，返回流失概率和风险等级
    4. 提供 /api/dashboard 数据分析接口（大屏可视化数据）
    5. 自动生成 Swagger 文档 (/docs)
"""
import pickle
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 添加项目根目录到 sys.path，以便导入 MLP 网络类（仅导入网络定义，不导入训练逻辑）
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.mlp_model import MLP
from backend.analytics import service as analytics_service

# ---------- 路径配置 ----------
PROJECT_ROOT = Path(__file__).parent.parent
MODEL_WEIGHT_DIR = PROJECT_ROOT / "model_weight"

MODEL_PATH = MODEL_WEIGHT_DIR / "ann_churn.pth"
SCALER_PATH = MODEL_WEIGHT_DIR / "scaler.pkl"
ENCODERS_PATH = MODEL_WEIGHT_DIR / "encoders.pkl"
FEATURE_COLS_PATH = MODEL_WEIGHT_DIR / "feature_cols.pkl"

# ---------- 全局对象（启动时加载） ----------
model: MLP = None
scaler: Any = None
encoders: Dict[str, Any] = None
feature_cols: list = None

# ---------- 风险分级配置 ----------
RISK_CONFIG = {
    "low": {"threshold": 0.3, "level": "低流失风险", "color": "green"},
    "medium": {"threshold": 0.7, "level": "中流失风险", "color": "orange"},
    "high": {"threshold": 1.0, "level": "高流失风险", "color": "red"},
}


# ---------- Pydantic 入参模型 (18个特征) ----------
class UserData(BaseModel):
    """前端提交的用户特征，字段名必须与CSV列名完全一致"""
    gender: str = Field(..., description="性别: F/M")
    age_range: str = Field(..., description="年龄段: <18,18-24,25-34,35-44,45-54,55+")
    new_user: int = Field(..., description="是否新用户: 0/1", ge=0, le=1)
    register_days: int = Field(..., description="注册天数", ge=0)
    member_level: int = Field(..., description="会员等级: 0-4", ge=0, le=4)
    device: str = Field(..., description="设备: Mobile/PC/Tablet")
    operative_system: str = Field(..., description="操作系统: Windows/Linux/macOS/Android/iOS")
    source: str = Field(..., description="渠道: Ads/Search/Social/Direct/Email/Referral")
    total_pages_visited: int = Field(..., description="累计访问页面数", ge=0)
    active_days_30d: int = Field(..., description="近30天活跃天数", ge=0, le=30)
    days_since_last_login: int = Field(..., description="距上次登录天数", ge=0)
    cart_total: int = Field(..., description="加购总件数", ge=0)
    fav_total: int = Field(..., description="收藏总件数", ge=0)
    last_buy_days: int = Field(..., description="距上次下单天数", ge=0)
    buy_freq: int = Field(..., description="历史下单总次数", ge=0)
    total_spend: float = Field(..., description="累计消费金额", ge=0)
    avg_order_amount: float = Field(..., description="平均客单价", ge=0)
    refund_cnt: int = Field(..., description="退款次数", ge=0)


# ---------- FastAPI 应用初始化 ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时加载模型与预处理产物，退出时清理"""
    load_artifacts()
    yield


app = FastAPI(
    title="电商用户流失预测 API",
    description="基于 ANN-MLP 的用户流失风险预测接口 + 大屏数据分析接口",
    version="2.0.0",
    lifespan=lifespan,
)

# 配置 CORS（允许 Vue 前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 启动加载函数 ----------
def load_artifacts():
    """启动时加载模型权重和预处理 pkl 文件"""
    global model, scaler, encoders, feature_cols

    print("\n" + "=" * 50)
    print("🔧 加载模型与预处理产物...")

    # 1. 加载 feature_cols（特征顺序）
    with open(FEATURE_COLS_PATH, "rb") as f:
        feature_cols = pickle.load(f)
    print(f"✅ feature_cols 加载成功，共 {len(feature_cols)} 个特征")

    # 2. 加载 encoders（分类编码器）
    with open(ENCODERS_PATH, "rb") as f:
        encoders = pickle.load(f)
    print(f"✅ encoders 加载成功，共 {len(encoders)} 个编码器")

    # 3. 加载 scaler（标准化器）
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    print("✅ scaler 加载成功")

    # 4. 加载模型权重
    model = MLP(input_dim=len(feature_cols))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=True))
    model.eval()  # 关闭 Dropout
    print(f"✅ 模型权重加载成功，输入维度: {len(feature_cols)}")
    print("=" * 50 + "\n")


# ---------- 推理处理函数 ----------
def predict_churn(user_data: UserData) -> Dict[str, float]:
    """
    核心推理流程：
        1. 分类字段用 encoders 编码
        2. 按 feature_cols 顺序组装特征向量
        3. scaler 标准化
        4. 模型推理得到流失概率
    """
    # 1. 将用户数据转为字典
    data_dict = user_data.model_dump()

    # 2. 分类字段编码
    encoded_dict = {}
    for col, value in data_dict.items():
        if col in encoders:
            # 分类特征：用训练好的 LabelEncoder 转换
            le = encoders[col]
            try:
                encoded_dict[col] = le.transform([str(value)])[0]
            except ValueError as e:
                raise ValueError(f"字段 '{col}' 的值 '{value}' 不在训练集类别中，合法值: {le.classes_.tolist()}")
        else:
            # 数值特征：直接保留
            encoded_dict[col] = value

    # 3. 按 feature_cols 顺序组装特征向量（严格一致！）
    feature_values = [encoded_dict[col] for col in feature_cols]
    feature_array = np.array(feature_values, dtype=np.float32).reshape(1, -1)

    # 4. 标准化
    scaled_features = scaler.transform(feature_array)

    # 5. 模型推理
    with torch.no_grad():
        input_tensor = torch.tensor(scaled_features, dtype=torch.float32)
        prob_tensor = model(input_tensor)
        prob = prob_tensor.item()

    # 6. 四舍五入保留4位小数
    prob_rounded = round(prob, 4)

    return {"prob": prob_rounded, "raw_prob": prob}


# ---------- 健康检查接口 ----------
@app.get("/health", tags=["系统"])
async def health_check():
    """服务健康检查"""
    return {"status": "ok", "model_loaded": model is not None}


# ---------- 预测接口 ----------
@app.post("/api/predict", tags=["预测"], response_model=Dict[str, Any])
async def predict(user_data: UserData):
    """
    用户流失风险预测

    - **输入**: 18 个用户特征（JSON格式）
    - **输出**: 流失概率、风险等级、颜色样式
    """
    try:
        # 1. 推理
        result = predict_churn(user_data)
        prob = result["prob"]

        # 2. 风险分级
        if prob < RISK_CONFIG["low"]["threshold"]:
            risk_info = RISK_CONFIG["low"]
        elif prob < RISK_CONFIG["medium"]["threshold"]:
            risk_info = RISK_CONFIG["medium"]
        else:
            risk_info = RISK_CONFIG["high"]

        # 3. 组装返回
        return {
            "churn_prob": prob,
            "risk_level": risk_info["level"],
            "color": risk_info["color"],
        }

    except ValueError as e:
        # 参数非法（如分类特征不在训练集类别中）
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 其他未捕获异常
        raise HTTPException(status_code=500, detail=f"推理服务内部错误: {str(e)}")


# ---------- 根路径（可选） ----------
@app.get("/", tags=["系统"])
async def root():
    return {
        "message": "电商用户流失预测 API 服务",
        "docs": "/docs",
        "health": "/health",
        "dashboard": "/api/dashboard",
    }


# ---------- 大屏数据分析接口 ----------
@app.get("/api/overview", tags=["分析"])
async def api_overview():
    """总体指标：用户数 / 流失 / 留存 / 流失率"""
    return analytics_service.overview()


@app.get("/api/dimensions", tags=["分析"])
async def api_dimensions():
    """各分类维度的流失率分布"""
    return analytics_service.dimensions()


@app.get("/api/correlations", tags=["分析"])
async def api_correlations():
    """数值特征与流失的相关性"""
    return analytics_service.correlations()


@app.get("/api/insights", tags=["分析"])
async def api_insights():
    """基于规则的经营洞察"""
    return analytics_service.insights()


@app.get("/api/model-metrics", tags=["分析"])
async def api_model_metrics():
    """模型训练指标（准确率 / AUC / Loss 曲线）"""
    return analytics_service.model_metrics()


@app.get("/api/dashboard", tags=["分析"])
async def api_dashboard():
    """大屏聚合数据（一次返回全部统计）"""
    return analytics_service.dashboard()


# ---------- 直接运行（调试用） ----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,                  # 直接传 app 对象，不依赖当前工作目录
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )