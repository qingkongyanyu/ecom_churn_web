# 电商用户流失预测Web系统 — 项目开发方案说明书

> 文件：项目开发方案说明书\.md
> 对应项目：电商用户流失预测 Web 系统
> 配套文档：《项目需求说明书\.md》、《数据集详细说明书\.md》
> 技术栈：Python3\.10\.11、PyTorch2\.5\.1、FastAPI、Vite\+Vue3\+SCSS、uv
> 设计原则：**模块解耦、职责单一、数据与逻辑分离、训练与推理分离**
> 核心设计思想：
> 
> 1. AI 训练模块 和 Web 推理后端完全解耦，训练脚本独立运行，训练产出模型 / 预处理产物交给后端加载；
> 
> 2. 数据处理逻辑封装为工具函数，训练、推理复用同一套预处理对象 \(pkl 文件\)，禁止代码复制粘贴；
> 
> 3. 前后端分离，后端只负责 AI 推理接口，不做页面渲染；前端只负责交互展示；
> 
> 4. 配置、数据、模型权重、源代码目录严格分开；
> 
> 

## 1 开发总体概述

### 1\.1 开发目标

依据需求说明书，完成一套解耦的 AI\+Web 项目：

1. 离线模块：数据集加载、预处理、ANN \(MLP\) 模型训练、评估、持久化输出产物；**只做离线训练，不提供 web 服务**

2. 后端服务模块：FastAPI，只负责加载已经训练好的模型与预处理对象，对外提供推理 HTTP 接口，不包含训练逻辑；

3. 前端模块：Vite\+Vue3\+SCSS，表单交互、请求接口、结果可视化，不接触任何 AI 模型代码；

4. 全部模块通过**文件产物（csv、pth、pkl）、http 接口**交互，模块之间不直接函数调用，实现解耦。

### 1\.2 开发约束

1. Python 使用`uv`作为包管理工具，虚拟环境隔离依赖；

2. 训练与推理代码分离：后端`main.py`**不能 import 训练脚本 \[train\.py\]\(train\.py\)**；

3. 所有文件使用**相对路径**；

4. 严禁在推理代码内部重新 fit scaler、LabelEncoder，全部读取训练阶段导出的 pkl 文件；

5. 本项目仅本地演示，不实现登录、鉴权、高并发。

## 2 整体系统架构（解耦架构）

```Plain Text
┌─────────────┐
│ 原始数据集  │
│ churn_data.csv │
└──────┬──────┘
       │
▼ 离线训练模块（core，独立执行）
┌────────────────────────────────┐
│dataset.py │mlp_model.py │train.py
└───────────┬────────────────────┘
            │输出文件产物
            ▼
┌──────────────────────────────────────────┐
│model_weight/ （解耦关键！模块间靠文件交互）│
│ ann_churn.pth 模型权重                    │
│ scaler.pkl 标准化器                       │
│ encoders.pkl 分类编码器                   │
│ feature_cols.pkl 特征顺序列表             │
└───────┬──────────────────────────────────┘
        │
▼ FastAPI后端（backend，只加载上面产物，无训练代码）
┌─────────────────────┐
│ main.py 推理接口服务 │
└──────────┬──────────┘
           │ HTTP JSON接口 /predict
           ▼
┌─────────────────────┐
│Vite‑Vue3前端模块     │
│Predict.vue页面表单  │
└─────────────────────┘
```

> 解耦说明：
> 
> - core 训练模块运行完成，生成 model\_weight 下一堆文件就完成任务；
> 
> - 后端完全不依赖 core/\[train\.py\]\(train\.py\) 代码，只读取导出的模型与预处理 pkl；
> 
> - 如果后续更换数据集、重新训练，**只重新运行 core/\[train\.py\]\(train\.py\)，后端、前端代码不用改动**。
> 
> 

## 3 完整项目文件目录结构（解耦版）

```Plain Text
ecom_churn_web/                     # 项目根目录
│
├── docs/                           # 📄全部项目文档，和源代码完全解耦
│   ├── 项目需求说明书.md
│   ├── 数据集详细说明书.md
│   └── 项目开发方案说明书.md
│
├── data/                           # 📊数据目录：存放原始数据，代码不修改原始csv
│   └── churn_data.csv
│
├── core/                           # 🧠AI离线训练模块【训练专用，不对外提供web服务】
│   ├── __init__.py
│   ├── dataset.py                  # 数据集加载、预处理逻辑（训练阶段使用）
│   ├── mlp_model.py                # ANN‑MLP模型网络定义【训练、推理都可import这个类】
│   └── train.py                    # 训练入口脚本，运行产出model_weight产物
│
├── model_weight/                   # 📦训练输出产物，git可忽略，运行train.py自动生成
│   ├── ann_churn.pth
│   ├── scaler.pkl
│   ├── encoders.pkl
│   └── feature_cols.pkl
│
├── result_img/                     # 📈实验输出图片，训练脚本自动输出
│   └── loss_curve.png
│
├── backend/                        # ⚡FastAPI推理后端【只做推理，没有训练代码！！！】
│   ├── __init__.py
│   ├── main.py                     # 后端服务入口，加载model_weight产物，提供/predict接口
│   └── requirements.txt            # python依赖清单
│
├── frontend‑vue/                   # 🎨Vite+Vue3前端，完全独立前端工程
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   │   └── request.js          # axios请求封装，访问后端/predict接口
│   │   ├── views/
│   │   │   └── Predict.vue         # 主预测页面：表单输入、结果展示
│   │   ├── style/                  # scss全局样式
│   │   └── main.js
│   ├── vite.config.js
│   └── package.json
│
├── .gitignore                      # git忽略：虚拟环境、model_weight、缓存、图片
├── README.md                       # 项目整体说明，启动步骤
└── pyproject.toml                  # uv包管理配置
```

> 解耦关键点说明：
> 
> 1. `docs`文件夹：所有 md 文档和源码分离，文档不属于业务代码；
> 
> 2. `core`模块：只负责离线训练，**后端 \[main\.py\]\(main\.py\) 仅导入 mlp\\\[\_model\.py\]\(\_model\.py\) 网络类，绝不导入 \[train\.py\]\(train\.py\) 训练脚本**；
> 
> 3. `model_weight`是模块之间的媒介：core 写文件，backend 读文件，两者没有直接函数调用；
> 
> 4. backend、frontend‑vue 各自独立，后端只输出 http 接口，前端完全独立工程。
> 
> 

## 4 各模块详细设计、职责、输入输出

### 4\.1 core 离线 AI 训练模块（离线执行，不启动 web）

> 职责：读取原始数据集，做预处理、搭建 ANN、训练、评估，输出模型与预处理持久化文件。
> 运行入口：`python core/train.py`，**必须在项目根目录执行**
> 
> 

#### 4\.1\.1 \[dataset\.py\]\(dataset\.py\)

职责：数据集读取、清洗、编码、标准化、划分数据集、自定义 Dataset 类
输入：`../data/churn_data.csv`
输出：

- 保存 4 个 pkl 文件到`../model_weight/`：`scaler.pkl`、`encoders.pkl`、`feature_cols.pkl`

- 返回训练 / 验证 / 测试集 Dataset 对象

> 注意：该脚本仅训练阶段调用；推理阶段**不调用 \[dataset\.py\]\(dataset\.py\)**，推理直接读取 pkl。
> 
> 

#### 4\.1\.2 mlp\\\[\_model\.py\]\(\_model\.py\)

职责：PyTorch MLP‑ANN 网络类定义
输入：超参数 input\_dim、隐藏层维度、dropout
输出：MLP 网络实例

> 复用规则：**训练脚本 \[train\.py\]\(train\.py\) 和后端 \[main\.py\]\(main\.py\) 都 import 这个 MLP 类**，保证推理和训练网络结构 100% 一致。
> 
> 

#### 4\.1\.3 \[train\.py\]\(train\.py\)【训练入口脚本】

职责：组装全部训练流程

1. 调用 \[dataset\.py\]\(dataset\.py\) 加载数据集；

2. 实例化 MLP 模型；

3. 训练循环、早停、保存最优权重 ann\_churn\.pth；

4. 绘制 loss 曲线保存至`../result_img/loss_curve.png`；

5. 测试集评估，控制台输出 acc、AUC、混淆矩阵。

输入：`data/churn_data.csv`
输出：

- model\_weight 目录全部产物

- result\_img/loss\_curve\.png

- 控制台打印评估指标

### 4\.2 backend FastAPI 推理后端模块（无训练逻辑！！）

> 职责：加载已经训练完毕的模型与预处理对象，提供 HTTP 推理接口；只处理 web 请求，不做任何模型训练。
> 运行入口：`python backend/main.py`
> 访问调试文档：`http://127.0.0.1:8000/docs`
> 
> 

#### \[main\.py\]\(main\.py\)

1. 导入`core.mlp_model.MLP`网络类（**只导入网络类，不导入 train、dataset**）

2. 服务启动时加载：`ann_churn.pth`、`scaler.pkl`、`encoders.pkl`、`feature_cols.pkl`；设置`model.eval()`，关闭 dropout。

3. 配置 CORS 跨域中间件，允许 vue 前端跨域访问。

4. Pydantic BaseModel 定义`UserData`入参实体，校验前端传来的 18 个特征字段。

5. POST 接口 `/predict`

    - 接收前端 JSON 入参；

    - 使用加载好的 encoders 做类别编码；

    - 严格按照`feature_cols`顺序组装特征向量；

    - scaler 标准化；

    - 模型推理，得到流失概率；

    - 按照规则划分风险等级，返回 json。

> 解耦重点：**后端不会读取原始 csv，不会做数据集划分，不执行训练逻辑**，全部依赖 core 模块输出的文件产物。
> 
> 

### 4\.3 frontend‑vue Vite\+Vue3 前端模块（完全独立工程）

> 职责：UI 交互，表单录入用户特征，http 请求后端接口，渲染预测结果；**完全不接触 AI、pytorch 代码**。
> 启动：进入`frontend‑vue`目录执行 `npm run dev`
> 
> 

1. `src/api/request.js`：axios 封装，请求后端`http://127.0.0.1:8000/predict`；

2. `src/views/Predict.vue`：页面主组件

    - 18 项特征表单，分类字段使用下拉选择框；

    - 点击预测触发 axios 请求；

    - 接收后端返回 json，展示流失概率、风险等级，根据 color 字段切换样式；

3. `src/style/`：SCSS 全局样式。

## 5 模块交互流程（完整业务链路）

### 阶段一：离线训练（只需要运行一次）

```Plain Text
1. data/churn_data.csv
    ↓
2. core/train.py运行 → 调用dataset.py做预处理、mlp_model构建网络，训练
    ↓
3. 输出产物保存到 model_weight/ 与 result_img/
```

### 阶段二：Web 在线预测演示（日常演示用）

```Plain Text
1. 用户操作Vue前端Predict.vue，填写表单，点击预测
    ↓ axios post json
2. FastAPI backend/main.py /predict接口接收请求
    ↓
3. 后端读取model_weight下全部pkl与pth，完成编码、标准化、推理
    ↓ 返回json
4. Vue前端接收返回，渲染概率、风险等级、颜色样式
```

> 模块之间没有 Python 函数直接调用：训练模块和后端之间靠磁盘文件交互；后端和前端靠 HTTP‑JSON 交互。实现完全解耦。
> 
> 

## 6 开发实施步骤（顺序不能乱）

> 使用 uv 包管理器管理 Python 虚拟环境
> 
> 

1. 环境准备

    - 创建 uv 虚拟环境：`uv venv --python 3.10.11`

    - 激活虚拟环境，安装全部 python 依赖，导出 requirements\.txt

2. 目录搭建：严格按照上面文件结构创建全部文件夹与空文件；把`churn_data.csv`放入`data/`

3. 开发 core 模块

    - 编写`mlp_model.py`网络类

    - 编写`dataset.py`数据集加载预处理

    - 编写`train.py`训练脚本

4. **执行离线训练**：项目根目录执行 `python core/train.py`，确认 model\_weight、result\_img 全部生成，看控制台评估指标；

5. 开发 backend 后端

    - 编写`backend/main.py`，只 import MLP 网络类；加载 model\_weight 产物；实现 /predict 接口；配置跨域；

    - 启动后端，访问`127.0.0.1:8000/docs`使用 swagger 测试接口，确认接口返回正常；

6. 前端工程

    - vite 创建 vue3 项目，安装 axios，编写 request\.js、Predict\.vue、scss 样式；npm run dev 启动前端；

7. 前后端联调：填写表单，提交预测，查看页面输出结果；

8. 编写根目录 \[README\.md\]\(README\.md\)，写清环境、训练、后端、前端启动命令；

9. 将全部 md 文档放入 docs 文件夹，整理项目，准备上传 GitHub。

## 7 关键解耦设计说明 \& 风险点规避

|风险点|解耦设计方案|
|---|---|
|后端推理和训练预处理逻辑不一致|训练阶段把 scaler、encoders、feature\_cols 全部保存 pkl；后端只读 pkl，不复写预处理代码；后端不 import \[dataset\.py\]\(dataset\.py\) 训练脚本|
|网络结构训练、推理不一致|训练脚本和后端**共用同一个 mlp\\\[\_model\.py\]\(\_model\.py\) 的 MLP 类**，不复制一份网络代码|
|把训练逻辑写进 web 后端|强制约束：`backend/main.py`禁止 import `train.py`，训练只可以离线脚本运行|
|硬编码特征顺序|feature\_cols\.pkl 保存特征列顺序，推理阶段严格复用，禁止手写顺序列表|
|文档和源码混杂|全部需求、数据集、开发方案 md 统一放在独立 docs 文件夹|
|前端写死业务参数|风险分级逻辑放在后端接口，前端只接收返回颜色字段，后续修改分级规则不用改前端代码|

## 8 测试策略（按模块独立测试，解耦带来可以分模块单独验证）

1. **core 模块单元测试（不启动 web）**
运行`python core/train.py`，确认全部模型产物生成，loss 曲线正常，指标在预期区间；

2. **后端接口独立测试（不需要启动前端）**
启动 backend 服务，访问`/docs`swagger 页面，手动输入 json，测试 /predict 接口返回是否正常；

3. **前端独立测试（可以 mock 接口，不需要真实后端）**
前端可以把 axios 请求替换 mock json 数据，单独调试页面布局、表单、渲染；

4. **完整端到端联调测试**：后端 \+ 前端同时启动，完整表单提交预测。

## 9 交付物清单

1. docs 文件夹内三份 markdown 文档：需求说明书、数据集说明书、本开发方案

2. data/churn\_data\.csv 原始数据集

3. core 模块全部源代码

4. backend 后端源代码 \+ requirements\.txt

5. frontend‑vue 完整前端工程

6. \[README\.md\]\(README\.md\)、pyproject\.toml \(uv 配置\)、\.gitignore

7. 训练产出产物：model\_weight 目录、result\_img 目录（运行 \[train\.py\]\(train\.py\) 自动生成）

> 提示：复制全部内容保存为 `docs/项目开发方案说明书.md`，VS Code 可直接预览 markdown。
> 如果你需要，下一步我可以写项目根目录的 `README.md` 完整模板。
> 
> 

> （注：部分内容可能由 AI 生成）
