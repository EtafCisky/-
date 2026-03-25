"""
宗门仓储层

处理宗门数据的持久化。
"""
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...domain.models.sect import Sect, SectMember, SectPosition
from ..database.schema import SectTable, PlayerTable


class SectRepository:
    """宗门仓储"""
    
    def __init__(self, session: Session):
        """
        初始化宗门仓储
        
        Args:
            session: 数据库会话
        """
        self.session = session
    
    def get_by_id(self, sect_id: int) -> Optional[Sect]:
        """
        根据ID获取宗门
        
        Args:
            sect_id: 宗门ID
            
        Returns:
            宗门对象，如果不存在则返回None
        """
        sect_record = self.session.query(SectTable).filter_by(sect_id=sect_id).first()
        
        if not sect_record:
            return None
        
        return Sect(
            sect_id=sect_record.sect_id,
            name=sect_record.name,
            leader_id=sect_record.leader_id,
            scale=sect_record.level,  # 使用level字段存储建设度
            funds=sect_record.funds,
            materials=sect_record.experience,  # 使用experience字段存储资材
            elixir_room_level=0,  # 暂时固定为0
            created_at=sect_record.created_at
        )
    
    def get_sect(self, sect_id: int) -> Optional[Sect]:
        """
        根据ID获取宗门（别名方法）
        
        Args:
            sect_id: 宗门ID
            
        Returns:
            宗门对象，如果不存在则返回None
        """
        return self.get_by_id(sect_id)
    
    def get_by_name(self, name: str) -> Optional[Sect]:
        """
        根据名称获取宗门
        
        Args:
            name: 宗门名称
            
        Returns:
            宗门对象，如果不存在则返回None
        """
        sect_record = self.session.query(SectTable).filter_by(name=name).first()
        
        if not sect_record:
            return None
        
        return Sect(
            sect_id=sect_record.sect_id,
            name=sect_record.name,
            leader_id=sect_record.leader_id,
            scale=sect_record.level,
            funds=sect_record.funds,
            materials=sect_record.experience,
            elixir_room_level=0,
            created_at=sect_record.created_at
        )
    
    def create(self, sect: Sect) -> int:
        """
        创建宗门
        
        Args:
            sect: 宗门对象
            
        Returns:
            宗门ID
        """
        # 生成新的宗门ID
        max_id = self.session.query(func.max(SectTable.sect_id)).scalar() or 0
        new_id = max_id + 1
        
        sect_record = SectTable(
            sect_id=new_id,
            name=sect.name,
            leader_id=sect.leader_id,
            level=sect.scale,
            experience=sect.materials,
            funds=sect.funds,
            max_members=50,
            created_at=sect.created_at
        )
        
        self.session.add(sect_record)
        self.session.commit()
        
        return new_id
    
    def update(self, sect: Sect) -> None:
        """
        更新宗门
        
        Args:
            sect: 宗门对象
        """
        sect_record = self.session.query(SectTable).filter_by(sect_id=sect.sect_id).first()
        
        if sect_record:
            sect_record.name = sect.name
            sect_record.leader_id = sect.leader_id
            sect_record.level = sect.scale
            sect_record.experience = sect.materials
            sect_record.funds = sect.funds
            
            self.session.commit()
    
    def delete(self, sect_id: int) -> None:
        """
        删除宗门
        
        Args:
            sect_id: 宗门ID
        """
        self.session.query(SectTable).filter_by(sect_id=sect_id).delete()
        self.session.commit()
    
    def get_all(self, limit: int = 100) -> List[Sect]:
        """
        获取所有宗门
        
        Args:
            limit: 限制数量
            
        Returns:
            宗门列表
        """
        sect_records = self.session.query(SectTable).order_by(
            SectTable.level.desc()
        ).limit(limit).all()
        
        sects = []
        for record in sect_records:
            sects.append(Sect(
                sect_id=record.sect_id,
                name=record.name,
                leader_id=record.leader_id,
                scale=record.level,
                funds=record.funds,
                materials=record.experience,
                elixir_room_level=0,
                created_at=record.created_at
            ))
        
        return sects
    
    def get_all_sects(self, limit: int = 100) -> List[Sect]:
        """
        获取所有宗门（别名方法）
        
        Args:
            limit: 限制数量
            
        Returns:
            宗门列表
        """
        return self.get_all(limit)
    
    def get_members(self, sect_id: int) -> List[SectMember]:
        """
        获取宗门成员列表
        
        Args:
            sect_id: 宗门ID
            
        Returns:
            成员列表
        """
        # 将sect_id转换为字符串进行比较
        members = self.session.query(PlayerTable).filter(
            PlayerTable.sect_id == str(sect_id)
        ).all()
        
        result = []
        for member in members:
            # 将字符串职位转换为整数
            try:
                position_value = int(member.sect_position) if member.sect_position else 4
            except (ValueError, TypeError):
                position_value = 4
            
            result.append(SectMember(
                user_id=member.user_id,
                user_name=member.nickname or member.user_id,
                position=SectPosition(position_value),
                contribution=0,  # 暂时固定为0，后续可以从player表读取
                level_index=member.level_index
            ))
        
        return result
    
    def get_sect_members(self, sect_id: int) -> List[SectMember]:
        """
        获取宗门成员列表（别名方法）
        
        Args:
            sect_id: 宗门ID
            
        Returns:
            成员列表
        """
        return self.get_members(sect_id)
    
    def get_member_count(self, sect_id: int) -> int:
        """
        获取宗门成员数量
        
        Args:
            sect_id: 宗门ID
            
        Returns:
            成员数量
        """
        return self.session.query(PlayerTable).filter(
            PlayerTable.sect_id == str(sect_id)
        ).count()
    
    def update_player_sect(
        self, 
        user_id: str, 
        sect_id: int, 
        position: SectPosition
    ) -> None:
        """
        更新玩家宗门信息
        
        Args:
            user_id: 用户ID
            sect_id: 宗门ID（0表示无宗门）
            position: 职位
        """
        player = self.session.query(PlayerTable).filter_by(user_id=user_id).first()
        
        if player:
            player.sect_id = str(sect_id) if sect_id > 0 else None
            player.sect_position = str(position.value) if sect_id > 0 else None
            self.session.commit()
