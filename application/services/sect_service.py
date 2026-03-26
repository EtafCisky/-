"""
宗门服务层

处理宗门相关的业务逻辑。
"""
import time
from typing import Tuple, Optional, Dict, List

from ...domain.models.sect import Sect, SectMember, SectPosition
from ...domain.models.player import Player
from ...infrastructure.repositories.sect_repo import SectRepository
from ...infrastructure.repositories.player_repo import PlayerRepository
from ...core.config import ConfigManager
from ...core.exceptions import BusinessException


class SectService:
    """宗门服务"""
    
    # 宗门名称限制
    SECT_NAME_MIN_LENGTH = 2
    SECT_NAME_MAX_LENGTH = 12
    SECT_NAME_FORBIDDEN = ["管理员", "系统", "官方", "GM", "admin"]
    
    def __init__(
        self,
        sect_repo: SectRepository,
        player_repo: PlayerRepository,
        config_manager: ConfigManager,
    ):
        """
        初始化宗门服务
        
        Args:
            sect_repo: 宗门仓储
            player_repo: 玩家仓储
            config_manager: 配置管理器
        """
        self.sect_repo = sect_repo
        self.player_repo = player_repo
        self.config_manager = config_manager
    
    def _validate_sect_name(self, name: str) -> Tuple[bool, str]:
        """
        验证宗门名称
        
        Args:
            name: 宗门名称
            
        Returns:
            (是否有效, 错误消息)
        """
        if len(name) < self.SECT_NAME_MIN_LENGTH or len(name) > self.SECT_NAME_MAX_LENGTH:
            return False, f"宗门名称长度需在{self.SECT_NAME_MIN_LENGTH}-{self.SECT_NAME_MAX_LENGTH}字之间"
        
        for forbidden in self.SECT_NAME_FORBIDDEN:
            if forbidden.lower() in name.lower():
                return False, "宗门名称包含禁用词汇"
        
        return True, ""
    
    def create_sect(
        self, 
        user_id: str, 
        sect_name: str,
        required_stone: int = 10000,
        required_level: int = 3
    ) -> Tuple[bool, str]:
        """
        创建宗门
        
        Args:
            user_id: 用户ID
            sect_name: 宗门名称
            required_stone: 需求灵石
            required_level: 需求境界等级
            
        Returns:
            (是否成功, 消息)
            
        Raises:
            BusinessException: 各种业务异常
        """
        # 获取玩家
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        # 检查是否已有宗门
        if player.sect_id and player.sect_id != "0":
            raise BusinessException("你已经加入了宗门，无法创建新宗门")
        
        # 检查境界
        if player.level_index < required_level:
            raise BusinessException(f"创建宗门需要达到境界等级 {required_level}")
        
        # 检查灵石
        if player.gold < required_stone:
            raise BusinessException(f"创建宗门需要 {required_stone} 灵石")
        
        # 验证宗门名称
        valid, error = self._validate_sect_name(sect_name)
        if not valid:
            raise BusinessException(error)
        
        # 检查宗门名称是否重复
        existing_sect = self.sect_repo.get_by_name(sect_name)
        if existing_sect:
            raise BusinessException(f"宗门名称『{sect_name}』已被使用")
        
        # 扣除灵石
        player.gold -= required_stone
        self.player_repo.update(player)
        
        # 创建宗门
        new_sect = Sect(
            sect_id=0,  # 将由仓储层生成
            name=sect_name,
            leader_id=user_id,
            scale=100,  # 初始建设度
            funds=0,
            materials=100,  # 初始资材
            elixir_room_level=0,
            created_at=int(time.time())
        )
        
        sect_id = self.sect_repo.create(new_sect)
        
        # 更新玩家宗门信息（设为宗主）
        self.sect_repo.update_player_sect(user_id, sect_id, SectPosition.LEADER)
        
        return True, f"✨ 恭喜！你成功创建了宗门『{sect_name}』，成为一代宗主！"
    
    def join_sect(self, user_id: str, sect_name: str) -> Tuple[bool, str]:
        """
        加入宗门
        
        Args:
            user_id: 用户ID
            sect_name: 宗门名称
            
        Returns:
            (是否成功, 消息)
            
        Raises:
            BusinessException: 各种业务异常
        """
        # 获取玩家
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        # 检查是否已有宗门
        if player.sect_id and player.sect_id != "0":
            raise BusinessException("你已经加入了宗门！请先退出当前宗门")
        
        # 查找宗门
        sect = self.sect_repo.get_by_name(sect_name)
        if not sect:
            raise BusinessException(f"未找到宗门『{sect_name}』")
        
        # 检查宗门是否已满
        member_count = self.sect_repo.get_member_count(sect.sect_id)
        if not sect.can_accept_members(member_count):
            raise BusinessException("宗门成员已满")
        
        # 加入宗门（默认为外门弟子）
        self.sect_repo.update_player_sect(user_id, sect.sect_id, SectPosition.OUTER_DISCIPLE)
        
        return True, f"✨ 你成功加入了宗门『{sect_name}』，成为外门弟子！"
    
    def leave_sect(self, user_id: str) -> Tuple[bool, str]:
        """
        退出宗门
        
        Args:
            user_id: 用户ID
            
        Returns:
            (是否成功, 消息)
            
        Raises:
            BusinessException: 各种业务异常
        """
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        if not player.sect_id or player.sect_id == "0":
            raise BusinessException("你还未加入任何宗门")
        
        # 获取宗门信息
        sect = self.sect_repo.get_by_id(int(player.sect_id))
        if not sect:
            raise BusinessException("宗门信息异常")
        
        # 检查是否为宗主
        if sect.leader_id == user_id:
            raise BusinessException("宗主无法直接退出宗门！请先传位或解散宗门")
        
        sect_name = sect.name
        
        # 清除宗门信息
        self.sect_repo.update_player_sect(user_id, 0, SectPosition.OUTER_DISCIPLE)
        
        return True, f"✨ 你已退出宗门『{sect_name}』！"
    
    def donate_to_sect(self, user_id: str, stone_amount: int) -> Tuple[bool, str]:
        """
        宗门捐献（1灵石 = 10建设度 + 1贡献）
        
        Args:
            user_id: 用户ID
            stone_amount: 捐献灵石数量
            
        Returns:
            (是否成功, 消息)
            
        Raises:
            BusinessException: 各种业务异常
        """
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        if not player.sect_id or player.sect_id == "0":
            raise BusinessException("你还未加入宗门")
        
        if stone_amount <= 0:
            raise BusinessException("捐献数量必须大于0")
        
        if player.gold < stone_amount:
            raise BusinessException(f"你的灵石不足！当前拥有 {player.gold} 灵石")
        
        # 获取宗门
        sect = self.sect_repo.get_by_id(int(player.sect_id))
        if not sect:
            raise BusinessException("宗门信息异常")
        
        # 扣除灵石
        player.gold -= stone_amount
        self.player_repo.update(player)
        
        # 增加宗门建设度和灵石
        scale_gained = sect.add_donation(stone_amount)
        self.sect_repo.update(sect)
        
        # 注意：贡献度暂时不记录，因为Player模型中没有sect_contribution字段
        # 如果需要，可以后续添加
        
        return True, f"✨ 捐献成功！消耗 {stone_amount} 灵石，宗门获得 {scale_gained} 建设度！"
    
    def get_sect_info(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        获取宗门信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            (是否成功, 消息, 宗门数据)
            
        Raises:
            BusinessException: 各种业务异常
        """
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        if not player.sect_id or player.sect_id == "0":
            raise BusinessException("你还未加入宗门")
        
        sect = self.sect_repo.get_by_id(int(player.sect_id))
        if not sect:
            raise BusinessException("宗门信息异常")
        
        # 获取宗主信息
        owner = self.player_repo.get_by_id(sect.leader_id)
        owner_name = owner.nickname if owner and owner.nickname else sect.leader_id
        
        # 获取成员数量
        member_count = self.sect_repo.get_member_count(sect.sect_id)
        
        # 获取玩家职位
        try:
            position_value = int(player.sect_position) if player.sect_position else 4
            position = SectPosition(position_value)
        except (ValueError, TypeError):
            position = SectPosition.OUTER_DISCIPLE
        
        position_name = position.display_name
        
        info_msg = f"""🏛️ 宗门信息
━━━━━━━━━━━━━━━

宗门名称：{sect.name}
宗主：{owner_name}
建设度：{sect.scale}
宗门灵石：{sect.funds}
宗门资材：{sect.materials}
丹房等级：{sect.elixir_room_level}
成员数量：{member_count}人

你的职位：{position_name}"""
        
        sect_data = {
            "sect": sect,
            "player_position": position,
            "member_count": member_count
        }
        
        return True, info_msg, sect_data
    
    def list_all_sects(self, limit: int = 10) -> Tuple[bool, str]:
        """
        获取所有宗门列表
        
        Args:
            limit: 限制数量
            
        Returns:
            (是否成功, 消息)
        """
        sects = self.sect_repo.get_all(limit=limit)
        
        if not sects:
            return False, "❌ 当前还没有任何宗门！"
        
        lines = ["🏛️ 宗门列表", "━━━━━━━━━━━━━━━", ""]
        
        for idx, sect in enumerate(sects, 1):
            owner = self.player_repo.get_by_id(sect.leader_id)
            owner_name = owner.nickname if owner and owner.nickname else "未知"
            member_count = self.sect_repo.get_member_count(sect.sect_id)
            
            lines.append(f"{idx}. 【{sect.name}】")
            lines.append(f"   宗主：{owner_name}")
            lines.append(f"   建设度：{sect.scale} | 成员：{member_count}人")
            lines.append("")
        
        return True, "\n".join(lines)
    
    def change_position(
        self, 
        operator_id: str, 
        target_id: str, 
        new_position: int
    ) -> Tuple[bool, str]:
        """
        变更宗门职位
        
        Args:
            operator_id: 操作者ID（必须是宗主）
            target_id: 目标用户ID
            new_position: 新职位（0-4）
            
        Returns:
            (是否成功, 消息)
            
        Raises:
            BusinessException: 各种业务异常
        """
        # 检查操作者
        operator = self.player_repo.get_by_id(operator_id)
        if not operator or not operator.sect_id or operator.sect_id == "0":
            raise BusinessException("你还未加入宗门")
        
        try:
            op_position_value = int(operator.sect_position) if operator.sect_position else 4
            op_position = SectPosition(op_position_value)
        except (ValueError, TypeError):
            op_position = SectPosition.OUTER_DISCIPLE
        
        if op_position != SectPosition.LEADER:
            raise BusinessException("只有宗主才能变更职位")
        
        # 检查目标用户
        target = self.player_repo.get_by_id(target_id)
        if not target:
            raise BusinessException("目标用户不存在")
        
        if target.sect_id != operator.sect_id:
            raise BusinessException("目标用户不在你的宗门")
        
        if target_id == operator_id:
            raise BusinessException("无法变更自己的职位")
        
        # 验证新职位
        try:
            new_pos = SectPosition(new_position)
        except ValueError:
            raise BusinessException("无效的职位！职位范围：0（宗主）- 4（外门弟子）")
        
        if new_pos == SectPosition.LEADER:
            raise BusinessException("无法直接任命宗主！请使用传位功能")
        
        # 变更职位
        self.sect_repo.update_player_sect(target_id, int(operator.sect_id), new_pos)
        
        target_name = target.nickname if target.nickname else target_id
        position_name = new_pos.display_name
        
        return True, f"✨ 已将 {target_name} 的职位变更为：{position_name}"
    
    def transfer_ownership(
        self, 
        current_owner_id: str, 
        new_owner_id: str
    ) -> Tuple[bool, str]:
        """
        宗主传位
        
        Args:
            current_owner_id: 当前宗主ID
            new_owner_id: 新宗主ID
            
        Returns:
            (是否成功, 消息)
            
        Raises:
            BusinessException: 各种业务异常
        """
        # 检查当前宗主
        current_owner = self.player_repo.get_by_id(current_owner_id)
        if not current_owner or not current_owner.sect_id or current_owner.sect_id == "0":
            raise BusinessException("你还未加入宗门")
        
        sect = self.sect_repo.get_by_id(int(current_owner.sect_id))
        if not sect or sect.leader_id != current_owner_id:
            raise BusinessException("你不是宗主")
        
        # 检查新宗主
        new_owner = self.player_repo.get_by_id(new_owner_id)
        if not new_owner:
            raise BusinessException("目标用户不存在")
        
        if new_owner.sect_id != current_owner.sect_id:
            raise BusinessException("目标用户不在你的宗门")
        
        if new_owner_id == current_owner_id:
            raise BusinessException("无法传位给自己")
        
        # 执行传位
        sect.leader_id = new_owner_id
        self.sect_repo.update(sect)
        
        # 更新职位：新宗主->宗主，旧宗主->长老
        self.sect_repo.update_player_sect(new_owner_id, sect.sect_id, SectPosition.LEADER)
        self.sect_repo.update_player_sect(current_owner_id, sect.sect_id, SectPosition.ELDER)
        
        new_owner_name = new_owner.nickname if new_owner.nickname else new_owner_id
        
        return True, f"✨ 宗主之位已传给 {new_owner_name}！你现在是长老。"
    
    def kick_member(self, operator_id: str, target_id: str) -> Tuple[bool, str]:
        """
        踢出宗门成员
        
        Args:
            operator_id: 操作者ID
            target_id: 目标用户ID
            
        Returns:
            (是否成功, 消息)
            
        Raises:
            BusinessException: 各种业务异常
        """
        # 检查操作者权限
        operator = self.player_repo.get_by_id(operator_id)
        if not operator or not operator.sect_id or operator.sect_id == "0":
            raise BusinessException("你还未加入宗门")
        
        try:
            op_position_value = int(operator.sect_position) if operator.sect_position else 4
            op_position = SectPosition(op_position_value)
        except (ValueError, TypeError):
            op_position = SectPosition.OUTER_DISCIPLE
        
        # 宗主和长老可以踢人
        if op_position not in [SectPosition.LEADER, SectPosition.ELDER]:
            raise BusinessException("只有宗主和长老才能踢出成员")
        
        # 检查目标
        target = self.player_repo.get_by_id(target_id)
        if not target:
            raise BusinessException("目标用户不存在")
        
        if target.sect_id != operator.sect_id:
            raise BusinessException("目标用户不在你的宗门")
        
        if target_id == operator_id:
            raise BusinessException("无法踢出自己")
        
        try:
            target_position_value = int(target.sect_position) if target.sect_position else 4
            target_position = SectPosition(target_position_value)
        except (ValueError, TypeError):
            target_position = SectPosition.OUTER_DISCIPLE
        
        # 长老只能踢外门弟子
        if op_position == SectPosition.ELDER and target_position != SectPosition.OUTER_DISCIPLE:
            raise BusinessException("长老只能踢出外门弟子")
        
        # 无法踢出宗主
        if target_position == SectPosition.LEADER:
            raise BusinessException("无法踢出宗主")
        
        # 踢出
        target_name = target.nickname if target.nickname else target_id
        self.sect_repo.update_player_sect(target_id, 0, SectPosition.OUTER_DISCIPLE)
        
        return True, f"✨ 已将 {target_name} 踢出宗门！"

    def perform_sect_task(self, user_id: str) -> Tuple[bool, str]:
        """
        执行宗门任务
        
        Args:
            user_id: 用户ID
            
        Returns:
            (是否成功, 消息)
            
        Raises:
            BusinessException: 各种业务异常
        """
        import time
        import random
        
        player = self.player_repo.get_by_id(user_id)
        if not player:
            raise BusinessException("玩家不存在")
        
        if not player.sect_id or player.sect_id == "0":
            raise BusinessException("你还未加入宗门")
        
        # 检查1小时冷却（使用系统配置存储）
        current_time = int(time.time())
        cooldown_key = f"sect_task_cooldown_{user_id}"
        
        try:
            from ...infrastructure.repositories.system_config_repo import SystemConfigRepository
            from ...infrastructure.storage.json_storage import JSONStorage
            from pathlib import Path
            
            # 创建临时的 JSONStorage（使用默认数据目录）
            storage = JSONStorage(data_dir=Path("data"), enable_cache=True)
            config_repo = SystemConfigRepository(storage)
            
            last_task_str = config_repo.get_config(cooldown_key)
            if last_task_str:
                last_task_time = int(last_task_str)
                cooldown_seconds = 3600  # 1小时
                
                if current_time - last_task_time < cooldown_seconds:
                    remaining = cooldown_seconds - (current_time - last_task_time)
                    remaining_minutes = remaining // 60
                    
                    raise BusinessException(f"宗门任务冷却中！还需 {remaining_minutes} 分钟")
        except BusinessException:
            raise
        except Exception:
            # 如果获取配置失败，允许继续
            pass
        
        # 执行任务
        contribution_gain = random.randint(10, 30)
        materials_gain = contribution_gain * 10
        
        # 注意：Player模型中没有sect_contribution字段
        # 这里我们只更新宗门资源，不更新玩家贡献度
        # 如果需要贡献度功能，需要在Player模型中添加该字段
        
        # 更新宗门资源
        sect = self.sect_repo.get_by_id(int(player.sect_id))
        if sect:
            sect.materials += materials_gain
            self.sect_repo.update(sect)
        
        # 设置1小时冷却
        try:
            config_repo.set_config(cooldown_key, str(current_time))
        except Exception:
            pass
        
        return True, f"✨ 完成宗门任务！\n获得贡献：{contribution_gain}\n宗门资材：+{materials_gain}"
