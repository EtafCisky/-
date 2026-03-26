# 数据存储迁移完成

## 概述

修仙插件 V3 已成功从 SQLAlchemy + SQLite 迁移到基于 JSON 文件的存储方案。

## 完成的工作

### 1. 核心存储层
- ✅ 实现 JSONStorage 类（`infrastructure/storage/json_storage.py`）
- ✅ 实现 TimestampConverter 类（`infrastructure/storage/timestamp_converter.py`）
- ✅ 实现文件锁机制（防止并发冲突）
- ✅ 实现原子写入（临时文件 + 重命名）
- ✅ 实现自动备份和恢复机制
- ✅ 实现内存缓存机制

### 2. Repository 层
已更新所有 Repository 以使用 JSONStorage：
- ✅ PlayerRepository
- ✅ SectRepository
- ✅ ShopRepository
- ✅ BossRepository
- ✅ BountyRepository
- ✅ BankRepository
- ✅ BlessedLandRepository
- ✅ SpiritFarmRepository
- ✅ SpiritEyeRepository
- ✅ DualCultivationRepository
- ✅ ImpartRepository
- ✅ CombatRepository
- ✅ EquipmentRepository
- ✅ StorageRingRepository
- ✅ RiftRepository

### 3. 配置系统
- ✅ 添加 JSONStorageConfig 配置类
- ✅ 更新 Container 以使用配置
- ✅ 创建配置示例文件（`config_example.json`）

### 4. 错误处理
- ✅ 定义存储异常类
- ✅ 实现全面的日志记录
- ✅ 实现数据验证机制

### 5. 文档
- ✅ 添加详细的代码注释和文档字符串
- ✅ 创建使用指南（`infrastructure/storage/README.md`）
- ✅ 提供配置示例

## 主要特性

### 文件组织
- 每个实体类型使用独立的 JSON 文件
- 文件存储在 `data/json/` 目录下
- 统一的数据结构：`{entity_id: entity_data}`

### 并发安全
- 使用 filelock 库实现文件锁
- 支持多线程安全访问
- 自动处理锁超时

### 数据保护
- 原子写入操作
- 自动创建备份文件（.bak）
- JSON 解析失败时自动恢复
- 最多保留 3 个备份文件

### 性能优化
- 内存缓存减少文件 I/O
- 支持过滤、排序、限制查询
- 增量更新机制

### 时间戳标准化
- 统一使用 ISO 8601 格式
- 自动转换 Unix 时间戳
- 所有时间戳使用 UTC 时区

## 配置说明

在 AstrBot 配置中添加以下配置：

```json
{
  "JSON_STORAGE": {
    "DATA_DIR": "data/json",
    "ENABLE_CACHE": true,
    "LOCK_TIMEOUT": 30,
    "MAX_BACKUPS": 3
  }
}
```

### 配置项说明

| 配置项       | 默认值      | 说明                 |
| ------------ | ----------- | -------------------- |
| DATA_DIR     | "data/json" | JSON 文件存储目录    |
| ENABLE_CACHE | true        | 是否启用内存缓存     |
| LOCK_TIMEOUT | 30          | 文件锁超时时间（秒） |
| MAX_BACKUPS  | 3           | 最大备份文件数量     |

## 使用方法

### 基本使用

```python
from infrastructure.storage.json_storage import JSONStorage
from pathlib import Path

# 创建存储实例（通常通过 Container 获取）
storage = container.json_storage()

# 保存数据
storage.set("players.json", "user_001", {"name": "张三", "level": 10})

# 读取数据
player = storage.get("players.json", "user_001")

# 查询数据
top_players = storage.query(
    "players.json",
    sort_key=lambda x: x["level"],
    reverse=True,
    limit=10
)
```

### 在 Repository 中使用

```python
from infrastructure.repositories.player_repo import PlayerRepository

# 通过 Container 获取 Repository
repo = container.player_repository()

# 使用 Repository 操作数据
player = repo.get_by_id("user_001")
repo.save(player)
```

## 注意事项

### 数据迁移
- 本次迁移不包含自动数据迁移工具
- 旧的 SQLite 数据不会自动转换
- 用户需要重新开始游戏或手动迁移数据

### 性能考虑
- 单个 JSON 文件建议不超过 10MB
- 适合中小规模并发场景
- 读多写少的场景性能最佳

### 备份建议
- 定期备份 `data/json/` 目录
- 系统会自动创建 .bak 备份文件
- 建议定期清理旧备份

## 故障排查

### 文件锁超时
- 增加 LOCK_TIMEOUT 配置值
- 减少并发写入频率

### JSON 解析失败
- 系统会自动尝试从备份恢复
- 检查 .bak 备份文件
- 必要时手动恢复数据

### 缓存不一致
- 调用 `storage.reload_cache(filename)` 重新加载

## 相关文档

- 使用指南：`infrastructure/storage/README.md`
- 配置示例：`config_example.json`
- 设计文档：`.kiro/specs/database-to-json-migration/design.md`
- 需求文档：`.kiro/specs/database-to-json-migration/requirements.md`

## 版本信息

- 迁移完成日期：2024
- 插件版本：V3
- 存储方案：JSON 文件存储
- 原存储方案：SQLAlchemy + SQLite

## 后续工作

建议的后续优化：
1. 实现数据迁移工具（可选）
2. 添加数据压缩功能（如果文件过大）
3. 实现数据分片（如果单文件过大）
4. 添加数据导入导出功能

## 许可证

本项目采用 MIT 许可证。
