"""洞天福地仓储"""
from typing import Optional
from sqlalchemy.orm import Session

from ..database.schema import BlessedLandTable
from ...domain.models.blessed_land import BlessedLand


class BlessedLandRepository:
    """洞天福地仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_blessed_land(self, user_id: str) -> Optional[BlessedLand]:
        """获取洞天福地"""
        row = self.session.query(BlessedLandTable).filter(
            BlessedLandTable.user_id == user_id
        ).first()
        
        if not row:
            return None
        
        return BlessedLand(
            id=row.id,
            user_id=row.user_id,
            land_type=row.land_type,
            land_name=row.land_name,
            level=row.level,
            exp_bonus=row.exp_bonus,
            gold_per_hour=row.gold_per_hour,
            last_collect_time=row.last_collect_time
        )
    
    def create_blessed_land(
        self,
        user_id: str,
        land_type: int,
        land_name: str,
        exp_bonus: float,
        gold_per_hour: int
    ) -> int:
        """创建洞天福地"""
        row = BlessedLandTable(
            user_id=user_id,
            land_type=land_type,
            land_name=land_name,
            level=1,
            exp_bonus=exp_bonus,
            gold_per_hour=gold_per_hour,
            last_collect_time=0
        )
        
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        
        return row.id
    
    def update_blessed_land(
        self,
        user_id: str,
        level: Optional[int] = None,
        exp_bonus: Optional[float] = None,
        gold_per_hour: Optional[int] = None,
        last_collect_time: Optional[int] = None
    ):
        """更新洞天福地"""
        updates = {}
        if level is not None:
            updates['level'] = level
        if exp_bonus is not None:
            updates['exp_bonus'] = exp_bonus
        if gold_per_hour is not None:
            updates['gold_per_hour'] = gold_per_hour
        if last_collect_time is not None:
            updates['last_collect_time'] = last_collect_time
        
        if updates:
            self.session.query(BlessedLandTable).filter(
                BlessedLandTable.user_id == user_id
            ).update(updates)
            self.session.commit()
