# 电商用户流失预测Web系统 《项目需求说明书》

> 文件：项目需求说明书\.md
> 技术栈：Python3\.10\.11、PyTorch2\.5\.1、FastAPI、Vite\+Vue3\+SCSS、scikit‑learn
> 项目定位：简历实战项目，实现 ANN‑MLP 模型训练 \+ Web 前后端预测演示
> 
> 

## 1 引言

### 1\.1 编写目的

本说明书明确**电商用户流失预测 Web 系统**全部业务需求、功能需求、非功能需求、输入输出、约束条件，作为后续编码开发、测试、项目验收的依据。
本项目为学生实战项目，用于简历展示，实现基于人工神经网络 ANN \(MLP\) 对电商用户做流失风险预测，并通过 Web 页面完成可视化演示。

### 1\.2 项目背景

电商平台运营需要识别潜在流失用户，从而开展挽留运营活动。传统统计方法难以挖掘多维度用户特征间的非线性关系。
本项目利用电商用户真实行为数据集，采用 PyTorch 搭建多层全连接人工神经网络 ANN，完成用户流失二分类预测；结合 FastAPI 后端、Vue3 前端构建 Web 系统，运营人员输入用户信息即可得到流失风险结果。

### 1\.3 适用范围

- 项目开发人员；项目测试；GitHub 项目文档；简历项目佐证。

- 仅本地演示使用，不面向公网生产部署。

### 1\.4 术语定义

|术语|说明|
|---|---|
|ANN / MLP|多层全连接人工神经网络，本项目用于用户流失二分类|
|churn|流失标签：1 = 用户流失，0 = 用户留存|
|LabelEncoder|标签编码器，对文本类别特征转为数字|
|标准化 \(StandardScaler\)|把特征缩放到均值 0 方差 1，神经网络训练必备预处理|
|pkl 文件|持久化文件，保存编码器、标准化器，用于线上推理复用|
|pth|PyTorch 模型权重文件，保存训练完成 ANN 网络参数|

## 2 总体描述

### 2\.1 产品愿景

实现一套完整 AI 建模 \+ Web 可视化演示系统：离线完成数据集处理、ANN 神经网络训练评估；Web 端录入用户信息，实时输出用户流失概率与风险等级。

### 2\.2 运行环境约束

#### 硬件环境

- CPU：普通家用 / 笔记本 CPU，**不需要 GPU 显卡**

- 内存 ≥ 4GB

#### 软件环境

|软件|版本要求|
|---|---|
|Python|3\.10\.11|
|PyTorch|2\.5\.1（CPU 版本）|
|后端框架|FastAPI、uvicorn|
|前端|Vite \+ Vue3 \+ SCSS \+ Axios|
|数据处理库|Pandas、NumPy、scikit‑learn、Matplotlib|
|操作系统|Windows10 / Windows11|

### 2\.3 数据集约束

1. 数据集文件名称：`churn_data.csv`，存放路径`./data/churn_data.csv`

2. 数据总样本：500 条；无缺失值；

3. 包含`user_id`唯一标识，18 个业务特征；标签字段`churn`；

4. 5 个文本分类特征，训练前必须编码转换；

5. 标签分布：流失 49\.8%，留存 50\.2%，样本均衡。

### 2\.4 主要业务角色

> 本系统仅一个角色：**运营演示人员**
> 
> 

- 业务操作：在 Web 表单录入用户全部特征，提交预测，查看流失概率、风险等级。

## 3 功能性需求

> 系统划分为 4 大功能模块：数据预处理模块、ANN 模型训练模块、后端推理接口模块、Vue 前端 Web 模块。
> 
> 

### 3\.1 数据预处理模块（离线训练阶段）

编号：REQ‑DATA‑001

> 目标：原始 csv 转换为 PyTorch 可训练数据集对象，保存预处理工具供推理复用。
> 
> 

1. REQ‑DATA‑001‑1：读取`churn_data.csv`，丢弃`user_id`无业务意义字段。

2. REQ‑DATA‑001‑2：识别 5 个分类字段，使用 LabelEncoder 完成编码；**将编码器对象保存为 encoders\.pkl**，推理阶段加载复用，禁止推理时重新 fit 拟合。

3. REQ‑DATA‑001‑3：分离特征矩阵 X 与标签 y。

4. REQ‑DATA‑001‑4：采用分层抽样 stratify，按 7:2:1 划分训练集、验证集、测试集，保证三集合流失 / 留存标签比例和原始数据集保持一致。

5. REQ‑DATA‑001‑5：使用 StandardScaler 对特征标准化；保存 scaler\.pkl 标准化器，推理阶段必须复用该对象。

6. REQ‑DATA‑001‑6：保存训练时特征列顺序 feature\_cols\.pkl，推理组装特征严格按照该顺序。

7. REQ‑DATA‑001‑7：自定义继承 Dataset 类`EcomChurnDataset`，封装数据，用于 DataLoader 加载。

### 3\.2 ANN 模型训练与评估模块（离线训练阶段）

编号：REQ‑TRAIN‑002

1. REQ‑TRAIN‑002‑1：基于 PyTorch nn\.Module 搭建 MLP‑ANN 网络，输入维度 18，两层隐藏层 \(64,32\)；配置 BatchNorm1d、Dropout 防止过拟合；最后 Sigmoid 输出 0‑1 之间流失概率。

2. REQ‑TRAIN‑002‑2：损失函数采用 BCELoss；优化器 Adam，开启 L2 权重衰减，抑制过拟合。

3. REQ‑TRAIN‑002‑3：训练循环中增加**早停 EarlyStopping**，监控验证集 loss，连续 N 轮无下降则终止训练，保存最优模型权重 ann\_churn\.pth。

4. REQ‑TRAIN‑002‑4：训练过程记录训练 loss、验证 loss，生成 loss 曲线图保存到`result_img/loss_curve.png`。

5. REQ‑TRAIN‑002‑5：在测试数据集完成模型评估，控制台输出指标：准确率 Accuracy、AUC、混淆矩阵。

6. REQ‑TRAIN‑002‑6：全部产出文件输出至`model_weight/`目录。

### 3\.3 FastAPI 后端接口模块（Web 在线推理）

编号：REQ‑BACKEND‑003

1. REQ‑BACKEND‑003‑1：启动服务时加载：ANN 模型权重 ann\_churn\.pth、scaler\.pkl、encoders\.pkl、feature\_cols\.pkl；模型设置 eval 评估模式，关闭 Dropout。

2. REQ‑BACKEND‑003‑2：配置 CORS 跨域中间件，允许 Vue 前端发起请求。

3. REQ‑BACKEND‑003‑3：定义 Pydantic 入参模型`UserData`，对前端提交的 18 项用户特征做参数校验。

4. REQ‑BACKEND‑003‑4：提供 POST 接口`/predict`。

    - 输入：JSON，完整 18 个用户特征

    - 内部处理：加载保存好的编码器做类别转换，按照 feature\_cols 顺序组装特征向量，scaler 标准化，模型推理得到流失概率。

    - 风险分级规则：

        - prob \<0\.3 → 低流失风险

        - 0\.3 ≤ prob \<0\.7 → 中流失风险

        - prob ≥0\.7 → 高流失风险

    - 返回 JSON 字段：`churn_prob`\(保留 4 位小数\)、`risk_level`风险等级、`color`（green/orange/red，用于前端样式）

5. REQ‑BACKEND‑003‑5：接口捕获异常，参数非法返回提示信息；提供 swagger 文档`/docs`方便调试接口。

### 3\.4 Vue3 前端 Web 演示模块

编号：REQ‑FRONT‑004

1. REQ‑FRONT‑004‑1：Vite 创建 Vue3 项目，使用 SCSS 编写页面样式；Axios 用于 http 请求后端接口。

2. REQ‑FRONT‑004‑2：构建表单页面，提供全部 18 个特征输入控件；分类字段使用下拉选择框限定输入选项，避免非法文本输入。

3. REQ‑FRONT‑004‑3：点击预测按钮，收集表单全部字段，axios POST 请求后端`/predict`接口。

4. REQ‑FRONT‑004‑4：接收后端返回 JSON，页面展示流失概率数值、风险等级；根据 color 字段切换文字 / 卡片背景颜色。

5. REQ‑FRONT‑004‑5：页面布局简洁，适合现场项目演示。

## 4 非功能性需求

### 4\.1 性能需求

1. 模型离线训练：CPU 运行，整体训练耗时 ≤60 秒。

2. Web 单用户预测接口响应时间：≤200ms。

3. 本系统不做高并发，仅支持单用户演示。

### 4\.2 可靠性需求

1. 训练、推理必须使用同一套 scaler、encoders，禁止推理阶段重新 fit，避免特征分布不一致。

2. 模型推理阶段必须设置 model\.eval \(\)，关闭 dropout。

### 4\.3 可移植性需求

1. 提供 requirements\.txt，记录全部 Python 依赖包版本。

2. 项目路径使用相对路径，换环境仅需要配置虚拟环境，不需要修改大量代码。

3. 提供 \[README\.md\]\(README\.md\) 说明文档，写明项目启动步骤。

### 4\.4 可演示性需求

1. 本地可以完整跑通：训练模型 → 启动后端 → 启动前端，完成端到端演示。

2. 产出 loss 曲线图、控制台评估指标，作为项目成果，用于简历、GitHub 展示。

## 5 输入输出规定

### 5\.1 离线训练阶段

- 输入：`data/churn_data.csv`

- 输出：

    - model\_weight 目录：ann\_churn\.pth、scaler\.pkl、encoders\.pkl、feature\_cols\.pkl

    - result\_img/loss\_curve\.png

    - 控制台打印：训练 loss、验证 loss、测试集准确率、AUC、混淆矩阵

### 5\.2 Web 接口 /predict

请求（POST JSON）示例片段：

```json
{
  "gender":"F",
  "age_range":"25‑34",
  "new_user":0,
  "register_days":416,
  "member_level":3,
  "device":"Mobile",
  "operative_system":"Windows",
  "source":"Ads",
  "total_pages_visited":134,
  "active_days_30d":16,
  "days_since_last_login":2,
  "cart_total":11,
  "fav_total":17,
  "last_buy_days":14,
  "buy_freq":19,
  "total_spend":9490.24,
  "avg_order_amount":526.42,
  "refund_cnt":1
}
```

返回输出 JSON 示例：

```json
{
  "churn_prob":0.8231,
  "risk_level":"高流失风险",
  "color":"red"
}
```

## 6 约束条件

1. Python 版本固定使用 **3\.10\.11**，不允许使用 3\.13 版本进行开发。

2. ANN 模型使用 PyTorch 原生手写搭建，**不能直接调用 sklearn 的 MLP，体现深度学习框架编码能力**。

3. 项目仅本地演示，**不做公网部署、用户登录、权限管理**。

4. 数据集为模拟电商用户数据集，仅用于学习项目，不用于真实商业生产。

## 7 预期模型指标（参考）

> 在本 500 条数据集条件下，模型合理效果区间
> 
> 

- 测试集准确率：82% \~ 88%

- AUC：0\.84 \~ 0\.89

## 8 交付物

1. 本《项目需求说明书\.md》

2. 全部源代码文件

3. 训练产出模型权重与 pkl 预处理文件

4. loss 曲线图

5. requirements\.txt

6. \[README\.md\]\(README\.md\) 项目说明文档

> 说明：本文件只做**需求定义**，不包含实现代码、开发步骤；开发方案是另外一份独立文档。
> 
> 

---

> 使用说明：复制全部内容，保存为 `项目需求说明书.md`，VS Code 打开即可预览 markdown 格式。
> 如果你需要，我再给你独立的《项目开发方案说明书\.md》。
> 
> 

> （注：部分内容可能由 AI 生成）
