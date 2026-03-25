"""秘境服务"""
import json
import random
import time
from typing import List, Tuple, Optional

from ...core.config import ConfigManager
from ...core.exceptions import GameException
from ...domain.models.rift import Rift, RiftEvent, RiftResult
from ...infrastructure.repositories.player_repo import PlayerRepository
from ...infrastructure.repositories.rift_repo import RiftRepository
from ...infrastructure.repositories.storage_ring_repo import StorageRingRepository


class RiftService:
    """秘境服务"""
    
    # 默认探索时长（秒）
    DEFAULT_DURATION = 1800  # 30分钟
    
    # 秘境物品掉落表（按秘境等级分组）
    RIFT_DROP_TABLE = {
        1: [  # 低级秘境
            {"name": "灵草", "weight": 40, "min": 2, "max": 5},
            {"name": "精铁", "weight": 30, "min": 1, "max": 3},
            {"name": "灵石碎片", "weight": 30, "min": 3, "max": 8},
        ],
        2: [  # 中级秘境
            {"name": "灵草", "weight": 30, "min": 3, "max": 7},
            {"name": "玄铁", "weight": 25, "min": 2, "max": 4},
            {"name": "灵兽毛皮", "weight": 20, "min": 1, "max": 3},
            {"name": "功法残页", "weight": 15, "min": 1, "max": 1},
            {"name": "秘境精华", "weight": 10, "min": 1, "max": 2},
        ],
        3: [  # 高级秘境
            {"name": "玄铁", "weight": 25, "min": 3, "max": 6},
            {"name": "星辰石", "weight": 20, "min": 2, "max": 4},
            {"name": "灵兽内丹", "weight": 20, "min": 1, "max": 2},
            {"name": "功法残页", "weight": 20, "min": 1, "max": 2},
            {"name": "天材地宝", "weight": 15, "min": 1, "max": 1},
        ],
    }
    
    # 秘境稀有丹药掉落表（按秘境等级分组）
    RIFT_PILL_DROP_TABLE = {
        1: [  # 低级秘境 - 3%概率掉落
            {"name": "三品凝神增益丹", "weight": 100, "min": 1, "max": 1},
        ],
        2: [  # 中级秘境 - 5%概率掉落
            {"name": "三品凝神增益丹", "weight": 50, "min": 1, "max": 1},
            {"name": "四品破境增益丹", "weight": 40, "min": 1, "max": 1},
            {"name": "五品渡劫增益丹", "weight": 10, "min": 1, "max": 1},
        ],
        3: [  # 高级秘境 - 10%概率掉落
            {"name": "四品破境增益丹", "weight": 40, "min": 1, "max": 1},
            {"name": "五品渡劫增益丹", "weight": 30, "min": 1, "max": 1},
            {"name": "六品破境增益丹", "weight": 20, "min": 1, "max": 1},
            {"name": "七品化神增益丹", "weight": 10, "min": 1, "max": 1},
        ],
    }
    
    # 秘境丹药掉落概率（百分比）
    RIFT_PILL_DROP_CHANCE = {
        1: 3,   # 低级秘境 3%
        2: 5,   # 中级秘境 5%
        3: 10,  # 高级秘境 10%
    }
    
    # 秘境事件列表
    RIFT_EVENTS = [
        {"desc": "你发现了一处灵泉，修为大增！", "item_chance": 70},
        {"desc": "你在秘境中击败了一只妖兽！", "item_chance": 80},
        {"desc": "你找到了一个隐藏的宝箱！", "item_chance": 100},
        {"desc": "你领悟了一些修炼心得。", "item_chance": 40},
        {"desc": "你在秘境中遇到了前辈留下的传承！", "item_chance": 90}
    ]
    
    def __init__(
        self,
        player_repo: PlayerRepository,
        rift_repo: RiftRepository,
        storage_ring_repo: StorageRingRepository,
        config_manager: ConfigManager
    ):
        self.player_repo = player_repo
        self.rift_repo = rift_repo
        self.storage_ring_repo = storage_ring_repo
        self.config_manager = config_manager
        self.explore_duration = self.DEFAULT_DURATION
    
    def get_all_rifts(self) -> List[Rift]:
        """获取所有秘境"""
        return self.rift_repo.get_all_rifts()
    
    def enter_rift(self, user_id: str, rift_id: int) -> str:
        """进入秘境"""
        # 获取玩家
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        # 检查状态
        if player.state != "idle":
            raise GameException("你当前无法探索秘境")
        
        # 获取秘境
        rift = self.rift_repo.get_rift_by_id(rift_id)
        if not rift:
            raise GameException("秘境不存在！使用【秘境列表】查看可用秘境")
        
        # 检查境界要求
        if player.level_index < rift.required_level:
            level_name = self._get_level_name(rift.required_level)
            raise GameException(f"探索【{rift.rift_name}】需要达到【{level_name}】！")
        
        # 设置探索状态
        start_time = int(time.time())
        end_time = start_time + self.explore_duration
        
        extra_data = {
            "rift_id": rift_id,
            "rift_level": rift.rift_level,
            "start_time": start_time,
            "end_time": end_time
        }
        
        self.player_repo.update_player_state(
            user_id,
            state="exploring",
            extra_data=json.dumps(extra_data)
        )
        
        return f"✨ 你进入了『{rift.rift_name}』！探索需要 {self.explore_duration//60} 分钟。\n使用【完成探索】领取奖励"
    
    def finish_exploration(self, user_id: str) -> RiftResult:
        """完成秘境探索"""
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        if player.state != "exploring":
            raise GameException("你当前不在探索秘境")
        
        # 解析状态数据
        state_data = self.player_repo.get_player_state(user_id)
        if not state_data or not state_data.extra_data:
            raise GameException("秘境数据异常")
        
        extra_data = json.loads(state_data.extra_data)
        rift_id = extra_data.get("rift_id")
        rift_level = extra_data.get("rift_level", 1)
        end_time = extra_data.get("end_time", 0)
        
        # 检查是否完成
        current_time = int(time.time())
        if current_time < end_time:
            remaining = end_time - current_time
            minutes = remaining // 60
            raise GameException(f"探索尚未完成！还需要 {minutes} 分钟")
        
        # 获取秘境
        rift = self.rift_repo.get_rift_by_id(rift_id) if rift_id else None
        rift_name = rift.rift_name if rift else "未知秘境"
        
        # 计算奖励
        if rift:
            exp_reward = random.randint(rift.exp_reward_min, rift.exp_reward_max)
            gold_reward = random.randint(rift.gold_reward_min, rift.gold_reward_max)
            rift_level = rift.rift_level
        else:
            # 兼容旧数据
            exp_reward = random.randint(1000, 5000)
            gold_reward = random.randint(500, 2000)
        
        # 随机事件
        event = random.choice(self.RIFT_EVENTS)
        
        # 物品掉落
        items_gained = self._roll_rift_drops(player, rift_level, event["item_chance"])
        
        # 发放奖励
        self.player_repo.add_gold(user_id, gold_reward)
        self.player_repo.add_experience(user_id, exp_reward)
        
        # 发放物品
        for item_name, count in items_gained:
            # 检查是否为丹药
            if self._is_pill_item(item_name):
                # 存入丹药背包
                self.player_repo.add_pill(user_id, item_name, count)
            else:
                # 存入储物戒
                self.storage_ring_repo.add_item(user_id, item_name, count)
        
        # 重置状态
        self.player_repo.update_player_state(user_id, state="idle", extra_data=None)
        
        return RiftResult(
            success=True,
            rift_name=rift_name,
            exp_gained=exp_reward,
            gold_gained=gold_reward,
            items_gained=items_gained,
            event_description=event["desc"]
        )
    
    def exit_rift(self, user_id: str) -> str:
        """退出秘境（放弃探索）"""
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        if player.state != "exploring":
            raise GameException("你当前不在探索秘境")
        
        # 重置状态
        self.player_repo.update_player_state(user_id, state="idle", extra_data=None)
        
        return "✅ 你已退出秘境，本次探索未获得任何奖励。"
    
    def _roll_rift_drops(self, player, rift_level: int, item_chance: int) -> List[Tuple[str, int]]:
        """根据秘境等级随机掉落物品"""
        dropped_items = []
        
        # 检查是否触发物品掉落
        if random.randint(1, 100) > item_chance:
            return dropped_items
        
        # 获取对应等级的掉落表
        drop_table = self.RIFT_DROP_TABLE.get(rift_level, self.RIFT_DROP_TABLE[1])
        
        # 加权随机选择物品
        total_weight = sum(item["weight"] for item in drop_table)
        roll = random.randint(1, total_weight)
        
        current_weight = 0
        for item in drop_table:
            current_weight += item["weight"]
            if roll <= current_weight:
                count = random.randint(item["min"], item["max"])
                dropped_items.append((item["name"], count))
                break
        
        # 高级秘境有50%概率额外掉落一件
        if rift_level >= 2 and random.randint(1, 100) <= 50:
            roll = random.randint(1, total_weight)
            current_weight = 0
            for item in drop_table:
                current_weight += item["weight"]
                if roll <= current_weight:
                    count = random.randint(item["min"], item["max"])
                    dropped_items.append((item["name"], count))
                    break
        
        # 稀有丹药掉落检测
        pill_drops = self._roll_pill_drops(rift_level)
        if pill_drops:
            dropped_items.extend(pill_drops)
        
        return dropped_items
    
    def _roll_pill_drops(self, rift_level: int) -> List[Tuple[str, int]]:
        """根据秘境等级随机掉落稀有丹药"""
        dropped_pills = []
        
        # 获取丹药掉落概率
        pill_chance = self.RIFT_PILL_DROP_CHANCE.get(rift_level, 3)
        
        # 检查是否触发丹药掉落
        if random.randint(1, 100) > pill_chance:
            return dropped_pills
        
        # 获取对应等级的丹药掉落表
        pill_table = self.RIFT_PILL_DROP_TABLE.get(rift_level, self.RIFT_PILL_DROP_TABLE[1])
        
        # 加权随机选择丹药
        total_weight = sum(item["weight"] for item in pill_table)
        roll = random.randint(1, total_weight)
        
        current_weight = 0
        for item in pill_table:
            current_weight += item["weight"]
            if roll <= current_weight:
                count = random.randint(item["min"], item["max"])
                dropped_pills.append((item["name"], count))
                break
        
        return dropped_pills
    
    def _is_pill_item(self, item_name: str) -> bool:
        """检查物品是否为丹药"""
        # 简单判断：包含"丹"字的为丹药
        return "丹" in item_name
    
    def _get_level_name(self, level_index: int) -> str:
        """获取境界名称"""
        # 从配置管理器获取境界名称
        level_data = self.config_manager.level_data
        if 0 <= level_index < len(level_data):
            return level_data[level_index].get("level_name", f"境界{level_index}")
        return f"境界{level_index}"
