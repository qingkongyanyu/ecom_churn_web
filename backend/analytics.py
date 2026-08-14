# backend/analytics.py
"""
数据分析模块（为大屏提供统计接口）
职责：
    1. 启动时读取原始 CSV 并缓存统计结果
    2. 计算总体指标、分类维度流失率、数值特征相关性
    3. 基于规则生成可读的经营洞察文案
    4. 读取训练阶段保存的 metrics.json（准确率 / AUC / 混淆矩阵 / Loss 曲线）
"""
import json
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

# ---------- 路径配置 ----------
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "churn_data.csv"
MODEL_WEIGHT_DIR = PROJECT_ROOT / "model_weight"
METRICS_PATH = MODEL_WEIGHT_DIR / "metrics.json"

CAT_COLS = ["gender", "age_range", "device", "operative_system", "source"]
TARGET_COL = "churn"
DROP_COLS = ["user_id"]

# 特征中文名映射（前端展示用）
FEATURE_CN = {
    "gender": "性别",
    "age_range": "年龄段",
    "new_user": "是否新用户",
    "register_days": "注册天数",
    "member_level": "会员等级",
    "device": "设备类型",
    "operative_system": "操作系统",
    "source": "渠道来源",
    "total_pages_visited": "累计访问页数",
    "active_days_30d": "近30天活跃天数",
    "days_since_last_login": "距上次登录天数",
    "cart_total": "加购总件数",
    "fav_total": "收藏总件数",
    "last_buy_days": "距上次下单天数",
    "buy_freq": "历史下单次数",
    "total_spend": "累计消费金额",
    "avg_order_amount": "平均客单价",
    "refund_cnt": "退款次数",
}


class AnalyticsService:
    """数据统计服务：惰性加载 + 缓存"""

    def __init__(self):
        self._df: pd.DataFrame | None = None
        self._cache: Dict[str, Any] = {}

    # ---------- 数据加载 ----------
    def _load(self) -> pd.DataFrame:
        if self._df is None:
            self._df = pd.read_csv(DATA_PATH, encoding="utf-8-sig")
            # 丢弃 user_id
            if DROP_COLS and self._df.columns[0] == DROP_COLS[0]:
                self._df = self._df.drop(columns=DROP_COLS, axis=1)
        return self._df

    # ---------- 总体概览 ----------
    def overview(self) -> Dict[str, Any]:
        df = self._load()
        n = len(df)
        churn = int(df[TARGET_COL].sum())
        retain = n - churn
        return {
            "total_users": n,
            "churn_count": churn,
            "retain_count": retain,
            "churn_rate": round(churn / n, 4) if n else 0.0,
            "retain_rate": round(retain / n, 4) if n else 0.0,
        }

    # ---------- 分类维度流失率 ----------
    def dimensions(self) -> List[Dict[str, Any]]:
        df = self._load()
        result = []
        for col in CAT_COLS:
            grp = df.groupby(col)[TARGET_COL].agg(count="count", churn="sum", rate="mean")
            items = [
                {
                    "value": str(idx),
                    "count": int(row["count"]),
                    "churn": int(row["churn"]),
                    "rate": round(float(row["rate"]), 4),
                }
                for idx, row in grp.iterrows()
            ]
            result.append({"dimension": col, "label": FEATURE_CN.get(col, col), "items": items})
        return result

    # ---------- 数值特征与流失相关性 ----------
    def correlations(self) -> List[Dict[str, Any]]:
        df = self._load()
        churn = df[TARGET_COL]
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        num_cols = [c for c in num_cols if c != TARGET_COL]
        items = []
        for col in num_cols:
            corr = df[col].corr(churn)
            # 流失 vs 留存 的均值对比（辅助解读）
            m0 = df[churn == 0][col].mean()
            m1 = df[churn == 1][col].mean()
            items.append({
                "feature": col,
                "label": FEATURE_CN.get(col, col),
                "corr": round(float(corr), 4),
                "mean_retain": round(float(m0), 2),
                "mean_churn": round(float(m1), 2),
            })
        items.sort(key=lambda x: x["corr"], reverse=True)
        return items

    # ---------- 规则化洞察 ----------
    def insights(self) -> List[Dict[str, Any]]:
        """基于数据规则生成经营洞察，供大屏展示"""
        df = self._load()
        avg_rate = df[TARGET_COL].mean()
        insights = []

        def _add(kind, title, desc, rate, n=None, delta=None):
            insights.append({
                "kind": kind,  # up | down | info | model
                "title": title,
                "desc": desc,
                "rate": round(float(rate), 4) if rate is not None else None,
                "count": n,
                "delta": round(float(delta), 4) if delta is not None else None,
            })

        # 1. 沉睡用户
        if "last_buy_days" in df.columns:
            mask = df["last_buy_days"] > 30
            n = int(mask.sum())
            rate = df[mask][TARGET_COL].mean()
            _add("up", "沉睡用户风险",
                 "距上次下单超过 30 天的用户",
                 rate, n, rate - avg_rate)

        # 2. 低活跃用户
        if "active_days_30d" in df.columns:
            mask = df["active_days_30d"] <= 3
            n = int(mask.sum())
            rate = df[mask][TARGET_COL].mean()
            _add("up", "低活跃用户风险",
                 "近 30 天活跃天数 ≤ 3 天的用户",
                 rate, n, rate - avg_rate)

        # 3. 老年用户
        if "age_range" in df.columns:
            mask = df["age_range"].astype(str) == "55+"
            n = int(mask.sum())
            rate = df[mask][TARGET_COL].mean() if n else 0.0
            _add("up", "高龄用户风险",
                 "55 岁以上用户群体",
                 rate, n, (rate - avg_rate) if n else None)

        # 4. 渠道风险
        if "source" in df.columns:
            grp = df.groupby("source")[TARGET_COL].mean()
            top = grp.idxmax()
            rate = grp[top]
            n = int((df["source"] == top).sum())
            _add("up", "高险渠道", f"「{top}」渠道用户",
                 rate, n, rate - avg_rate)

        # 5. 优质用户（留存信号）
        if "buy_freq" in df.columns:
            mask = df["buy_freq"] >= 20
            n = int(mask.sum())
            rate = df[mask][TARGET_COL].mean() if n else 0.0
            _add("down", "忠诚用户留存好",
                 "历史下单 ≥ 20 次的用户",
                 rate, n, (rate - avg_rate) if n else None)

        # 6. 新用户
        if "new_user" in df.columns:
            mask = df["new_user"] == 1
            n = int(mask.sum())
            rate = df[mask][TARGET_COL].mean() if n else 0.0
            _add("info", "新用户观察", "新注册用户群体", rate, n, None)

        return insights

    # ---------- 模型指标 ----------
    def model_metrics(self) -> Dict[str, Any]:
        if METRICS_PATH.exists():
            try:
                with open(METRICS_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    # ---------- 聚合接口（一次请求返回大屏所需全部数据） ----------
    def dashboard(self) -> Dict[str, Any]:
        return {
            "overview": self.overview(),
            "dimensions": self.dimensions(),
            "correlations": self.correlations(),
            "insights": self.insights(),
            "metrics": self.model_metrics(),
        }


# 模块级单例（FastAPI 启动时惰性加载）
service = AnalyticsService()
