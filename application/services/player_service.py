"""玩家业务服务"""
import random
from datetime import datetime
from typing import Optional

from ...core.config import ConfigManager
from ...core.exceptions import (
    PlayerAlreadyExistsException,
    PlayerNotFoundException,
    InvalidParameterException
)
from ...domain.models.player import Player
from ...domain.enums import CultivationType
from ...domain.factories import PlayerFactory
from ...infrastructure.repositories.player_repo import PlayerRepository
from ...utils.spirit_root_generator import SpiritRootGenerator


class PlayerService:
    """玩家业务服务"""
    
    def __init__(
        self,
        player_repo: PlayerRepository,
        config_manager: ConfigManager
    ):
        self.player_repo = player_repo
        self.config_manager = config_manager
        self.spirit_root_generator = SpiritRootGenerator(config_manager)
    
    def create_player(
        self,
        user_id: str,
        cultivation_type: CultivationType,
        user_name: Optional[str] = None
    ) -> Player:
        """
        创建玩家
        
        Args:
            user_id: 用户ID
            cultivation_type: 修炼类型
            user_name: 用户名（QQ昵称），如果提供则使用，否则使用默认格式
            
        Returns:
            创建的玩家对象
            
        Raises:
            PlayerAlreadyExistsException: 玩家已存在
        """
        # 检查是否已存在（在事务外检查，避免不必要的事务开销）
        if self.player_repo.exists(user_id):
            raise PlayerAlreadyExistsException(user_id)
        
        # 生成灵根
        spirit_root = self.spirit_root_generator.generate_random_root()
        
        # 获取初始灵石配置
        initial_gold = self.config_manager.settings.values.initial_gold
        
        # 创建玩家
        player = PlayerFactory.create_new_player(
            user_id=user_id,
            cultivation_type=cultivation_type,
            spirit_root=spirit_root,
            initial_gold=initial_gold,
            user_name=user_name
        )
        
        # 保存（JSONStorage 自动处理原子写入）
        self.player_repo.save(player)
        
        return player
    
    def get_player(self, user_id: str) -> Optional[Player]:
        """
        获取玩家
        
        Args:
            user_id: 用户ID
            
        Returns:
            玩家对象，不存在则返回None
        """
        return self.player_repo.get_by_id(user_id)
    
    def get_player_or_raise(self, user_id: str) -> Player:
        """
        获取玩家，不存在则抛出异常
        
        Args:
            user_id: 用户ID
            
        Returns:
            玩家对象
            
        Raises:
            PlayerNotFoundException: 玩家不存在
        """
        player = self.player_repo.get_by_id(user_id)
        if player is None:
            raise PlayerNotFoundException(user_id)
        return player
    
    def update_player(self, player: Player) -> None:
        """
        更新玩家
        
        Args:
            player: 玩家对象
        """
        # JSONStorage 自动处理原子写入
        self.player_repo.save(player)
    
    def check_in(self, player: Player) -> int:
        """
        每日签到
        
        Args:
            player: 玩家对象
            
        Returns:
            获得的灵石数量
            
        Raises:
            ValueError: 今日已签到
        """
        # 获取今天的日期
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 检查是否已签到
        if player.last_check_in_date == today:
            raise ValueError("今日已经签到过了")
        
        # 获取签到奖励范围
        settings = self.config_manager.settings.values
        gold_min = settings.check_in_gold_min
        gold_max = settings.check_in_gold_max
        
        # 确保最小值不大于最大值
        if gold_min > gold_max:
            gold_min, gold_max = gold_max, gold_min
        
        # 生成随机奖励
        reward_gold = random.randint(gold_min, gold_max)
        
        # 更新玩家数据
        player.add_gold(reward_gold)
        player.last_check_in_date = today
        
        # 保存（JSONStorage 自动处理原子写入）
        self.player_repo.save(player)
        
        return reward_gold
    
    def change_nickname(self, player: Player, new_nickname: str) -> None:
        """
        修改道号
        
        Args:
            player: 玩家对象
            new_nickname: 新道号
            
        Raises:
            InvalidParameterException: 道号无效
        """
        # 验证道号
        new_nickname = new_nickname.strip()
        
        if not new_nickname:
            raise InvalidParameterException("道号", "道号不能为空")
        
        if len(new_nickname) > 12:
            raise InvalidParameterException("道号", "道号长度不能超过12个字符")
        
        # 检查是否与其他玩家重复
        existing = self.player_repo.get_by_nickname(new_nickname)
        if existing and existing.user_id != player.user_id:
            raise InvalidParameterException("道号", "该道号已被其他道友使用")
        
        # 更新道号
        player.nickname = new_nickname
        player.user_name = new_nickname
        
        # 保存（JSONStorage 自动处理原子写入）
        self.player_repo.save(player)
    
    def change_name(self, player: Player, new_name: str) -> None:
        """
        修改道友名字（nickname）
        
        Args:
            player: 玩家对象
            new_name: 新名字
            
        Raises:
            InvalidParameterException: 名字无效
        """
        # 验证名字
        new_name = new_name.strip()
        
        if not new_name:
            raise InvalidParameterException("名字", "名字不能为空")
        
        if len(new_name) > 12:
            raise InvalidParameterException("名字", "名字长度不能超过12个字符")
        
        # 更新名字
        player.nickname = new_name
        
        # 保存（JSONStorage 自动处理原子写入）
        self.player_repo.save(player)
    
    def delete_player(self, user_id: str) -> None:
        """
        删除玩家（弃道重修）
        
        Args:
            user_id: 用户ID
        """
        # JSONStorage 自动处理原子写入
        self.player_repo.delete(user_id)
    
    def get_level_name(self, player: Player) -> str:
        """
        获取境界名称
        
        Args:
            player: 玩家对象
            
        Returns:
            境界名称
        """
        # 根据修炼类型获取对应的境界数据
        level_data = self.config_manager.get_level_data(player.cultivation_type.value)
        
        if 0 <= player.level_index < len(level_data):
            level_info = level_data[player.level_index]
            # 尝试多个可能的键名
            return level_info.get("name") or level_info.get("level_name", "未知境界")
        return "未知境界"
    
    def get_required_exp(self, player: Player) -> int:
        """
        获取突破所需修为
        
        Args:
            player: 玩家对象
            
        Returns:
            所需修为
        """
        # 根据修炼类型获取对应的境界数据
        level_data = self.config_manager.get_level_data(player.cultivation_type.value)
        
        if player.level_index + 1 < len(level_data):
            next_level = level_data[player.level_index + 1]
            # 尝试多个可能的键名
            return next_level.get("required_exp") or next_level.get("exp_needed", 0)
        return 0
