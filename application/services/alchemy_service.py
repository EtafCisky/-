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
        # 境界加成：每高一级境界，成功率+2%
        level_bonus = (player.level_index - required_level) * 2
        final_success_rate = min(95, base_success_rate + level_bonus)
        
        # 判断是否成功
        roll = random.randint(1, 100)
        is_success = roll <= final_success_rate
        
        pill_name = recipe["name"]
        
        if is_success:
            # 炼制成功 - 丹药存入储物戒
            synthesized, technique_name = self.storage_ring_repo.add_item(user_id, pill_name, 1)
            
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
                
                if "add_hp" in effects:
                    effect_parts.append(f"恢复{effects['add_hp']}气血")
                if "add_experience" in effects:
                    effect_parts.append(f"增加{effects['add_experience']}修为")
                if "add_breakthrough_bonus" in effects:
                    bonus = int(effects["add_breakthrough_bonus"] * 100)
                    effect_parts.append(f"提升{bonus}%突破率")
                
                if effect_parts:
                    rank = pill_data.get("rank", "")
                    return f"{'，'.join(effect_parts)}（{rank}）"
        
        return "丹药效果"
