"""洞天福地服务"""
import time
from typing import Optional

from ...core.config import ConfigManager
from ...core.exceptions import GameException
from ...domain.models.blessed_land import BlessedLand, BlessedLandInfo
from ...infrastructure.repositories.player_repo import PlayerRepository
from ...infrastructure.repositories.blessed_land_repo import BlessedLandRepository


class BlessedLandService:
    """洞天福地服务"""
    
    # 洞天配置
    BLESSED_LANDS = {
        1: {"name": "小洞天", "price": 10000, "exp_bonus": 0.05, "gold_per_hour": 100, "max_level": 5, "max_exp_per_hour": 5000},
        2: {"name": "中洞天", "price": 50000, "exp_bonus": 0.10, "gold_per_hour": 500, "max_level": 10, "max_exp_per_hour": 15000},
        3: {"name": "大洞天", "price": 200000, "exp_bonus": 0.20, "gold_per_hour": 2000, "max_level": 15, "max_exp_per_hour": 30000},
        4: {"name": "福地", "price": 500000, "exp_bonus": 0.30, "gold_per_hour": 5000, "max_level": 20, "max_exp_per_hour": 50000},
        5: {"name": "洞天福地", "price": 1000000, "exp_bonus": 0.50, "gold_per_hour": 10000, "max_level": 30, "max_exp_per_hour": 100000},
    }
    
    def __init__(
        self,
        player_repo: PlayerRepository,
        blessed_land_repo: BlessedLandRepository,
        config_manager: ConfigManager
    ):
        self.player_repo = player_repo
        self.blessed_land_repo = blessed_land_repo
        self.config_manager = config_manager
    
    def get_blessed_land_info(self, user_id: str) -> BlessedLandInfo:
        """获取洞天信息"""
        # 获取玩家
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        # 获取洞天
        land = self.blessed_land_repo.get_blessed_land(user_id)
        if not land:
            raise GameException("你还没有洞天")
        
        # 计算待收取收益
        now = int(time.time())
        pending_hours, pending_gold = land.calculate_income(now)
        
        # 获取配置
        config = self.BLESSED_LANDS.get(land.land_type, self.BLESSED_LANDS[1])
        max_level = config["max_level"]
        can_upgrade = land.level < max_level
        upgrade_cost = int(config["price"] * land.level * 0.5) if can_upgrade else 0
        
        return BlessedLandInfo(
            land_type=land.land_type,
            land_name=land.land_name,
            level=land.level,
            exp_bonus=land.exp_bonus,
            gold_per_hour=land.gold_per_hour,
            last_collect_time=land.last_collect_time,
            pending_hours=pending_hours,
            pending_gold=pending_gold,
            max_level=max_level,
            upgrade_cost=upgrade_cost,
            can_upgrade=can_upgrade
        )
    
    def purchase_blessed_land(self, user_id: str, land_type: int) -> str:
        """购买洞天"""
        if land_type not in self.BLESSED_LANDS:
            raise GameException("❌ 无效的洞天类型。可选：1-小洞天 2-中洞天 3-大洞天 4-福地 5-洞天福地")
        
        # 获取玩家
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        # 检查是否已有洞天
        existing = self.blessed_land_repo.get_blessed_land(user_id)
        if existing:
            raise GameException(f"❌ 你已拥有【{existing.land_name}】，请先升级而非重新购买")
        
        # 获取配置
        config = self.BLESSED_LANDS[land_type]
        price = config["price"]
        
        if player.gold < price:
            raise GameException(f"❌ 灵石不足！购买{config['name']}需要 {price:,} 灵石")
        
        # 扣除灵石
        self.player_repo.add_gold(user_id, -price)
        
        # 创建洞天
        now = int(time.time())
        self.blessed_land_repo.create_blessed_land(
            user_id=user_id,
            land_type=land_type,
            land_name=config["name"],
            exp_bonus=config["exp_bonus"],
            gold_per_hour=config["gold_per_hour"]
        )
        
        # 更新收取时间
        self.blessed_land_repo.update_blessed_land(user_id, last_collect_time=now)
        
        return (
            f"✨ 恭喜获得【{config['name']}】！\n"
            f"━━━━━━━━━━━━━━━\n"
            f"修炼加成：+{config['exp_bonus']:.0%}\n"
            f"每小时产出：{config['gold_per_hour']} 灵石\n"
            f"━━━━━━━━━━━━━━━\n"
            f"使用 洞天收取 领取产出"
        )
    
    def upgrade_blessed_land(self, user_id: str) -> str:
        """升级洞天"""
        # 获取玩家
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        # 获取洞天
        land = self.blessed_land_repo.get_blessed_land(user_id)
        if not land:
            raise GameException("❌ 你还没有洞天！使用 购买洞天 <类型> 获取")
        
        # 获取配置
        config = self.BLESSED_LANDS.get(land.land_type, self.BLESSED_LANDS[1])
        
        if land.level >= config["max_level"]:
            raise GameException(f"❌ 你的{land.land_name}已达最高等级 {config['max_level']}！")
        
        # 升级费用：基础价格 × 当前等级 × 0.5
        upgrade_cost = int(config["price"] * land.level * 0.5)
        
        if player.gold < upgrade_cost:
            raise GameException(f"❌ 灵石不足！升级需要 {upgrade_cost:,} 灵石")
        
        # 升级加成
        new_level = land.level + 1
        new_exp_bonus = config["exp_bonus"] * (1 + new_level * 0.1)
        new_gold_per_hour = int(config["gold_per_hour"] * (1 + new_level * 0.15))
        
        # 扣除灵石
        self.player_repo.add_gold(user_id, -upgrade_cost)
        
        # 更新洞天
        self.blessed_land_repo.update_blessed_land(
            user_id=user_id,
            level=new_level,
            exp_bonus=new_exp_bonus,
            gold_per_hour=new_gold_per_hour
        )
        
        return (
            f"🎉 {land.land_name}升级到 Lv.{new_level}！\n"
            f"━━━━━━━━━━━━━━━\n"
            f"修炼加成：+{new_exp_bonus:.1%}\n"
            f"每小时产出：{new_gold_per_hour} 灵石\n"
            f"花费：{upgrade_cost:,} 灵石"
        )
    
    def collect_income(self, user_id: str) -> str:
        """收取洞天产出"""
        # 获取玩家
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        # 获取洞天
        land = self.blessed_land_repo.get_blessed_land(user_id)
        if not land:
            raise GameException("❌ 你还没有洞天！")
        
        now = int(time.time())
        
        # 检查冷却
        if not land.can_collect(now):
            remaining = int(3600 - (now - land.last_collect_time))
            minutes = remaining // 60
            raise GameException(f"❌ 收取冷却中，还需 {minutes} 分钟")
        
        # 计算产出
        hours, gold_income = land.calculate_income(now)
        
        if hours == 0:
            raise GameException("❌ 暂无可收取的产出")
        
        # 计算修为收益，并限制上限防止高修为玩家收益无限增长
        config = self.BLESSED_LANDS.get(land.land_type, self.BLESSED_LANDS[1])
        max_exp_per_hour = config.get("max_exp_per_hour", 5000)
        exp_income = int(player.experience * land.exp_bonus * hours * 0.01)
        exp_income = min(exp_income, max_exp_per_hour * hours)
        
        # 增加收益
        self.player_repo.add_gold(user_id, gold_income)
        self.player_repo.add_experience(user_id, exp_income)
        
        # 更新收取时间
        self.blessed_land_repo.update_blessed_land(user_id, last_collect_time=now)
        
        # 重新获取玩家信息
        player = self.player_repo.get_player(user_id)
        
        return (
            f"✅ 洞天收取成功！\n"
            f"━━━━━━━━━━━━━━━\n"
            f"累计时长：{hours} 小时\n"
            f"获得灵石：+{gold_income:,}\n"
            f"获得修为：+{exp_income:,}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"当前灵石：{player.gold:,}"
        )
