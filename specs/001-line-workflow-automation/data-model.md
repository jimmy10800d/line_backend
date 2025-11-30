# Data Model: LINE 自動化流程引擎
# 資料模型

**Feature**: 001-line-workflow-automation  
**Date**: 2025-11-30  
**Database**: SQLite + SQLAlchemy ORM

---

## Entity Relationship Diagram (ERD)
## 實體關係圖

```
┌─────────────────────────────────────────────────────────────────┐
│                            User                                  │
│  (單一用戶系統，但保留結構以便未來擴展)                           │
├─────────────────────────────────────────────────────────────────┤
│  PK: id (UUID)                                                   │
│  • line_user_id: VARCHAR(50) UNIQUE                             │
│  • display_name: VARCHAR(100)                                    │
│  • preferences: JSON                                             │
│  • created_at: DATETIME                                          │
│  • updated_at: DATETIME                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │ 1:N              │ 1:N              │ 1:N
         ▼                  ▼                  ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Integration   │  │    Workflow     │  │    Schedule     │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│ PK: id (UUID)   │  │ PK: id (UUID)   │  │ PK: id (UUID)   │
│ FK: user_id     │  │ FK: user_id     │  │ FK: user_id     │
│ • service_type  │  │ • name          │  │ FK: workflow_id │
│ • access_token  │  │ • description   │  │ • cron_expr     │
│ • refresh_token │  │ • trigger       │  │ • next_run_at   │
│ • token_expiry  │  │ • steps (JSON)  │  │ • last_run_at   │
│ • metadata      │  │ • is_active     │  │ • is_active     │
│ • created_at    │  │ • version       │  │ • created_at    │
│ • updated_at    │  │ • created_at    │  │ • updated_at    │
└─────────────────┘  │ • updated_at    │  └─────────────────┘
                     └────────┬────────┘
                              │ 1:N
                              ▼
                     ┌─────────────────┐
                     │  ExecutionLog   │
                     ├─────────────────┤
                     │ PK: id (UUID)   │
                     │ FK: workflow_id │
                     │ FK: schedule_id │
                     │ • task_type     │
                     │ • status        │
                     │ • input (JSON)  │
                     │ • output (JSON) │
                     │ • error         │
                     │ • started_at    │
                     │ • finished_at   │
                     │ • created_at    │
                     └─────────────────┘
```

---

## Entity Definitions
## 實體定義

### 1. User (用戶)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | 主鍵 |
| line_user_id | VARCHAR(50) | UNIQUE, NOT NULL | LINE 用戶 ID |
| display_name | VARCHAR(100) | | LINE 顯示名稱 |
| preferences | JSON | DEFAULT '{}' | 用戶偏好設定 |
| created_at | DATETIME | NOT NULL | 建立時間 |
| updated_at | DATETIME | NOT NULL | 更新時間 |

**Preferences JSON Schema**:
```json
{
  "timezone": "Asia/Taipei",
  "language": "zh-TW",
  "notification_enabled": true,
  "default_calendar_id": "primary"
}
```

### 2. Integration (外部服務整合)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | 主鍵 |
| user_id | UUID | FK → User.id | 用戶外鍵 |
| service_type | ENUM | NOT NULL | 服務類型 |
| access_token | TEXT | ENCRYPTED | 存取權杖（加密） |
| refresh_token | TEXT | ENCRYPTED | 刷新權杖（加密） |
| token_expiry | DATETIME | | 權杖過期時間 |
| metadata | JSON | DEFAULT '{}' | 服務特定資料 |
| created_at | DATETIME | NOT NULL | 建立時間 |
| updated_at | DATETIME | NOT NULL | 更新時間 |

**ServiceType Enum**:
```python
class ServiceType(str, Enum):
    GOOGLE_CALENDAR = "google_calendar"
    NOTION = "notion"
    GITHUB = "github"
```

**Metadata JSON Examples**:
```json
// Google Calendar
{
  "email": "user@gmail.com",
  "calendar_id": "primary"
}

// Notion
{
  "workspace_name": "My Workspace",
  "workspace_id": "abc123"
}

// GitHub
{
  "username": "jimmy10800d",
  "default_repo": "line_backend"
}
```

### 3. Workflow (工作流程)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | 主鍵 |
| user_id | UUID | FK → User.id | 用戶外鍵 |
| name | VARCHAR(100) | NOT NULL | 流程名稱 |
| description | TEXT | | 流程描述 |
| trigger | JSON | NOT NULL | 觸發條件 |
| steps | JSON | NOT NULL | 步驟序列 |
| is_active | BOOLEAN | DEFAULT true | 啟用狀態 |
| version | INTEGER | DEFAULT 1 | 版本號 |
| created_at | DATETIME | NOT NULL | 建立時間 |
| updated_at | DATETIME | NOT NULL | 更新時間 |

**Trigger JSON Schema**:
```json
{
  "type": "command",  // command | schedule | webhook
  "value": "/morning"
}
```

**Steps JSON Schema**:
```json
[
  {
    "order": 1,
    "type": "google_calendar",
    "action": "query",
    "params": {"date": "today"},
    "output_var": "today_events"
  },
  {
    "order": 2,
    "type": "message",
    "action": "send",
    "params": {
      "template": "今日行程：{{today_events}}"
    }
  }
]
```

### 4. Schedule (排程)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | 主鍵 |
| user_id | UUID | FK → User.id | 用戶外鍵 |
| workflow_id | UUID | FK → Workflow.id | 工作流程外鍵 |
| name | VARCHAR(100) | NOT NULL | 排程名稱 |
| cron_expression | VARCHAR(50) | NOT NULL | Cron 表達式 |
| next_run_at | DATETIME | | 下次執行時間 |
| last_run_at | DATETIME | | 上次執行時間 |
| is_active | BOOLEAN | DEFAULT true | 啟用狀態 |
| created_at | DATETIME | NOT NULL | 建立時間 |
| updated_at | DATETIME | NOT NULL | 更新時間 |

### 5. ExecutionLog (執行日誌)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | 主鍵 |
| workflow_id | UUID | FK → Workflow.id, NULLABLE | 工作流程外鍵 |
| schedule_id | UUID | FK → Schedule.id, NULLABLE | 排程外鍵 |
| task_type | VARCHAR(50) | NOT NULL | 任務類型 |
| status | ENUM | NOT NULL | 執行狀態 |
| input | JSON | | 輸入參數 |
| output | JSON | | 輸出結果 |
| error | TEXT | | 錯誤訊息 |
| started_at | DATETIME | NOT NULL | 開始時間 |
| finished_at | DATETIME | | 結束時間 |
| created_at | DATETIME | NOT NULL | 建立時間 |

**ExecutionStatus Enum**:
```python
class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
```

---

## Indexes
## 索引設計

```sql
-- User
CREATE UNIQUE INDEX idx_user_line_id ON user(line_user_id);

-- Integration
CREATE INDEX idx_integration_user ON integration(user_id);
CREATE UNIQUE INDEX idx_integration_user_service ON integration(user_id, service_type);

-- Workflow
CREATE INDEX idx_workflow_user ON workflow(user_id);
CREATE INDEX idx_workflow_active ON workflow(is_active) WHERE is_active = true;

-- Schedule
CREATE INDEX idx_schedule_workflow ON schedule(workflow_id);
CREATE INDEX idx_schedule_next_run ON schedule(next_run_at) WHERE is_active = true;

-- ExecutionLog
CREATE INDEX idx_log_workflow ON execution_log(workflow_id);
CREATE INDEX idx_log_created ON execution_log(created_at);
CREATE INDEX idx_log_status ON execution_log(status);
```

---

## SQLAlchemy Models (Python)
## SQLAlchemy 模型

```python
# src/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func
import uuid

Base = declarative_base()

class TimestampMixin:
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

def generate_uuid():
    return str(uuid.uuid4())
```

```python
# src/models/user.py
from sqlalchemy import Column, String, JSON
from sqlalchemy.dialects.sqlite import UUID
from .base import Base, TimestampMixin, generate_uuid

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(UUID, primary_key=True, default=generate_uuid)
    line_user_id = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100))
    preferences = Column(JSON, default={})
```

```python
# src/models/integration.py
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.sqlite import UUID
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, generate_uuid
from enum import Enum as PyEnum

class ServiceType(str, PyEnum):
    GOOGLE_CALENDAR = "google_calendar"
    NOTION = "notion"
    GITHUB = "github"

class Integration(Base, TimestampMixin):
    __tablename__ = 'integrations'
    
    id = Column(UUID, primary_key=True, default=generate_uuid)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    access_token = Column(Text)  # Encrypted
    refresh_token = Column(Text)  # Encrypted
    token_expiry = Column(DateTime)
    metadata = Column(JSON, default={})
    
    user = relationship("User", back_populates="integrations")
```

---

## Data Retention Policy
## 資料保留政策

| 資料類型 | 保留期限 | 清理策略 |
|----------|----------|----------|
| ExecutionLog | 7 天 | 每日凌晨 3:00 清理 |
| Workflow (deleted) | 30 天軟刪除 | 手動清理 |
| User | 永久 | 不自動清理 |
| Integration | 永久 | Token 過期後保留設定 |

```python
# scripts/cleanup_logs.py
async def cleanup_expired_logs():
    """清理超過 7 天的執行日誌"""
    cutoff = datetime.now() - timedelta(days=7)
    deleted = await ExecutionLog.filter(created_at__lt=cutoff).delete()
    logger.info(f"Cleaned up {deleted} expired execution logs")
```

---

## Migration Strategy
## 遷移策略

使用 Alembic 進行資料庫遷移：

```bash
# 初始化
alembic init alembic

# 建立遷移
alembic revision --autogenerate -m "initial schema"

# 執行遷移
alembic upgrade head
```
