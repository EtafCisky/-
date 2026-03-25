"""历练服务"""
import json
import random
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from ...core.config import ConfigManager
from ...core.exceptions import GameException
from ...domain.models.adventure import AdventureRoute, AdventureEvent, AdventureResult
from ...domain.enums import PlayerState
from ...infrastructure.repositories.player_repo import PlayerRepository
from ...infrastructure.repositories.storage_ring_repo import StorageRingRepository


class AdventureService:
    """历练服务"""
    
    def __init__(
        self,
        player_repo: PlayerRepository,
        storage_ring_repo: StorageRingRepository,
        config_manager: ConfigManager
    ):
        self.player_repo = player_repo
        self.storage_ring_repo = storage_ring_repo
        self.config_manager = config_manager
        self.routes: Dict[str, Dict] = {}  # 存储原始路线配置
        self.route_alias_index: Dict[str, str] = {}  # 别名索引
        self.event_groups: Dict[str, List[Dict]] = {}  # 事件组
        self.drop_tables: Dict[str, List[Dict]] = {}  # 掉落表
        self._load_routes()
    
    def _load_routes(self):
        """加载历练路线配置"""
        config_dir = self.config_manager.config_dir
        config_file = config_dir / "adventure_config.json"
        
        if not config_file.exists():
            raise GameException("历练配置文件不存在")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 加载路线
        for route_data in data.get("routes", []):
            key = route_data["key"]
            self.routes[key] = route_data
            
            # 添加别名映射
            aliases = set(route_data.get("aliases", []))
            aliases.add(key)
            aliases.add(route_data["name"])
            
            for alias in aliases:
                self.route_alias_index[alias.lower()] = key
        
        # 加载事件组
        self.event_groups = data.get("event_groups", {})
        
        # 加载掉落表
        self.drop_tables = data.get("drop_tables", {})
    
    def get_route_overview(self) -> List[Dict]:
        """获取路线概览"""
        overview = []
        for route in self.routes.values():
            overview.append({
                "key": route["key"],
                "name": route["name"],
                "risk": route.get("risk", "未知"),
                "duration": route.get("duration", 0),
                "min_level": route.get("min_level", 0),
                "description": route.get("description", ""),
                "aliases": route.get("aliases", [])
            })
        return overview
    
    def start_adventure(self, user_id: str, route_name: str) -> str:
        """开始历练"""
        # 获取玩家
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        # 检查状态
        if player.state != PlayerState.IDLE:
            raise GameException("你当前无法开始历练")
        
        # 查找路线（通过别名索引）
        route_key = self.route_alias_index.get(route_name.lower())
        if not route_key:
            raise GameException(f"未找到历练路线：{route_name}")
        
        route = self.routes.get(route_key)
        if not route:
            raise GameException(f"未找到历练路线：{route_name}")
        
        # 检查境界要求
        min_level = route.get("min_level", 0)
        if player.level_index < min_level:
            raise GameException(f"你的境界还不足以踏上这条路线（需要境界 ≥ {min_level}）")
        
        # 更新玩家状态
        start_time = int(time.time())
        duration = route.get("duration", 3600)
        end_time = start_time + duration
        
        extra_data = {
            "route_key": route_key,
            "route_name": route["name"],
            "start_time": start_time,
            "end_time": end_time
        }
        
        self.player_repo.update_player_state(
            user_id,
            state=PlayerState.ADVENTURING,
            extra_data=json.dumps(extra_data)
        )
        
        # 格式化时间
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        time_str = f"{hours}小时{minutes}分钟" if hours > 0 else f"{minutes}分钟"
        
        # 构建提示信息
        lines = [
            f"✨ 你选择了「{route['name']}」——{route.get('description', '未知冒险')}",
            f"路线风险：{route.get('risk', '未知')} | 历练时长：{time_str}"
        ]
        
        if min_level > 0:
            lines.append(f"建议境界：{min_level} 阶以上")
        
        fatigue = route.get("fatigue_cooldown", 0)
        if fatigue:
            lines.append(f"（该路线完成后需要休整 {fatigue // 60} 分钟）")
        
        return "\n".join(lines)
    
    def check_adventure_status(self, user_id: str) -> str:
        """检查历练状态"""
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        if player.state != PlayerState.ADVENTURING:
            raise GameException("你当前没有进行历练")
        
        # 解析状态数据
        state_data = self.player_repo.get_player_state(user_id)
        if not state_data or not state_data.extra_data:
            raise GameException("历练数据异常")
        
        extra_data = json.loads(state_data.extra_data)
        route_name = extra_data.get("route_name", "未知")
        end_time = extra_data.get("end_time", 0)
        
        current_time = int(time.time())
        remaining = end_time - current_time
        
        if remaining <= 0:
            return f"你的【{route_name}】历练已完成\n请使用【完成历练】命令领取奖励"
        
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        time_str = f"{hours}小时{minutes}分钟" if hours > 0 else f"{minutes}分钟"
        
        return f"你正在进行【{route_name}】历练\n剩余时间：{time_str}"
    
    def finish_adventure(self, user_id: str) -> AdventureResult:
        """完成历练"""
        player = self.player_repo.get_player(user_id)
        if not player:
            raise GameException("你还未踏入修仙之路")
        
        if player.state != PlayerState.ADVENTURING:
            raise GameException("你当前没有进行历练")
        
        # 解析状态数据
        state_data = self.player_repo.get_player_state(user_id)
        if not state_data or not state_data.extra_data:
            raise GameException("历练数据异常")
        
        extra_data = json.loads(state_data.extra_data)
        route_key = extra_data.get("route_key")
        end_time = extra_data.get("end_time", 0)
        
        # 检查是否完成
        current_time = int(time.time())
        if current_time < end_time:
            remaining = end_time - current_time
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            time_str = f"{hours}小时{minutes}分钟" if hours > 0 else f"{minutes}分钟"
            raise GameException(f"历练尚未完成，还需要 {time_str}")
        
        # 获取路线
        route = self.routes.get(route_key)
        if not route:
            raise GameException("历练路线数据异常")
        
        # 计算奖励
        result = self._calculate_rewards(player, route)
        
        # 发放奖励
        self.player_repo.add_gold(user_id, result.gold_gained)
        self.player_repo.add_experience(user_id, result.exp_gained)
        
        # 发放物品
        for item in result.items_gained:
            self.storage_ring_repo.add_item(
                user_id,
                item["name"],
                item["count"]
            )
        
        # 重置状态
        self.player_repo.update_player_state(user_id, state=PlayerState.IDLE, extra_data=None)
        
        return result
    
    def _trigger_route_event(self, route: Dict) -> Dict:
        """触发路线事件"""
        event_weights = route.get("event_weights", {})
        if not event_weights:
            # 默认标准事件
            group_key = "standard"
        else:
            # 按权重随机选择事件组
            total_weight = sum(max(0, w) for w in event_weights.values())
            if total_weight == 0:
                group_key = "standard"
            else:
                rand = random.randint(1, total_weight)
                cumulative = 0
                group_key = "standard"
                
                for key, weight in event_weights.items():
                    cumulative += max(0, weight)
                    if rand <= cumulative:
                        group_key = key
                        break
        
        # 从事件组中随机选择一个事件
        group = self.event_groups.get(group_key, [])
        if not group:
            # 默认事件
            return {
                "key": "default",
                "name": "平稳推进",
                "desc": "历练过程顺风顺水，按部就班地完成既定目标。",
                "exp_mult": 1.0,
                "gold_mult": 1.0,
                "item_chance": 0.35,
                "bonus_progress": 0
            }
        
        return random.choice(group)
    
    def _calculate_rewards(self, player, route: Dict) -> AdventureResult:
        """计算历练奖励"""
        # 基础奖励（按分钟计算）
        duration_minutes = route.get("duration", 3600) // 60
        base_exp_per_min = route.get("base_exp_per_min", 45)
        base_gold_per_min = route.get("base_gold_per_min", 10)
        
        base_exp = duration_minutes * base_exp_per_min
        base_gold = duration_minutes * base_gold_per_min
        
        # 境界加成
        level_bonus_exp = player.level_index * route.get("level_bonus_exp", 12)
        level_bonus_gold = player.level_index * route.get("level_bonus_gold", 3)
        
        # 完成奖励
        completion_bonus = route.get("completion_bonus", {})
        completion_exp = completion_bonus.get("exp", 0)
        completion_gold = completion_bonus.get("gold", 0)
        
        # 总基础奖励
        total_exp = base_exp + level_bonus_exp + completion_exp
        total_gold = base_gold + level_bonus_gold + completion_gold
        
        # 触发随机事件
        event = self._trigger_route_event(route)
        event_type = event.get("key")
        event_description = event.get("desc")
        exp_multiplier = event.get("exp_mult", 1.0)
        gold_multiplier = event.get("gold_mult", 1.0)
        item_chance = event.get("item_chance", 0.35) / 100.0  # 转换为小数
        
        # 应用事件倍率
        final_exp = max(0, int(total_exp * exp_multiplier))
        final_gold = max(0, int(total_gold * gold_multiplier))
        
        # 随机掉落物品
        items_gained = []
        if random.random() <= item_chance:
            drop_tier = route.get("drop_tier", "low")
            drop_table = self.drop_tables.get(drop_tier, [])
            
            if drop_table:
                # 按权重选择掉落物品
                total_weight = sum(drop.get("weight", 1) for drop in drop_table)
                rand_weight = random.uniform(0, total_weight)
                cumulative_weight = 0.0
                
                for drop_data in drop_table:
                    cumulative_weight += drop_data.get("weight", 1)
                    if rand_weight <= cumulative_weight:
                        min_count = drop_data.get("min", 1)
                        max_count = drop_data.get("max", 1)
                        count = random.randint(min_count, max_count)
                        items_gained.append({
                            "name": drop_data["name"],
                            "count": count
                        })
                        break
        
        return AdventureResult(
            success=True,
            gold_gained=final_gold,
            exp_gained=final_exp,
            items_gained=items_gained,
            event_type=event_type,
            event_description=event_description,
            fatigue_cost=route.get("fatigue_cooldown", 0)
        )
