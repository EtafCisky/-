"""Boss仓储"""
from typing import Optional
from sqlalchemy.orm import Session

from ..database.schema import BossTable
from ...domain.models.boss import Boss


class BossRepository:
    """Boss仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_active_boss(self) -> Optional[Boss]:
        """获取当前存活的Boss"""
        row = self.session.query(BossTable).filter(
            BossTable.status == 1
        ).first()
        
        if not row:
            return None
        
        return self._to_domain(row)
    
    def get_boss_by_id(self, boss_id: int) -> Optional[Boss]:
        """根据ID获取Boss"""
        row = self.session.query(BossTable).filter(
            BossTable.boss_id == boss_id
        ).first()
        
        if not row:
            return None
        
        return self._to_domain(row)
    
    def create_boss(self, boss: Boss) -> int:
        """创建Boss"""
        row = BossTable(
            boss_name=boss.boss_name,
            boss_level=boss.boss_level,
            hp=boss.hp,
            max_hp=boss.max_hp,
            atk=boss.atk,
            defense=boss.defense,
            stone_reward=boss.stone_reward,
            create_time=boss.create_time,
            status=boss.status
        )
        
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        
        return row.boss_id
    
    def update_boss(self, boss: Boss) -> None:
        """更新Boss"""
        self.session.query(BossTable).filter(
            BossTable.boss_id == boss.boss_id
        ).update({
            "hp": boss.hp,
            "status": boss.status
        })
        self.session.commit()
    
    def defeat_boss(self, boss_id: int) -> None:
        """标记Boss为已击败"""
        self.session.query(BossTable).filter(
            BossTable.boss_id == boss_id
        ).update({
            "status": 0
        })
        self.session.commit()
    
    def _to_domain(self, row: BossTable) -> Boss:
        """转换为领域模型"""
        return Boss(
            boss_id=row.boss_id,
            boss_name=row.boss_name,
            boss_level=row.boss_level,
            hp=row.hp,
            max_hp=row.max_hp,
            atk=row.atk,
            defense=row.defense,
            stone_reward=row.stone_reward,
            create_time=row.create_time,
            status=row.status
        )
