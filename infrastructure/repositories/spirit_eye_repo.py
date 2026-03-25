"""天地灵眼仓储"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database.schema import SpiritEyeTable
from ...domain.models.spirit_eye import SpiritEye


class SpiritEyeRepository:
    """天地灵眼仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_spirit_eye(self, eye_id: int) -> Optional[SpiritEye]:
        """获取灵眼"""
        row = self.session.query(SpiritEyeTable).filter(
            SpiritEyeTable.eye_id == eye_id
        ).first()
        
        if not row:
            return None
        
        return self._to_domain(row)
    
    def get_user_spirit_eye(self, user_id: str) -> Optional[SpiritEye]:
        """获取用户占领的灵眼"""
        row = self.session.query(SpiritEyeTable).filter(
            SpiritEyeTable.owner_id == user_id
        ).first()
        
        if not row:
            return None
        
        return self._to_domain(row)
    
    def get_available_spirit_eyes(self) -> List[SpiritEye]:
        """获取所有可占领的灵眼"""
        rows = self.session.query(SpiritEyeTable).filter(
            SpiritEyeTable.owner_id.is_(None)
        ).all()
        
        return [self._to_domain(row) for row in rows]
    
    def get_all_spirit_eyes(self) -> List[SpiritEye]:
        """获取所有灵眼"""
        rows = self.session.query(SpiritEyeTable).all()
        return [self._to_domain(row) for row in rows]
    
    def create_spirit_eye(
        self,
        eye_type: int,
        eye_name: str,
        exp_per_hour: int,
        spawn_time: int
    ) -> int:
        """创建灵眼"""
        row = SpiritEyeTable(
            eye_type=eye_type,
            eye_name=eye_name,
            exp_per_hour=exp_per_hour,
            spawn_time=spawn_time,
            owner_id=None,
            owner_name=None,
            claim_time=None,
            last_collect_time=0
        )
        
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        
        return row.eye_id
    
    def claim_spirit_eye(
        self,
        eye_id: int,
        user_id: str,
        user_name: str,
        claim_time: int
    ) -> bool:
        """占领灵眼（原子操作）"""
        # 使用乐观锁确保原子性
        result = self.session.query(SpiritEyeTable).filter(
            and_(
                SpiritEyeTable.eye_id == eye_id,
                SpiritEyeTable.owner_id.is_(None)
            )
        ).update({
            'owner_id': user_id,
            'owner_name': user_name,
            'claim_time': claim_time,
            'last_collect_time': claim_time
        })
        
        self.session.commit()
        return result > 0
    
    def release_spirit_eye(self, eye_id: int):
        """释放灵眼"""
        self.session.query(SpiritEyeTable).filter(
            SpiritEyeTable.eye_id == eye_id
        ).update({
            'owner_id': None,
            'owner_name': None,
            'claim_time': None,
            'last_collect_time': 0
        })
        self.session.commit()
    
    def update_collect_time(self, eye_id: int, collect_time: int):
        """更新收取时间"""
        self.session.query(SpiritEyeTable).filter(
            SpiritEyeTable.eye_id == eye_id
        ).update({'last_collect_time': collect_time})
        self.session.commit()
    
    def _to_domain(self, row: SpiritEyeTable) -> SpiritEye:
        """转换为领域模型"""
        return SpiritEye(
            eye_id=row.eye_id,
            eye_type=row.eye_type,
            eye_name=row.eye_name,
            exp_per_hour=row.exp_per_hour,
            spawn_time=row.spawn_time,
            owner_id=row.owner_id,
            owner_name=row.owner_name,
            claim_time=row.claim_time,
            last_collect_time=row.last_collect_time
        )
