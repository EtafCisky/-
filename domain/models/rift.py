"""秘境领域模型"""
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional


@dataclass
class Rift:
    """秘境模型"""
    rift_id: int
    rift_name: str
    rift_level: int  # 秘境等级 (1-3)
    required_level: int  # 需求境界索引
    exp_reward_min: int  # 最小修为奖励
    exp_reward_max: int  # 最大修为奖励
    gold_reward_min: int  # 最小灵石奖励
    gold_reward_max: int  # 最大灵石奖励
    description: str = ""  # 描述
    
    def get_rewards_range(self) -> Dict[str, Tuple[int, int]]:
        """获取奖励范围"""
        return {
            "exp": (self.exp_reward_min, self.exp_reward_max),
            "gold": (self.gold_reward_min, self.gold_reward_max)
        }


@dataclass
class RiftEvent:
    """秘境事件"""
    description: str  # 事件描述
    item_chance: int  # 物品掉落概率（百分比）


@dataclass
class RiftResult:
    """秘境探索结果"""
    success: bool
    rift_name: str
    exp_gained: int
    gold_gained: int
    items_gained: List[Tuple[str, int]]  # [(物品名, 数量), ...]
    event_description: str
