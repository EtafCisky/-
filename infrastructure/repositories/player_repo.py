"""玩家仓储"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from ...domain.models.player import Player
from ...domain.enums import CultivationType, PlayerState
from ..database.schema import PlayerTable
from .base import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    """玩家仓储实现"""
    
    def __init__(self, session: Session):
        super().__init__(session)
    
    def get_by_id(self, user_id: str) -> Optional[Player]:
        """
        根据用户ID获取玩家
        
        Args:
            user_id: 用户ID
            
        Returns:
            玩家对象，不存在则返回None
        """
        stmt = select(PlayerTable).where(PlayerTable.user_id == user_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        
        if result is None:
            return None
        
        return self._to_domain(result)
    
    def get_by_nickname(self, nickname: str) -> Optional[Player]:
        """
        根据道号获取玩家
        
        Args:
            nickname: 道号
            
        Returns:
            玩家对象，不存在则返回None
        """
        stmt = select(PlayerTable).where(PlayerTable.nickname == nickname)
        result = self.session.execute(stmt).scalar_one_or_none()
        
        if result is None:
            return None
        
        return self._to_domain(result)
    
    def save(self, player: Player) -> None:
        """
        保存玩家（创建或更新）
        
        Args:
            player: 玩家对象
        """
        # 检查是否已存在
        existing = self.session.get(PlayerTable, player.user_id)
        
        if existing:
            # 更新
            self._update_from_domain(existing, player)
        else:
            # 创建
            table_obj = self._to_table(player)
            self.session.add(table_obj)
        
        self.session.flush()
    
    def delete(self, user_id: str) -> None:
        """
        删除玩家
        
        Args:
            user_id: 用户ID
        """
        player = self.session.get(PlayerTable, user_id)
        if player:
            self.session.delete(player)
            self.session.flush()
    
    def exists(self, user_id: str) -> bool:
        """
        检查玩家是否存在
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否存在
        """
        stmt = select(PlayerTable.user_id).where(PlayerTable.user_id == user_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result is not None
    
    def get_top_by_level(self, limit: int = 10) -> List[Player]:
        """
        获取境界排行榜
        
        Args:
            limit: 返回数量
            
        Returns:
            玩家列表
        """
        stmt = (
            select(PlayerTable)
            .order_by(PlayerTable.level_index.desc(), PlayerTable.experience.desc())
            .limit(limit)
        )
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]
    
    def get_top_by_gold(self, limit: int = 10) -> List[Player]:
        """
        获取灵石排行榜
        
        Args:
            limit: 返回数量
            
        Returns:
            玩家列表
        """
        stmt = (
            select(PlayerTable)
            .order_by(PlayerTable.gold.desc())
            .limit(limit)
        )
        results = self.session.execute(stmt).scalars().all()
        return [self._to_domain(r) for r in results]
    
    def _to_domain(self, table_obj: PlayerTable) -> Player:
        """将数据库对象转换为领域对象"""
        import json
        
        # 解析丹药背包
        pills_inventory = {}
        if table_obj.pills_inventory:
            try:
                pills_inventory = json.loads(table_obj.pills_inventory)
            except:
                pills_inventory = {}
        
        return Player(
            user_id=table_obj.user_id,
            nickname=table_obj.nickname,
            cultivation_type=CultivationType(table_obj.cultivation_type),
            spiritual_root=table_obj.spiritual_root,
            level_index=table_obj.level_index,
            experience=table_obj.experience,
            gold=table_obj.gold,
            state=PlayerState.from_string(table_obj.state),
            spiritual_qi=table_obj.mp,
            max_spiritual_qi=table_obj.max_mp,
            blood_qi=table_obj.hp,
            max_blood_qi=table_obj.max_hp,
            lifespan=table_obj.created_at,  # 临时映射
            mental_power=table_obj.mental_power,
            physical_damage=table_obj.physical_damage,
            magic_damage=table_obj.magic_damage,
            physical_defense=table_obj.physical_defense,
            magic_defense=table_obj.magic_defense,
            weapon=table_obj.equipped_weapon,
            armor=table_obj.equipped_armor,
            main_technique=table_obj.equipped_main_technique,
            pills_inventory=pills_inventory,
            sect_id=int(table_obj.sect_id) if table_obj.sect_id else None,
            sect_position=int(table_obj.sect_position) if table_obj.sect_position else None,
            level_up_rate=0,  # 需要从其他地方获取
            created_at=table_obj.created_at,
            updated_at=table_obj.updated_at,
            last_check_in_date=None,  # 需要从时间戳转换
            cultivation_start_time=table_obj.cultivation_start_time,
            user_name=table_obj.nickname
        )
    
    def _to_table(self, player: Player) -> PlayerTable:
        """将领域对象转换为数据库对象"""
        import json
        
        return PlayerTable(
            user_id=player.user_id,
            nickname=player.nickname,
            cultivation_type=player.cultivation_type.value,
            spiritual_root=player.spiritual_root,
            level_index=player.level_index,
            experience=player.experience,
            gold=player.gold,
            state=player.state.value,
            cultivation_start_time=player.cultivation_start_time,
            hp=player.blood_qi,
            max_hp=player.max_blood_qi,
            mp=player.spiritual_qi,
            max_mp=player.max_spiritual_qi,
            physical_damage=player.physical_damage,
            magic_damage=player.magic_damage,
            physical_defense=player.physical_defense,
            magic_defense=player.magic_defense,
            mental_power=player.mental_power,
            equipped_weapon=player.weapon,
            equipped_armor=player.armor,
            equipped_main_technique=player.main_technique,
            pills_inventory=json.dumps(player.pills_inventory, ensure_ascii=False) if player.pills_inventory else None,
            sect_id=str(player.sect_id) if player.sect_id else None,
            sect_position=str(player.sect_position) if player.sect_position else None,
            created_at=player.created_at,
            updated_at=player.updated_at
        )
    
    def _update_from_domain(self, table_obj: PlayerTable, player: Player) -> None:
        """用领域对象更新数据库对象"""
        import json
        
        table_obj.nickname = player.nickname
        table_obj.cultivation_type = player.cultivation_type.value
        table_obj.spiritual_root = player.spiritual_root
        table_obj.level_index = player.level_index
        table_obj.experience = player.experience
        table_obj.gold = player.gold
        table_obj.state = player.state.value
        table_obj.cultivation_start_time = player.cultivation_start_time
        table_obj.hp = player.blood_qi
        table_obj.max_hp = player.max_blood_qi
        table_obj.mp = player.spiritual_qi
        table_obj.max_mp = player.max_spiritual_qi
        table_obj.physical_damage = player.physical_damage
        table_obj.magic_damage = player.magic_damage
        table_obj.physical_defense = player.physical_defense
        table_obj.magic_defense = player.magic_defense
        table_obj.mental_power = player.mental_power
        table_obj.equipped_weapon = player.weapon
        table_obj.equipped_armor = player.armor
        table_obj.equipped_main_technique = player.main_technique
        table_obj.pills_inventory = json.dumps(player.pills_inventory, ensure_ascii=False) if player.pills_inventory else None
        table_obj.sect_id = str(player.sect_id) if player.sect_id else None
        table_obj.sect_position = str(player.sect_position) if player.sect_position else None
        table_obj.updated_at = player.updated_at
