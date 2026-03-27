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
    
    # 稀有掉落子类别（按掉落等级分组）
    # 包含：天材地宝、炼器材料、法器、功法
    RARE_DROP_SUBTYPES = {
        "low": {  # 低级掉落 - 凡品
            "天材地宝": [
                {"name": "百年灵芝", "weight": 35},
                {"name": "紫玉参", "weight": 30},
                {"name": "青莲子", "weight": 25},
                {"name": "赤血果", "weight": 10},
            ],
            "炼器材料": [
                {"name": "寒铁精", "weight": 40},
                {"name": "赤铜矿", "weight": 35},
                {"name": "灵木芯", "weight": 25},
            ],
            "法器": [
                {"name": "青锋剑", "weight": 50},
                {"name": "玄铁甲", "weight": 50},
            ],
            "功法": [
                {"name": "长春功残篇", "weight": 70},
                {"name": "御风诀残篇", "weight": 28},
                {"name": "长春功", "weight": 1},  # 完整功法，极低概率（5个残篇合成）
                {"name": "御风诀", "weight": 1},  # 完整功法，极低概率（5个残篇合成）
            ],
        },
        "mid": {  # 中级掉落 - 珍品
            "天材地宝": [
                {"name": "千年灵芝", "weight": 30},
                {"name": "九转仙草", "weight": 25},
                {"name": "龙血果", "weight": 20},
                {"name": "凤凰羽", "weight": 15},
                {"name": "玄冰莲", "weight": 10},
            ],
            "炼器材料": [
                {"name": "紫金沙", "weight": 35},
                {"name": "星辉晶砂", "weight": 30},
                {"name": "赤炎石", "weight": 25},
                {"name": "月光粉尘", "weight": 10},
            ],
            "法器": [
                {"name": "烈阳刀", "weight": 40},
                {"name": "月华袍", "weight": 40},
                {"name": "镇魂幡", "weight": 20},
            ],
            "功法": [
                {"name": "不动明王经残篇", "weight": 50},
                {"name": "北冥神功残篇", "weight": 30},
                {"name": "九阳神功残篇", "weight": 17},
                {"name": "不动明王经", "weight": 1},  # 完整功法（10个残篇合成）
                {"name": "北冥神功", "weight": 1},  # 完整功法（10个残篇合成）
                {"name": "九阳神功", "weight": 1},  # 完整功法（10个残篇合成）
            ],
        },
        "high": {  # 高级掉落 - 圣品/帝品
            "天材地宝": [
                {"name": "万年灵芝王", "weight": 25},
                {"name": "九天息壤", "weight": 20},
                {"name": "太阳神果", "weight": 18},
                {"name": "太阴神花", "weight": 18},
                {"name": "混沌青莲", "weight": 12},
                {"name": "不死神药", "weight": 7},
            ],
            "炼器材料": [
                {"name": "玄冰之核", "weight": 30},
                {"name": "龙骨髓", "weight": 25},
                {"name": "凤凰真羽", "weight": 20},
                {"name": "星辰陨铁", "weight": 15},
                {"name": "混沌神石", "weight": 10},
            ],
            "法器": [
                {"name": "寒霜剑", "weight": 35},
                {"name": "泰坦之铠", "weight": 30},
                {"name": "妖精之弓", "weight": 25},
                {"name": "戮仙剑阵", "weight": 8},
                {"name": "弑神枪", "weight": 2},
            ],
            "功法": [
                {"name": "焚天诀残篇", "weight": 40},
                {"name": "道经残篇", "weight": 30},
                {"name": "吞天魔功残篇", "weight": 20},
                {"name": "他化自在大法残篇", "weight": 9},
                {"name": "焚天诀", "weight": 0.4},  # 完整功法（15个残篇合成）
                {"name": "道经", "weight": 0.3},  # 完整帝品功法（15个残篇合成）
                {"name": "吞天魔功", "weight": 0.2},  # 完整功法（15个残篇合成）
                {"name": "他化自在大法", "weight": 0.1},  # 完整功法（15个残篇合成）
            ],
        },
    }
    
    # 功法残篇合成配置
    TECHNIQUE_SYNTHESIS = {
        # 凡品功法 - 5个残篇合成
        "长春功": {"fragment": "长春功残篇", "required": 5, "tier": "凡品"},
        "御风诀": {"fragment": "御风诀残篇", "required": 5, "tier": "凡品"},
        # 珍品功法 - 10个残篇合成
        "不动明王经": {"fragment": "不动明王经残篇", "required": 10, "tier": "珍品"},
        "北冥神功": {"fragment": "北冥神功残篇", "required": 10, "tier": "珍品"},
        "九阳神功": {"fragment": "九阳神功残篇", "required": 10, "tier": "珍品"},
        # 圣品/帝品功法 - 15个残篇合成
        "焚天诀": {"fragment": "焚天诀残篇", "required": 15, "tier": "圣品"},
        "道经": {"fragment": "道经残篇", "required": 15, "tier": "帝品"},
        "吞天魔功": {"fragment": "吞天魔功残篇", "required": 15, "tier": "圣品"},
        "他化自在大法": {"fragment": "他化自在大法残篇", "required": 15, "tier": "圣品"},
    }
    
    # 稀有掉落类别权重（决定掉落哪个类别）
    RARE_DROP_CATEGORY_WEIGHTS = {
        "low": {"天材地宝": 40, "炼器材料": 35, "法器": 20, "功法": 5},
        "mid": {"天材地宝": 35, "炼器材料": 30, "法器": 25, "功法": 10},
        "high": {"天材地宝": 30, "炼器材料": 25, "法器": 30, "功法": 15},
    }
    
    def __init__(
        self,
        player_repo: PlayerRepository,
        storage_ring_repo: StorageRingRepository,
        config_manager: ConfigManager,
        bounty_repo=None  # 添加可选的悬赏仓储
    ):
        self.player_repo = player_repo
        self.storage_ring_repo = storage_ring_repo
        self.config_manager = config_manager
        self.bounty_repo = bounty_repo  # 保存悬赏仓储引用
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
        synthesis_messages = []
        for item in result.items_gained:
            synthesized, technique_name = self.storage_ring_repo.add_item(
                user_id,
                item["name"],
                item["count"]
            )
            if synthesized:
                # 获取功法品质
                tier = self.storage_ring_repo.TECHNIQUE_SYNTHESIS.get(technique_name, {}).get("tier", "未知")
                synthesis_messages.append(f"✨ 恭喜！你集齐了残篇，自动合成了【{tier}】功法《{technique_name}》！")
        
        # 如果有合成信息，添加到结果描述中
        if synthesis_messages:
            result.event_description += "\n\n" + "\n".join(synthesis_messages)
        
        # 重置状态
        self.player_repo.update_player_state(user_id, state=PlayerState.IDLE, extra_data=None)
        
        # 更新悬赏进度
        if self.bounty_repo:
            try:
                self._update_bounty_progress(user_id, route, result)
            except Exception as e:
                # 悬赏更新失败不影响历练完成
                pass
        
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
                        # 检查是否为类别物品（需要二级掉落）
                        item_name = self._resolve_item_category(drop_data["name"], drop_tier)
                        items_gained.append({
                            "name": item_name,
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
    
    def _update_bounty_progress(self, user_id: str, route: Dict, result: AdventureResult):
        """更新悬赏进度"""
        # 获取路线的悬赏标签
        bounty_tag = route.get("bounty_tag")
        if not bounty_tag:
            return
        
        # 获取进行中的悬赏任务
        active_bounty = self.bounty_repo.get_active_bounty(user_id)
        if not active_bounty:
            return
        
        # 检查任务是否已过期
        if int(time.time()) > active_bounty.expire_time:
            return
        
        # 检查标签是否匹配（从配置加载悬赏模板）
        try:
            import json
            from pathlib import Path
            config_file = self.config_manager.config_dir / "bounty_templates.json"
            if not config_file.exists():
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                bounty_config = json.load(f)
            
            templates = bounty_config.get("templates", [])
            template = next((t for t in templates if t["id"] == active_bounty.bounty_id), None)
            
            if not template:
                return
            
            progress_tags = template.get("progress_tags", [])
            if bounty_tag not in progress_tags:
                return
            
            # 计算进度增加量
            base_progress = route.get("bounty_progress", 1)
            # 事件可能提供额外进度
            # 这里简化处理，直接使用基础进度
            progress_to_add = base_progress
            
            # 更新进度
            new_progress = min(
                active_bounty.current_progress + progress_to_add,
                active_bounty.target_count
            )
            
            self.bounty_repo.update_progress(user_id, new_progress)
            
        except Exception:
            # 静默失败
            pass
    
    def _resolve_item_category(self, item_name: str, drop_tier: str) -> str:
        """
        解析物品类别，如果是类别物品则进行二级掉落
        
        Args:
            item_name: 物品名称（可能是类别）
            drop_tier: 掉落等级（low/mid/high）
            
        Returns:
            具体的物品名称
        """
        # 检查是否为"稀有掉落"类别
        if item_name == "稀有掉落":
            return self._roll_rare_drop(drop_tier)
        
        # 其他物品直接返回
        return item_name
    
    def _roll_rare_drop(self, drop_tier: str) -> str:
        """
        从稀有掉落中随机选择一种物品（二级掉落）
        
        流程：
        1. 根据掉落等级选择类别（天材地宝、炼器材料、法器、功法）
        2. 从选中的类别中随机选择具体物品
        
        Args:
            drop_tier: 掉落等级（决定掉落品质和类别权重）
            
        Returns:
            具体的物品名称
        """
        # 第一步：选择类别
        category_weights = self.RARE_DROP_CATEGORY_WEIGHTS.get(drop_tier, self.RARE_DROP_CATEGORY_WEIGHTS["low"])
        total_weight = sum(category_weights.values())
        roll = random.randint(1, total_weight)
        
        current_weight = 0
        selected_category = None
        for category, weight in category_weights.items():
            current_weight += weight
            if roll <= current_weight:
                selected_category = category
                break
        
        if not selected_category:
            selected_category = "天材地宝"  # 兜底
        
        # 第二步：从选中的类别中选择具体物品
        item_table = self.RARE_DROP_SUBTYPES.get(drop_tier, {}).get(selected_category, [])
        if not item_table:
            # 兜底：返回默认物品
            return "灵草"
        
        # 加权随机选择
        total_weight = sum(item["weight"] for item in item_table)
        roll = random.randint(1, total_weight)
        
        current_weight = 0
        for item in item_table:
            current_weight += item["weight"]
            if roll <= current_weight:
                return item["name"]
        
        # 兜底：返回第一个
        return item_table[0]["name"]
