"""秘境仓储"""
from typing import List, Optional
from sqlalchemy.orm import Session

from ..database.schema import RiftTable
from ...domain.models.rift import Rift


class RiftRepository:
    """秘境仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_all_rifts(self) -> List[Rift]:
        """获取所有秘境"""
        rows = self.session.query(RiftTable).all()
        return [self._to_domain(row) for row in rows]
    
    def get_rift_by_id(self, rift_id: int) -> Optional[Rift]:
        """根据ID获取秘境"""
        row = self.session.query(RiftTable).filter(
            RiftTable.rift_id == rift_id
        ).first()
        
        if not row:
            return None
        
        return self._to_domain(row)
    
    def get_rifts_by_level(self, rift_level: int) -> List[Rift]:
        """根据等级获取秘境"""
        rows = self.session.query(RiftTable).filter(
            RiftTable.rift_level == rift_level
        ).all()
        
        return [self._to_domain(row) for row in rows]
    
    def create_rift(self, rift: Rift) -> int:
        """创建秘境"""
        row = RiftTable(
            rift_name=rift.rift_name,
            rift_level=rift.rift_level,
            required_level=rift.required_level,
            exp_reward_min=rift.exp_reward_min,
            exp_reward_max=rift.exp_reward_max,
            gold_reward_min=rift.gold_reward_min,
            gold_reward_max=rift.gold_reward_max,
            description=rift.description
        )
        
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        
        return row.rift_id
    
    def _to_domain(self, row: RiftTable) -> Rift:
        """转换为领域模型"""
        return Rift(
            rift_id=row.rift_id,
            rift_name=row.rift_name,
            rift_level=row.rift_level,
            required_level=row.required_level,
            exp_reward_min=row.exp_reward_min,
            exp_reward_max=row.exp_reward_max,
            gold_reward_min=row.gold_reward_min,
            gold_reward_max=row.gold_reward_max,
            description=row.description or ""
        )
