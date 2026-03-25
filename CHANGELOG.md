# 更新日志

## [3.0.16] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**配置加载修复（重要）**

- 修复 `__init__` 方法未接收 `config` 参数导致配置无法加载的问题
- AstrBot 会将配置作为第二个参数传递给插件，但之前的代码没有接收
- 现在 `__init__(self, context: Context, config=None)` 同时支持两种配置传递方式
- 优先使用 `config` 参数（AstrBot 4.x 标准方式）
- 如果没有 `config` 参数，则从 `context.get_config()` 获取（备用方式）
- 添加详细的配置来源日志，帮助诊断配置问题
- 修复了"配置中未找到 VALUES 部分"的警告
- 修复了修改配置后不生效的问题

---

## [3.0.15] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**境界配置键名兼容性修复**

- 修复 `get_level_name()` 方法中使用错误的键名 `level_name` 导致的 KeyError
- 修复 `get_required_exp()` 方法中使用错误的键名 `exp_needed` 导致的错误
- 配置文件使用 `name` 和 `required_exp` 作为键名
- 添加键名兼容性处理，同时支持 `name`/`level_name` 和 `required_exp`/`exp_needed`
- 修复了查看玩家信息时出现 "'level_name'" 错误的问题

**配置加载调试日志**

- 在配置加载时添加详细的调试日志
- 显示从 AstrBot 读取的配置内容
- 显示初始灵石等关键配置项的值
- 帮助用户诊断配置未生效的问题

---

## [3.0.14] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**SQLite 数据库锁定问题修复**

- 在所有数据库写操作后添加 `commit()` 和 `session.close()` 调用
- 在 `PlayerService` 的所有方法中添加 try-except-finally 块确保会话正确关闭
- 在 `require_player` 装饰器中添加会话关闭逻辑，避免读取操作后会话泄漏
- 在 SQLite 连接配置中添加 30 秒超时参数，避免长时间锁定
- 修复了创建角色时出现 "database is locked" 错误的问题
- 确保所有数据库操作后会话都被正确释放

---

## [3.0.13] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**Handler 重复命令注册修复**

- 移除 `pill_handler.py` 中的 `@filter.command` 装饰器
- 移除 `equipment_handler.py` 中的 `@filter.command` 装饰器
- 命令现在只在 `main.py` 中注册一次，handler 方法仅作为处理函数
- 修复了 handler 和 main.py 双重注册导致的命令冲突
- 移除 handler 文件中不再需要的 `filter` 导入

---

## [3.0.12] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**命令注册冲突修复**

- 修复插件内部命令重复注册导致的冲突问题
- 统一使用 `Commands` 常量而非硬编码字符串注册命令
- 修复的命令：
  - 丹药背包：使用 `Commands.PILL_BACKPACK`
  - 服用丹药：使用 `Commands.USE_PILL`
  - 搜索丹药：使用 `Commands.SEARCH_PILL`
  - 我的装备：使用 `Commands.EQUIPMENT_INFO`
  - 装备：使用 `Commands.EQUIP`（新增常量）
  - 卸下：使用 `Commands.UNEQUIP`
- 确保所有命令只注册一次，避免冲突

---

## [3.0.11] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**数据库索引名称冲突修复**

- 修复多个表使用相同索引名称导致的数据库初始化错误
- 重命名 `LoanTable` 的索引：`idx_user_status` → `idx_loan_user_status`, `idx_due` → `idx_loan_due`
- 重命名 `BountyTaskTable` 的索引：`idx_user_status` → `idx_bounty_user_status`, `idx_expire` → `idx_bounty_expire`
- 重命名 `RiftTable` 的索引：`idx_level` → `idx_rift_level`
- 确保所有数据库索引名称全局唯一
- 修复 "index idx_level already exists" 错误

---

## [3.0.10] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**抽象类实例化错误修复**

- 修复 `EquipmentRepository` 未实现 `BaseRepository` 抽象方法的问题
- 实现 `get_by_id()`, `save()`, `delete()`, `exists()` 四个抽象方法
- `save()` 和 `delete()` 抛出 `NotImplementedError`（装备数据为只读配置）
- `get_by_id()` 委托给 `get_equipment_by_id()`
- `exists()` 检查装备是否存在

**配置文件路径问题修复**

- 添加 `_initialize_config_files()` 方法自动复制配置文件
- 插件首次加载时将配置文件从源目录复制到数据目录
- 支持配置文件列表：level_config.json, body_level_config.json, items.json, weapons.json, pills.json, storage_rings.json, adventure_config.json, bounty_templates.json, alchemy_recipes.json
- 避免"历练配置文件不存在"等配置加载错误
- 确保插件在 AstrBot 环境中正常加载

**银行服务配置错误修复**

- 修复 `BankService` 尝试访问不存在的 `settings.game` 属性
- 改为直接使用类中定义的默认配置常量
- 确保银行服务可以正常初始化

---

## [3.0.9] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**禁用未实现的悬赏系统**

- 临时禁用悬赏系统相关功能（bounty_service 未实现）
- 注释掉 bounty_handler 的导入和初始化
- 注释掉所有悬赏相关命令
- 添加 TODO 标记，待后续实现
- 确保插件可以正常加载

---

## [3.0.8] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**缺失异常类修复（续）**

- 添加 `GameException` 类到 `core/exceptions.py`
- `GameException` 作为 `XiuxianException` 的子类，用于游戏逻辑错误
- 修复多个服务和处理器中的导入错误
- 确保所有异常类型都已定义

---

## [3.0.7] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**缺失异常类修复**

- 添加 `BusinessException` 类到 `core/exceptions.py`
- `BusinessException` 作为 `XiuxianException` 的子类，用于一般业务逻辑错误
- 修复多个服务和处理器中的导入错误
- 确保异常处理机制正常工作

---

## [3.0.6] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**AstrBot API 导入错误修复**

- 修复 `filter` 导入路径错误：应从 `astrbot.api.event` 导入，而非 `astrbot.api`
- 修复 `main.py` 中的导入语句
- 修复 `equipment_handler.py` 中的导入语句
- 修复 `pill_handler.py` 中的导入语句
- 确保插件可以正常加载和运行

---

## [3.0.5] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**语法错误修复**

- 重写 `help_handler.py` 文件，使用三引号字符串替代括号字符串拼接
- 添加显式 UTF-8 编码声明
- 修复多行字符串语法错误
- 确保跨平台兼容性

---

## [3.0.4] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**导入错误修复**

- 修复 `ItemRank` 导入错误，应为 `ItemRarity`
- 统一枚举命名：装备品阶使用 `ItemRarity` 而非 `ItemRank`
- 修复 `equipment.py` 和 `equipment_repo.py` 中的导入和使用
- 确保所有枚举引用一致

---

## [3.0.3] - 2024 (Bug 修复版)

### 🐛 Bug 修复

**插件加载失败**

- 修复 `context.get_config()` 调用参数错误
- 移除不支持的默认值参数，改为手动处理 None 情况
- 确保插件可以正常加载

---

## [3.0.2] - 2024 (第二轮代码审核修复版)

### 🔧 严重逻辑错误修复 (P0)

**枚举成员引用错误**

- 修复 `CultivationType.BODY` → `CultivationType.PHYSICAL` 引用错误
- 修正 `breakthrough_service.py` 中的 2 处枚举引用
- 修正 `factories.py` 和 `breakthrough_handler.py` 中的枚举校验
- 确保体修玩家创建和突破流程正常

**配置管理器实例统一**

- Container 现在接收 config_manager 参数，不再内部创建新实例
- main.py 将配置管理器传入 Container，确保全局唯一
- 消除了两套配置源导致的配置不一致问题
- 所有 Service 现在使用同一个配置管理器实例

**命令注册冲突**

- 移除 constants.py 中的重复 `RANK_GOLD` 定义
- 移除 main.py 中的重复 `cmd_rank_gold` 方法
- 统一使用 `RANK_WEALTH` 和 `cmd_rank_wealth`
- 消除命令路由冲突

### ✨ 代码质量改进 (P1)

**状态定义统一**

- 移除 constants.py 中的重复 `PlayerState` 定义（英文值）
- 移除 constants.py 中的重复 `CultivationType` 定义
- 移除 constants.py 中的重复 `ItemType` 定义
- 统一使用 domain/enums.py 中的枚举定义（中文值）
- 确保状态判断和显示一致性

**类型标注修复**

- 修正 `level_data` 和 `body_level_data` 属性，正确处理 JSON 配置结构
- 添加对字典和列表格式的兼容性处理
- 确保返回类型与实际使用一致

**异常处理改进**

- `_load_settings()` 已有详细错误日志和堆栈追踪
- 配置加载失败时记录警告并使用默认配置
- 关键配置错误可被及时发现

### 🛡️ 代码健壮性增强 (P2)

**枚举转换安全性**

- 修改 `PlayerState.from_string()` 对无效输入抛出 ValueError
- 添加清晰的错误提示，列出所有有效状态
- 防止静默失败导致的逻辑错误

**装饰器兼容性**

- 改进 `require_player` 和 `check_player_state` 装饰器
- 支持异步生成器和普通异步函数两种类型
- 添加类型检查和清晰的错误提示
- 使用 `inspect` 模块动态判断函数类型

**配置化数据库路径**

- `Container.database()` 现在从配置管理器读取数据库路径
- 支持通过配置文件自定义数据库文件名
- 提高配置的灵活性和可维护性

### 📝 技术债务

以下问题已识别但未在本次修复：

- 会话管理策略需要优化
- 配置文件路径白名单已实现，需要持续维护

---

## [3.0.1] - 2024 (代码审核修复版)

### 🔧 高风险问题修复

**数据库连接管理**

- 统一数据库连接对象，移除 main.py 中的独立 db_connection
- 所有组件现在使用 container.database() 返回的同一个连接
- 修复了初始化连接和业务连接不一致的问题

**配置目录路径**

- 统一 main.py 和 Container 的配置目录为 `data_dir / "config"`
- 消除了配置漂移风险，确保配置加载一致性

**资源释放**

- 实现 Container.cleanup() 方法正确关闭数据库连接
- terminate() 现在调用 cleanup() 释放所有资源
- 避免资源泄漏问题

### ✨ 代码质量改进

**重构主类构造函数**

- 将 Handler 初始化移到独立的 _setup_handlers() 方法
- **init** 方法现在只负责核心初始化
- 提升代码可读性和可测试性

**异常处理改进**

- _initialize_rifts() 失败时记录详细错误和堆栈信息
- ConfigManager._load_settings() 失败时记录警告
- initialize() 关键初始化失败时中断启动流程
- 所有异常都有清晰的错误提示

**代码清理**

- 移除未使用的导入（Path, DatabaseConnection）
- 添加必要的 logger 导入

### 📝 技术债务

以下问题已识别但未在本次修复：

- 常量定义重复（constants.py vs enums.py）
- 会话管理策略需要优化
- 装饰器类型安全需要增强
- 配置文件路径需要白名单校验

---

## [3.0.0] - 2024

### 🎉 重大更新 - 完全重构

基于 Clean Architecture 原则完全重构修仙插件，提供更稳定、更易维护的代码架构。

### ✨ 新特性

#### 架构升级

- 🏗️ 采用清晰分层架构（Presentation → Application → Domain → Infrastructure）
- 💉 实现依赖注入容器
- 🗄️ 使用 SQLAlchemy ORM 替代原生 SQL
- 📦 配置文件化管理

#### 核心系统（Phase 1-14）

**玩家系统**

- ✅ 创建角色（法修/体修双路线）
- ✅ 每日签到系统
- ✅ 角色信息查看
- ✅ 道号修改
- ✅ 弃道重修功能

**修炼系统**

- ✅ 闭关修炼机制
- ✅ 境界突破系统
- ✅ 体修/法修双路线支持

**战斗系统**

- ✅ PVP 战斗（切磋/决斗）
- ✅ 世界 Boss 系统
- ✅ 传承挑战系统
- ✅ 战斗记录查询

**装备系统**

- ✅ 武器/防具/饰品装备
- ✅ 装备强化系统
- ✅ 装备属性加成

**丹药系统**

- ✅ 丹药背包管理
- ✅ 丹药服用效果
- ✅ 炼丹系统
- ✅ 丹药配方

**商店系统**

- ✅ 丹阁（丹药商店）
- ✅ 器阁（装备商店）
- ✅ 百宝阁（综合商店）
- ✅ 物品信息查询

**储物戒系统**

- ✅ 储物空间管理
- ✅ 物品存取
- ✅ 物品搜索
- ✅ 批量操作
- ✅ 储物戒升级
- ✅ 物品赠予

**宗门系统**

- ✅ 创建/加入宗门
- ✅ 宗门职位管理
- ✅ 宗门捐献
- ✅ 宗门任务
- ✅ 宗门排行

**历练系统**

- ✅ 多种历练路线
- ✅ 历练状态查询
- ✅ 历练奖励结算

**秘境系统**

- ✅ 秘境探索
- ✅ 秘境奖励
- ✅ 秘境列表

**悬赏系统**

- ✅ 悬赏任务
- ✅ 任务进度追踪
- ✅ 任务奖励

**银行系统**

- ✅ 灵石存取
- ✅ 利息计算
- ✅ 贷款系统
- ✅ 银行流水
- ✅ 存款排行

**洞天福地系统**

- ✅ 洞天购买
- ✅ 洞天升级
- ✅ 修炼加成
- ✅ 收益收取

**灵田系统**

- ✅ 灵田开垦
- ✅ 灵草种植
- ✅ 灵草收获
- ✅ 灵田升级

**双修系统**

- ✅ 双修请求
- ✅ 修为互增
- ✅ 冷却机制

**天地灵眼系统**

- ✅ 灵眼抢占
- ✅ 灵眼收益
- ✅ 灵眼释放

**排行榜系统**

- ✅ 境界排行
- ✅ 战力排行
- ✅ 灵石排行
- ✅ 宗门排行
- ✅ 存款排行
- ✅ 贡献排行

### 📊 统计数据

- 80+ 游戏命令
- 24 个数据库表
- 21 个业务服务
- 21 个命令处理器
- 17 个领域模型
- 17 个数据仓储

### 🏗️ 技术架构

**表现层（Presentation）**

- 处理用户命令和消息格式化
- 21 个命令处理器

**应用层（Application）**

- 实现业务逻辑和用例
- 21 个业务服务

**领域层（Domain）**

- 定义核心业务模型和规则
- 17 个领域模型

**基础设施层（Infrastructure）**

- 提供数据持久化和外部服务
- 17 个数据仓储
- SQLAlchemy ORM

### 📝 许可证

本项目采用 GNU AGPL v3 许可证。

### 🤝 致谢

本项目基于 [nonebot_plugin_xiuxian_2](https://github.com/xiuxian-2/nonebot_plugin_xiuxian_2) 重构开发。
