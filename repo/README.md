# 达芬奇手术纪要系统 (DaVinci Surgical Minutes)

针对远程手术指导会议的全栈解决方案，支持腔镜手术画面同步、音频处理、语音转写、AI摘要生成和邮件归档。

## 功能特性

### 🔴 实时音视频处理
- 腔镜手术画面实时同步（支持RTSP/HLS流）
- 多通道音频采集（主刀医生 + 远程专家）
- WebSocket实时双向通信

### 🎵 智能音频处理
- **librosa** 消除电刀干扰（500Hz-5000Hz频段滤波）
- **librosa** 消除监护仪警报（800Hz-3200Hz频段滤波）
- 谱减法降噪 + 维纳滤波
- 实时音频质量监控

### 🎙️ 语音转写与识别
- **Whisper** 多语言语音转写（支持中文）
- 手术步骤自动识别与标记
- 解剖术语智能识别
- **pyannote.audio** 说话人分离（主刀/专家区分）

### 🤖 AI智能摘要
- **OpenAI GPT-4** 手术要点提取
- 手术步骤时间线生成
- 技术改进建议
- 并发症风险评估
- 解剖标识汇总

### 📧 邮件归档
- 精美HTML格式手术记录
- CSV格式转写附件
- 自动归档到手术记录系统
- 邮件模板支持Jinja2定制

## 技术栈

### 后端
- **FastAPI** - 高性能Python Web框架
- **PostgreSQL** - 关系型数据库
- **Redis** - 缓存和消息队列
- **librosa** - 音频分析和处理
- **Whisper** - OpenAI语音转写
- **pyannote.audio** - 说话人识别
- **SQLAlchemy** - ORM框架

### 前端
- **React 18** + **TypeScript**
- **Vite** - 构建工具
- **Ant Design** - UI组件库
- **Tailwind CSS** - 样式框架
- **Zustand** - 状态管理
- **HLS.js** - 视频流播放
- **MediaRecorder API** - 音视频录制

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (推荐)

### 使用Docker部署

```bash
# 克隆项目
git clone <repository-url>
cd auto114

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入API密钥等配置

# 启动所有服务
docker-compose up -d

# 访问前端
# http://localhost

# 访问API文档
# http://localhost:8000/docs
```

### 本地开发

#### 后端
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置
uvicorn app.main:app --reload --port 8000
```

#### 前端
```bash
cd frontend
npm install
npm run dev
```

## 配置说明

### 必要的环境变量

```env
# OpenAI API 密钥
OPENAI_API_KEY=sk-your-api-key

# PyAnnote 认证令牌 (用于说话人识别)
PYANNOTE_AUTH_TOKEN=your-pyannote-token

# SMTP邮件配置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-password

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/davinci_db
```

## API接口

### 手术会话管理
- `POST /api/surgery` - 创建手术会话
- `GET /api/surgery` - 获取手术会话列表
- `GET /api/surgery/{session_id}` - 获取会话详情
- `PUT /api/surgery/{session_id}/end` - 结束手术会话

### 音频处理
- `POST /api/audio/upload/{session_id}` - 上传音频文件
- `POST /api/audio/process/{session_id}` - 处理音频片段
- `GET /api/audio/analyze/{session_id}` - 音频质量分析

### 语音转写
- `POST /api/transcript/transcribe-segment/{session_id}` - 转写音频片段
- `GET /api/transcript/{session_id}` - 获取转写记录
- `GET /api/transcript/surgery-steps/{session_id}` - 获取手术步骤
- `GET /api/transcript/anatomical-terms/{session_id}` - 获取解剖术语

### AI摘要
- `POST /api/summary/generate/{session_id}` - 生成手术摘要
- `GET /api/summary/{session_id}` - 获取手术摘要

### 邮件归档
- `POST /api/archive/send/{session_id}` - 发送归档邮件
- `GET /api/archive/status/{session_id}` - 获取归档状态

### WebSocket
- `WS /ws/{session_id}` - 实时通信通道

## 项目结构

```
auto114/
├── backend/
│   ├── app/
│   │   ├── api/              # API路由
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据模型
│   │   ├── services/         # 业务服务
│   │   └── utils/            # 工具函数
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/       # React组件
│   │   ├── pages/            # 页面组件
│   │   ├── hooks/            # 自定义Hooks
│   │   ├── services/         # API服务
│   │   ├── store/            # 状态管理
│   │   └── types/            # TypeScript类型
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 使用流程

1. **创建手术会话** - 输入患者信息、手术类型、主刀医生和远程专家信息
2. **开始录制** - 系统自动采集音视频，实时传输
3. **实时转写** - Whisper实时转写对话内容，自动标记手术步骤和解剖术语
4. **音频降噪** - 自动消除电刀和监护仪警报噪音
5. **生成摘要** - 手术结束后，AI自动生成结构化手术摘要
6. **邮件归档** - 将完整手术记录发送到归档邮箱

## 注意事项

1. 首次运行会自动下载Whisper模型，可能需要较长时间
2. PyAnnote模型需要在HuggingFace申请访问权限
3. 建议使用GPU加速音频处理和语音转写
4. 请确保有足够的磁盘空间存储手术记录
5. 生产环境请务必配置HTTPS

## License

MIT License
