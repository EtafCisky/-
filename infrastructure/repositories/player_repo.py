"""玩家仓储"""
import json
from typing import Optional, List, Dict, Any

from ...domain.models.player import Player
from ...domain.enums import CultivationType, PlayerState
from ..storage import JSONStorage, TimestampConverter
from .base import BaseRepository


class PlayerRepository(BaseRepository[Player]):
    """玩家仓储实现"""
    
    def __init__(self, storage: JSONStorage):
        """
        初始化玩家仓储
        
        Args:
            storage: JSON 存储管理器
        """
        super().__init__(storage, "players.json")
    
    def get_by_id(self, user_id: str) -> Optional[Player]:
        """
        根据用户ID获取玩家
        
        Args:
            user_id: 用户ID
            
        Returns:
            玩家对象，不存在则返回None
        """
        data = self.storage.get(self.filename, user_id)
        if data is None:
            return None
        return self._to_domain(data)
    
    def get_by_nickname(self, nickname: str) -> Optional[Player]:
        """
        根据道号获取玩家
        
        Args:
            nickname: 道号
            
        Returns:
            玩家对象，不存在则返回None
        """
        # 查询所有玩家，找到匹配的道号
        results = self.storage.query(
            self.filename,
            filter_fn=lambda x: x.get('nickname') == nickname,
            limit=1
        )
        
        if not results:
            return None
        
        return self._to_domain(results[0])
    
    def save(self, player: Player) -> None:
        """
        保存玩家（创建或更新）
        
        Args:
            player: 玩家对象
        """
        data = self._to_dict(player)
        self.storage.set(self.filename, player.user_id, data)
    
    def delete(self, user_id: str) -> None:
        """
        删除玩家
        
        Args:
            user_id: 用户ID
        """
        self.storage.delete(self.filename, user_id)
    
    def exists(self, user_id: str) -> bool:
        """
        检查玩家是否存在
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否存在
        """
        return self.storage.exists(self.filename, user_id)
    
    def get_top_by_level(self, limit: int = 10) -> List[Player]:
        """
        获取境界排行榜
        
        Args:
            limit: 返回数量
            
        Returns:
            玩家列表
        """
        results = self.storage.query(
            self.filename,
            sort_key=lambda x: (x['level_index'], x['experience']),
            reverse=True,
            limit=limit
        )
        return [self._to_domain(data) for data in results]
    
    def get_top_by_gold(self, limit: int = 10) -> List[Player]:
        """
        获取灵石排行榜
        
        Args:
            limit: 返回数量
            
        Returns:
            玩家列表
        """
        results = self.storage.query(
            self.filename,
            sort_key=lambda x: x['gold'],
            reverse=True,
            limit=limit
        )
        return [self._to_domain(data) for data in results]
    
    def get_player(self, user_id: str) -> Optional[Player]:
        """
        获取玩家（get_by_id 的别名，用于兼容性）
        
        Args:
            user_id: 用户ID
            
        Returns:
            玩家对象，不存在则返回None
        """
        return self.get_by_id(user_id)
    
    def add_gold(self, user_id: str, amount: int) -> None:
        """
        增加/减少玩家灵石（便捷方法）
        
        Args:
            user_id: 用户ID
            amount: 灵石数量（正数为增加，负数为减少）
        """
        player = self.get_by_id(user_id)
        if not player:
            raise ValueError(f"玩家不存在: {user_id}")
        
        if amount > 0:
            player.add_gold(amount)
        else:
            player.consume_gold(-amount)
        
        self.save(player)
    
    def add_experience(self, user_id: str, exp: int) -> None:
        """
        增加玩家修为（便捷方法）
        
        Args:
            user_id: 用户ID
            exp: 修为数量
        """
        player = self.get_by_id(user_id)
        if not player:
            raise ValueError(f"玩家不存在: {user_id}")
        
        player.add_experience(exp)
        self.save(player)
    
    def get_player_state(self, user_id: str):
        """
        获取玩家状态（便捷方法，用于兼容性）
        
        Args:
            user_id: 用户ID
            
        Returns:
            玩家状态对象
        """
        # TODO: 实现 PlayerStateTable 查询
        # 暂时返回 None
        return None
    
    def get_all_players(self) -> List[Player]:
        """
        获取所有玩家
        
        Returns:
            玩家列表
        """
        results = self.storage.query(self.filename)
        return [self._to_domain(data) for data in results]
    
    def _to_domain(self, data: Dict[str, Any]) -> Player:
        """
        将字典数据转换为领域对象
        
        Args:
            data: 字典数据
            
        Returns:
            Player 对象
        """
        # 转换时间戳
        created_at = TimestampConverter.from_iso8601(data.get('created_at'))
        updated_at = TimestampConverter.from_iso8601(data.get('updated_at'))
        cultivation_start_time = TimestampConverter.from_iso8601(data.get('cultivation_start_time'))
        
        # 如果时间戳为 None，使用默认值
        if created_at is None:
            created_at = 0
        if updated_at is None:
            updated_at = 0
        if cultivation_start_time is None:
            cultivation_start_time = 0
        
        # 解析丹药背包
        pills_inventory = data.get('pills_inventory', {})
        if isinstance(pills_inventory, str):
            try:
                pills_inventory = json.loads(pills_inventory)
            except:
                pills_inventory = {}
        
        return Player(
            user_id=data['user_id'],
            nickname=data['nickname'],
            cultivation_type=CultivationType(data['cultivation_type']),
            spiritual_root=data['spiritual_root'],
            level_index=data.get('level_index', 0),
            experience=data.get('experience', 0),
            gold=data.get('gold', 0),
            state=PlayerState.from_string(data.get('state', 'idle')),
            spiritual_qi=data.get('spiritual_qi', 0),
            max_spiritual_qi=data.get('max_spiritual_qi', 0),
            blood_qi=data.get('blood_qi', 0),
            max_blood_qi=data.get('max_blood_qi', 0),
            lifespan=data.get('lifespan', 100),
            mental_power=data.get('mental_power', 100),
            physical_damage=data.get('physical_damage', 5),
            magic_damage=data.get('magic_damage', 5),
            physical_defense=data.get('physical_defense', 5),
            magic_defense=data.get('magic_defense', 0),
            weapon=data.get('weapon'),
            armor=data.get('armor'),
            main_technique=data.get('main_technique'),
            pills_inventory=pills_inventory,
            sect_id=data.get('sect_id'),
            sect_position=data.get('sect_position'),
            level_up_rate=data.get('level_up_rate', 0),
            created_at=created_at,
            updated_at=updated_at,
            last_check_in_date=data.get('last_check_in_date'),
            cultivation_start_time=cultivation_start_time,
            user_name=data.get('user_name')
        )
    
    def _to_dict(self, player: Player) -> Dict[str, Any]:
        """
        将领域对象转换为字典数据
        
        Args:
            player: Player 对象
            
        Returns:
            字典数据
        """
        return {
            'user_id': player.user_id,
            'nickname': player.nickname,
            'cultivation_type': player.cultivation_type.value,
            'spiritual_root': player.spiritual_root,
            'level_index': player.level_index,
            'experience': player.experience,
            'gold': player.gold,
            'state': player.state.value,
            'spiritual_qi': player.spiritual_qi,
            'max_spiritual_qi': player.max_spiritual_qi,
            'blood_qi': player.blood_qi,
            'max_blood_qi': player.max_blood_qi,
            'lifespan': player.lifespan,
            'mental_power': player.mental_power,
            'physical_damage': player.physical_damage,
            'magic_damage': player.magic_damage,
            'physical_defense': player.physical_defense,
            'magic_defense': player.magic_defense,
            'weapon': player.weapon,
            'armor': player.armor,
            'main_technique': player.main_technique,
            'pills_inventory': player.pills_inventory,
            'sect_id': player.sect_id,
            'sect_position': player.sect_position,
            'level_up_rate': player.level_up_rate,
            'created_at': TimestampConverter.to_iso8601(player.created_at),
            'updated_at': TimestampConverter.to_iso8601(player.updated_at),
            'last_check_in_date': player.last_check_in_date,
            'cultivation_start_time': TimestampConverter.to_iso8601(player.cultivation_start_time),
            'user_name': player.user_name
        }
