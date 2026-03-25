"""悬赏领域模型"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional


class BountyStatus(Enum):
    """悬赏状态枚举"""
    CANCELLED = 0  # 已取消
    ACTIVE = 1  # 进行中
    COMPLETED = 2  # 已完成
    EXPIRED = 3  # 已过期


class BountyDifficulty(Enum):
    """悬赏难度枚举"""
    EASY = "easy"  # F级
    NORMAL = "normal"  # E级
    HARD = "hard"  # D级
    ELITE = "elite"  # C级


@dataclass
class BountyTemplate:
    """悬赏模板"""
    id: int  # 模板ID
    name: str  # 任务名称
    difficulty: str  # 难度
    category: str  # 类别（巡山、采集、猎杀等）
    progress_tags: List[str]  # 进度标签（用于匹配活动）
    min_target: int  # 最小目标数量
    max_target: int  # 最大目标数量
    time_limit: int  # 时间限制（秒）
    reward: Dict[str, int]  # 基础奖励 {"stone": 灵石, "exp": 修为}
    item_table: str  # 物品掉落表名称
    description: str  # 描述
    weight: int = 1  # 权重（用于随机选择）


@dataclass
class BountyTask:
    """悬赏任务"""
    task_id: int  # 任务ID
    user_id: str  # 玩家ID
    bounty_id: int  # 悬赏模板ID
    bounty_name: str  # 任务名称
    target_type: str  # 目标类型
    target_count: int  # 目标数量
    current_progress: int  # 当前进度
    rewards: str  # 奖励JSON字符串
    start_time: int  # 开始时间戳
    expire_time: int  # 过期时间戳
    status: int  # 状态（0=已取消，1=进行中，2=已完成，3=已过期）
    
    def is_active(self) -> bool:
        """检查任务是否进行中"""
        return self.status == BountyStatus.ACTIVE.value
    
    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self.current_progress >= self.target_count
    
    def get_progress_percent(self) -> float:
        """获取进度百分比"""
        if self.target_count <= 0:
            return 0.0
        return (self.current_progress / self.target_count) * 100


@dataclass
class BountyReward:
    """悬赏奖励"""
    stone: int  # 灵石
    exp: int  # 修为
    items: List[tuple]  # 物品 [(物品名, 数量), ...]


@dataclass
class BountyEntry:
    """悬赏条目（用于显示列表）"""
    id: int  # 悬赏ID
    name: str  # 任务名称
    category: str  # 类别
    difficulty: str  # 难度
    difficulty_name: str  # 难度名称
    description: str  # 描述
    count: int  # 目标数量
    reward: Dict[str, int]  # 奖励
    time_limit: int  # 时间限制（秒）
    progress_tags: List[str]  # 进度标签
    item_table: str  # 物品掉落表
