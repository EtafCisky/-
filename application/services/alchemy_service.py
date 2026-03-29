"""
炼丹服务层

处理炼丹相关的业务逻辑。
"""
import random
from typing import Optional, Tuple, Dict, List
from pathlib import Path

from ...domain.models.player import Player
from ...infrastructure.repositories.player_repo import PlayerRepository
from ...infrastructure.repositories.storage_ring_repo import StorageRingRepository
from ...core.config import ConfigManager
from ...core.exceptions import BusinessException
from .recipe_manager import RecipeManager
from ...domain.models.recipe import Recipe


class AlchemyService:
    """炼丹服务"""
    
    def __init__(
        self,
        player_repo: PlayerRepository,
        storage_ring_repo: StorageRingRepository,
        config_manager: ConfigManager,
    ):
        """
        初始化炼丹服务
        
        Args:
            player_repo: 玩家仓储
            storage_ring_repo: 储物戒仓储
            config_manager: 配置管理器
        """
        self.player_repo = player_repo
        self.storage_ring_repo = storage_ring_repo
        self.config_manager = config_manager
        self._recipes_cache = None
        
        # 初始化配方管理器
        try:
            self.recipe_manager = RecipeManager()
            self.recipe_manager.load_recipes()
        except Exception as e:
            print(f"警告：无法加载配方管理器: {e}")
            self.recipe_manager = None
    
    def _load_recipes(self) -> Dict[int, Dict]:
        """加载炼丹配方"""
        if self._recipes_cache is not None:
            return self._recipes_cache
        
        recipes_config = self.config_manager.get_config("alchemy_recipes")
        if not recipes_config:
            return {}
        
        self._recipes_cache = {}
        for recipe in recipes_config:
            recipe_id = recipe.get("id")
            if recipe_id:
                self._recipes_cache[recipe_id] = recipe
        
        return self._recipes_cache
    
    def get_available_recipes(self, user_id: str) -> List[Dict]:
        """
        获取玩家可用的炼丹配方
        
        Args:
            user_id: 用户ID
            
        Returns:
            可用配方列表
            
        Raises:
            BusinessException: 玩家不存在
        """
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        recipes = self._load_recipes()
        available = []
        
        for recipe_id, recipe in recipes.items():
            required_level = recipe.get("level_required", 0)
            if player.level_index >= required_level:
                available.append(recipe)
        
        return available
    
    def get_recipe(self, recipe_id: int) -> Optional[Dict]:
        """
        获取指定配方
        
        Args:
            recipe_id: 配方ID
            
        Returns:
            配方字典，如果不存在则返回None
        """
        recipes = self._load_recipes()
        return recipes.get(recipe_id)
    
    def get_recipe_by_pill_id(self, pill_id: str) -> Optional[Recipe]:
        """
        通过丹药ID获取配方（使用新的配方管理器）
        
        Args:
            pill_id: 丹药ID
            
        Returns:
            配方对象，如果不存在则返回None
        """
        if self.recipe_manager:
            return self.recipe_manager.get_recipe_by_pill_id(pill_id)
        return None
    
    def get_recipe_by_name(self, pill_name: str) -> Optional[Recipe]:
        """
        通过丹药名称获取配方（使用新的配方管理器）
        
        Args:
            pill_name: 丹药名称
            
        Returns:
            配方对象，如果不存在则返回None
        """
        if self.recipe_manager:
            return self.recipe_manager.get_recipe_by_name(pill_name)
        return None
    
    def craft_pill(self, user_id: str, recipe_id: int) -> Tuple[bool, str, Dict]:
        """
        炼制丹药
        
        Args:
            user_id: 用户ID
            recipe_id: 配方ID
            
        Returns:
            (是否成功, 消息, 结果数据)
            
        Raises:
            BusinessException: 各种业务异常
        """
        # 获取玩家
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        # 检查玩家状态
        if not player.can_cultivate():  # 使用 can_cultivate 检查是否空闲
            raise BusinessException(f"当前状态「{player.state.value}」无法炼丹")
        
        # 获取配方
        recipe = self.get_recipe(recipe_id)
        if not recipe:
            raise BusinessException("无效的配方ID")
        
        # 检查境界要求
        required_level = recipe.get("level_required", 0)
        if player.level_index < required_level:
            raise BusinessException(
                f"炼制{recipe['name']}需要达到境界等级 {required_level}（当前：{player.level_index}）"
            )
        
        # 检查材料
        materials = recipe.get("materials", {})
        missing_materials = []
        
        # 检查灵石
        required_gold = materials.get("灵石", 0)
        if player.gold < required_gold:
            missing_materials.append(f"灵石（需要{required_gold}，拥有{player.gold}）")
        
        # 检查储物戒中的材料
        for material_name, required_count in materials.items():
            if material_name == "灵石":
                continue
            
            current_count = self.storage_ring_repo.get_item_count(user_id, material_name)
            if current_count < required_count:
                missing_materials.append(
                    f"{material_name}（需要{required_count}，拥有{current_count}）"
                )
        
        if missing_materials:
            raise BusinessException("材料不足！\n" + "\n".join(f"  · {m}" for m in missing_materials))
        
        # 扣除材料
        player.gold -= required_gold
        
        consumed_materials = []
        for material_name, required_count in materials.items():
            if material_name == "灵石":
                continue
            
            self.storage_ring_repo.remove_item(user_id, material_name, required_count)
            consumed_materials.append(f"{material_name}×{required_count}")
        
        # 计算成功率
        base_success_rate = recipe.get("success_rate", 50)
        # 炼丹职业加成：每级增加0.5%成功率
        alchemy_bonus = player.get_alchemy_success_bonus()
        final_success_rate = min(95, base_success_rate + alchemy_bonus)
        
        # 判断是否成功
        roll = random.randint(1, 100)
        is_success = roll <= final_success_rate
        
        pill_name = recipe["name"]
        
        if is_success:
            # 炼制成功 - 丹药存入储物戒
            if pill_name in player.storage_ring_items:
                player.storage_ring_items[pill_name] += 1
            else:
                player.storage_ring_items[pill_name] = 1
            
            self.player_repo.save(player)
            
            # 构建消耗材料显示
            cost_lines = []
            if required_gold > 0:
                cost_lines.append(f"灵石 -{required_gold}")
            cost_lines.extend(consumed_materials)
            cost_str = "、".join(cost_lines) if cost_lines else "无"
            
            message = f"""🎉 炼丹成功！
━━━━━━━━━━━━━━━

你成功炼制了【{pill_name}】！
丹药已存入储物戒

消耗：{cost_str}
成功率：{final_success_rate}%

💡 使用 服用丹药 {pill_name} 可服用此丹药
💡 使用 储物戒 查看所有物品"""
            
            result_data = {
                "success": True,
                "pill_name": pill_name,
                "cost": required_gold,
                "materials_consumed": consumed_materials,
                "success_rate": final_success_rate,
            }
        else:
            # 炼制失败
            self.player_repo.save(player)
            
            # 构建消耗材料显示
            cost_lines = []
            if required_gold > 0:
                cost_lines.append(f"灵石 -{required_gold}")
            cost_lines.extend(consumed_materials)
            cost_str = "、".join(cost_lines) if cost_lines else "无"
            
            message = f"""💔 炼丹失败
━━━━━━━━━━━━━━━

炼制【{pill_name}】失败了...

材料已消耗
消耗：{cost_str}
成功率：{final_success_rate}%

再接再厉！"""
            
            result_data = {
                "success": False,
                "pill_name": pill_name,
                "cost": required_gold,
                "materials_consumed": consumed_materials,
                "success_rate": final_success_rate,
            }
        
        return is_success, message, result_data
    
    def format_recipes(self, user_id: str) -> str:
        """
        格式化配方列表显示
        
        Args:
            user_id: 用户ID
            
        Returns:
            格式化后的字符串
            
        Raises:
            BusinessException: 玩家不存在
        """
        available_recipes = self.get_available_recipes(user_id)
        
        if not available_recipes:
            return "❌ 你当前境界无法炼制任何丹药！"
        
        lines = ["🔥 丹药配方", "━━━━━━━━━━━━━━━", ""]
        
        for recipe in available_recipes:
            materials = recipe.get("materials", {})
            materials_str = "、".join([f"{k}×{v}" for k, v in materials.items()])
            
            lines.append(f"【{recipe['name']}】(ID:{recipe['id']})")
            lines.append(f"  需求境界：Lv.{recipe.get('level_required', 0)}")
            lines.append(f"  材料：{materials_str}")
            lines.append(f"  成功率：{recipe.get('success_rate', 50)}%")
            
            # 获取丹药效果描述
            desc = self._get_pill_description(recipe['name'])
            if desc:
                lines.append(f"  效果：{desc}")
            
            lines.append("")
        
        lines.append("使用 炼丹 <配方ID> 开始炼制")
        
        return "\n".join(lines)
    
    def _get_pill_description(self, pill_name: str) -> str:
        """
        获取丹药效果描述
        
        Args:
            pill_name: 丹药名称
            
        Returns:
            效果描述
        """
        # 从配置中查找丹药
        pills_config = self.config_manager.get_config("pills")
        if not pills_config:
            return "丹药效果"
        
        # 遍历查找匹配的丹药
        for pill_id, pill_data in pills_config.items():
            if pill_data.get("name") == pill_name:
                description = pill_data.get("description", "")
                if description:
                    return description
                
                # 根据效果生成描述
                effects = pill_data.get("effect", {})
                effect_parts = []
                
                # 修为加成（显示数值）
                if "add_experience" in effects:
                    exp = effects["add_experience"]
                    if exp > 0:
                        effect_parts.append(f"增加{exp}修为")
                    elif exp < 0:
                        effect_parts.append(f"减少{abs(exp)}修为")
                
                # 突破率加成（显示数值）
                if "add_breakthrough_bonus" in effects:
                    bonus = int(effects["add_breakthrough_bonus"] * 100)
                    effect_parts.append(f"提升{bonus}%突破率")
                
                # 气血效果（不显示数值）
                if "add_hp" in effects:
                    hp = effects["add_hp"]
                    if hp > 0:
                        effect_parts.append("恢复气血")
                    elif hp < 0:
                        effect_parts.append("损失气血")
                
                # 气血上限（不显示数值）
                if "add_max_hp" in effects:
                    max_hp = effects["add_max_hp"]
                    if max_hp > 0:
                        effect_parts.append("提升气血上限")
                    elif max_hp < 0:
                        effect_parts.append("降低气血上限")
                
                # 精神力（不显示数值）
                if "add_mental_power" in effects:
                    mp = effects["add_mental_power"]
                    if mp > 0:
                        effect_parts.append("提升精神力")
                    elif mp < 0:
                        effect_parts.append("损失精神力")
                
                # 攻击力（不显示数值）
                if "add_attack" in effects:
                    atk = effects["add_attack"]
                    if atk > 0:
                        effect_parts.append("提升攻击力")
                    elif atk < 0:
                        effect_parts.append("降低攻击力")
                
                # 防御力（不显示数值）
                if "add_defense" in effects:
                    def_val = effects["add_defense"]
                    if def_val > 0:
                        effect_parts.append("提升防御力")
                    elif def_val < 0:
                        effect_parts.append("降低防御力")
                
                # 灵力（不显示数值）
                if "add_spiritual_power" in effects:
                    sp = effects["add_spiritual_power"]
                    if sp > 0:
                        effect_parts.append("提升灵力")
                    elif sp < 0:
                        effect_parts.append("损失灵力")
                
                # 灵石消耗（不显示数值）
                if "add_gold" in effects and effects["add_gold"] < 0:
                    effect_parts.append("消耗灵石")
                
                if effect_parts:
                    rank = pill_data.get("rank", "")
                    return f"{'，'.join(effect_parts)}（{rank}）"
        
        return "丹药效果"

    def craft_pill_by_name(self, user_id: str, pill_name: str) -> Tuple[bool, str, Dict]:
        """
        通过丹药名称炼制丹药（使用新配方系统）
        
        Args:
            user_id: 用户ID
            pill_name: 丹药名称
            
        Returns:
            (是否成功, 消息, 结果数据)
            
        Raises:
            BusinessException: 各种业务异常
        """
        # 获取玩家
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        # 检查玩家状态
        if not player.can_cultivate():
            raise BusinessException(f"当前状态「{player.state.value}」无法炼丹")
        
        # 获取配方
        recipe = self.get_recipe_by_name(pill_name)
        if not recipe:
            raise BusinessException(f"未找到【{pill_name}】的炼制配方")
        
        # 检查境界要求
        if player.level_index < recipe.level_required:
            raise BusinessException(
                f"炼制【{recipe.name}】需要达到境界等级 {recipe.level_required}（当前：{player.level_index}）"
            )
        
        # 检查材料
        missing_materials = []
        
        # 检查储物戒中的材料
        for material_name, required_count in recipe.materials.items():
            current_count = self.storage_ring_repo.get_item_count(user_id, material_name)
            if current_count < required_count:
                missing_materials.append(
                    f"{material_name}（需要{required_count}，拥有{current_count}）"
                )
        
        if missing_materials:
            raise BusinessException("材料不足！\n" + "\n".join(f"  · {m}" for m in missing_materials))
        
        # 扣除材料
        consumed_materials = []
        for material_name, required_count in recipe.materials.items():
            self.storage_ring_repo.remove_item(user_id, material_name, required_count)
            consumed_materials.append(f"{material_name}×{required_count}")
        
        # 计算成功率
        base_success_rate = recipe.success_rate
        # 炼丹职业加成：每级增加0.5%成功率
        alchemy_bonus = player.get_alchemy_success_bonus()
        final_success_rate = min(95, base_success_rate + alchemy_bonus)
        
        # 判断是否成功
        roll = random.randint(1, 100)
        is_success = roll <= final_success_rate
        
        if is_success:
            # 炼制成功 - 丹药存入储物戒
            self.storage_ring_repo.add_item(user_id, recipe.name, 1)
            
            # 增加炼丹经验
            alchemy_exp_gain = self._calculate_alchemy_exp(recipe.rank)
            level_up = player.add_alchemy_exp(alchemy_exp_gain)
            self.player_repo.save(player)
            
            # 构建消耗材料显示
            cost_str = "、".join(consumed_materials) if consumed_materials else "无"
            
            # 构建升级提示
            level_up_msg = ""
            if level_up:
                level_up_msg = f"\n\n🎊 炼丹等级提升！\n当前等级：Lv.{player.alchemy_level} {player.get_alchemy_title()}"
            
            message = f"""🎉 炼丹成功！
━━━━━━━━━━━━━━━

你成功炼制了【{recipe.name}】！
丹药已存入储物戒

品质：{recipe.rank}
消耗：{cost_str}
成功率：{final_success_rate}%
炼丹经验：+{alchemy_exp_gain}{level_up_msg}

💡 使用 服用丹药 {recipe.name} 可服用此丹药
💡 使用 储物戒 查看所有物品"""
            
            result_data = {
                "success": True,
                "pill_name": recipe.name,
                "rank": recipe.rank,
                "materials_consumed": consumed_materials,
                "success_rate": final_success_rate,
            }
        else:
            # 炼制失败 - 失败也给予少量经验
            alchemy_exp_gain = self._calculate_alchemy_exp(recipe.rank) // 3  # 失败给1/3经验
            level_up = player.add_alchemy_exp(alchemy_exp_gain)
            self.player_repo.save(player)
            
            # 构建消耗材料显示
            cost_str = "、".join(consumed_materials) if consumed_materials else "无"
            
            # 构建升级提示
            level_up_msg = ""
            if level_up:
                level_up_msg = f"\n\n🎊 炼丹等级提升！\n当前等级：Lv.{player.alchemy_level} {player.get_alchemy_title()}"
            
            message = f"""💔 炼丹失败
━━━━━━━━━━━━━━━

炼制【{recipe.name}】失败了...

材料已消耗
消耗：{cost_str}
成功率：{final_success_rate}%
炼丹经验：+{alchemy_exp_gain}{level_up_msg}

再接再厉！"""
            
            result_data = {
                "success": False,
                "pill_name": recipe.name,
                "rank": recipe.rank,
                "materials_consumed": consumed_materials,
                "success_rate": final_success_rate,
            }
        
        return is_success, message, result_data
    
    def format_new_recipes(self, user_id: str) -> str:
        """
        格式化新配方系统的配方列表显示
        
        Args:
            user_id: 用户ID
            
        Returns:
            格式化后的字符串
            
        Raises:
            BusinessException: 玩家不存在
        """
        if not self.recipe_manager:
            return "❌ 配方系统未初始化"
        
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        # 获取所有配方
        all_recipes = self.recipe_manager.get_all_recipes()
        
        # 筛选玩家可用的配方
        available_recipes = [
            recipe for recipe in all_recipes
            if player.level_index >= recipe.level_required
        ]
        
        if not available_recipes:
            return "❌ 你当前境界无法炼制任何丹药！"
        
        # 按品质和等级排序
        rank_order = {"凡品": 0, "灵品": 1, "珍品": 2, "圣品": 3, "帝品": 4, "道品": 5, "仙品": 6, "神品": 7}
        available_recipes.sort(key=lambda r: (rank_order.get(r.rank, 99), r.level_required))
        
        # 获取炼丹职业信息
        alchemy_title = player.get_alchemy_title()
        alchemy_level = player.alchemy_level
        success_bonus = player.get_alchemy_success_bonus()
        
        lines = [
            "🔥 丹药配方（新系统）",
            "━━━━━━━━━━━━━━━",
            f"炼丹职业：Lv.{alchemy_level} {alchemy_title}",
            f"成功率加成：+{success_bonus}%",
            ""
        ]
        
        for recipe in available_recipes:
            materials_str = "、".join([f"{k}×{v}" for k, v in recipe.materials.items()])
            
            lines.append(f"【{recipe.name}】({recipe.rank})")
            lines.append(f"  需求境界：Lv.{recipe.level_required}")
            lines.append(f"  材料：{materials_str}")
            lines.append(f"  成功率：{recipe.success_rate}%")
            lines.append(f"  成本：{recipe.cost}灵石")
            lines.append("")
        
        lines.append("使用 炼丹 <丹药名称> 开始炼制")
        
        return "\n".join(lines)

    def _calculate_alchemy_exp(self, pill_rank: str) -> int:
        """
        根据丹药品质计算炼丹经验
        
        Args:
            pill_rank: 丹药品质
            
        Returns:
            炼丹经验值
        """
        exp_map = {
            "凡品": 10,
            "灵品": 20,
            "珍品": 30,
            "圣品": 50,
            "帝品": 80,
            "道品": 120,
            "仙品": 180,
            "神品": 250
        }
        return exp_map.get(pill_rank, 10)
    
    def get_alchemy_info(self, user_id: str) -> str:
        """
        获取玩家炼丹职业信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            格式化的炼丹信息
            
        Raises:
            BusinessException: 玩家不存在
        """
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        title = player.get_alchemy_title()
        level = player.alchemy_level
        exp = player.alchemy_exp
        required_exp = player.get_required_alchemy_exp()
        success_bonus = player.get_alchemy_success_bonus()
        
        # 计算经验进度条
        exp_percentage = (exp / required_exp * 100) if required_exp > 0 else 0
        bar_length = 20
        filled = int(bar_length * exp / required_exp) if required_exp > 0 else 0
        bar = "█" * filled + "░" * (bar_length - filled)
        
        message = f"""🔥 炼丹职业信息
━━━━━━━━━━━━━━━

称号：{title}
等级：Lv.{level}
经验：{exp}/{required_exp}
进度：[{bar}] {exp_percentage:.1f}%

成功率加成：+{success_bonus}%

💡 炼制丹药可获得炼丹经验
💡 每级增加0.5%成功率加成
💡 失败也能获得少量经验"""
        
        return message
