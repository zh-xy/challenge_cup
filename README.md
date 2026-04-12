# 农民工权益保障智能平台（演示原型）

这是一个基于 FastAPI 的后端演示原型，使用 Mock Data、规则引擎、Jinja2 模板，并可选接入阿里百炼大模型问答，模拟“农民工维权辅助平台”的核心流程。

当前版本默认不依赖真实大模型，也不依赖数据库安装，适合挑战杯答辩演示与接口展示；如果配置了阿里百炼 API Key，`/qa/answer` 会自动升级为基于知识库上下文的智能问答。

## 演示目标

- 将农民工填写的原始案情文本清洗为结构化数据
- 基于规则引擎输出风险评估与建议动作
- 自动生成《劳动仲裁申请书》或《支持起诉申请书》
- 提供检察院支持端 Dashboard，汇总所有已提交案件并高亮高证据案件

## 核心模块

### 1. DataProcessor

负责“数据处理层（The Brain）”：

- 文本清洗：从自然语言中提取姓名、金额、欠薪时长、是否签合同等字段
- 场景识别：识别欠薪、工伤、未签劳动合同等典型类型
- 证据识别：根据文本关键词和表单证据生成标准证据清单
- 智能法律辅助：通过规则引擎输出风险等级、证据分数和建议动作

### 2. DocumentGenerator

负责“文书生成层（The Output）”：

- 基于 Jinja2 模板生成《劳动仲裁申请书》
- 基于 Jinja2 模板生成《支持起诉申请书》

### 3. CaseStore + Prosecutor Dashboard

负责“检察院支持端（The Admin）”：

- 使用内存 List 存储已提交案件
- 内置 4 个典型案例作为演示案例库
- `GET /prosecutor/dashboard` 返回全部案件汇总，并标记高证据案件

## 内置演示案例

- 工地欠薪三个月且未签合同
- 施工现场受伤待申请工伤认定
- 未签劳动合同主张双倍工资
- 包工头跑路导致工资无法结算

## 快速启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 FastAPI

```bash
uvicorn app.api:app --reload
```

启动后可访问：

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

### 3. 启动 Streamlit 演示页

```bash
streamlit run demo/ui.py
```

### 4. 可选：接入阿里百炼智能问答

`/qa/answer` 默认走本地 FAQ 规则匹配；如果配置阿里百炼环境变量，则优先调用大模型，失败时自动回退到规则问答。

```bash
export DASHSCOPE_API_KEY="你的阿里百炼API Key"
export DASHSCOPE_MODEL="qwen-plus"
export DASHSCOPE_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
```

说明：

- 默认模型是 `qwen-plus`
- 默认地域 base URL 是北京地域兼容模式地址
- 若未配置 `DASHSCOPE_API_KEY`，系统不会报错，只会继续使用当前规则问答

## API 概览

- `GET /health`
- `GET /capabilities`
- `GET /cases/samples`
- `GET /cases/submissions`
- `POST /case/analyze`
- `POST /cases/submit`
- `POST /cases/submit/sample/{case_id}`
- `POST /document/generate`
- `POST /qa/answer`
- `GET /prosecutor/dashboard`

## 典型调用示例

### 1. 分析案情

```bash
curl -X POST "http://127.0.0.1:8000/case/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "老板欠我三个月工资，一共2万，没签劳动合同，但有微信聊天记录和考勤照片。",
    "provided_evidence": ["身份证明", "聊天记录", "考勤记录或工作记录"]
  }'
```

### 2. 生成文书

```bash
curl -X POST "http://127.0.0.1:8000/document/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "support_prosecution_application",
    "description": "老板欠我三个月工资，一共2万，没签劳动合同，但有微信聊天记录和考勤照片。",
    "provided_evidence": ["身份证明", "聊天记录", "考勤记录或工作记录"],
    "facts": {
      "worker_name": "张某",
      "company_name": "某建筑劳务公司",
      "amount": "20000",
      "job_title": "木工"
    }
  }'
```

### 3. 查看检察院 Dashboard

```bash
curl "http://127.0.0.1:8000/prosecutor/dashboard"
```

### 4. 智能问答

```bash
curl -X POST "http://127.0.0.1:8000/qa/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "老板拖欠我三个月工资，没有劳动合同，只有微信聊天记录和考勤照片，我该怎么办？"
  }'
```

## 说明

- 数据持久化方式为内存存储，重启服务后会恢复为内置演示数据
- 风险评估是规则引擎结果，不代表真实法律意见
- 智能问答目前仍受限于本地知识库范围，主要覆盖欠薪、工伤、未签劳动合同三个场景
- 当前版本重点服务演示，不包含 OCR、真实案件库和生产级鉴权
