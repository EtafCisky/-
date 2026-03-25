"""灵田仓储"""
import json
from typing import Optional
from sqlalchemy.orm import Session

from ..database.schema import SpiritFarmTable
from ...domain.models.spirit_farm import SpiritFarm, Crop


class SpiritFarmRepository:
    """灵田仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_spirit_farm(self, user_id: str) -> Optional[SpiritFarm]:
        """获取灵田"""
        row = self.session.query(SpiritFarmTable).filter(
            SpiritFarmTable.user_id == user_id
        ).first()
        
        if not row:
            return None
        
        # 解析作物JSON
        crops_data = json.loads(row.crops) if row.crops else []
        crops = [
            Crop(
                name=c['name'],
                plant_time=c['plant_time'],
                mature_time=c['mature_time'],
                wither_time=c['wither_time'],
                slot=c['slot']
            )
            for c in crops_data
        ]
        
        return SpiritFarm(
            id=row.id,
            user_id=row.user_id,
            level=row.level,
            crops=crops
        )
    
    def create_spirit_farm(self, user_id: str) -> int:
        """创建灵田"""
        row = SpiritFarmTable(
            user_id=user_id,
            level=1,
            crops='[]'
        )
        
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        
        return row.id
    
    def update_crops(self, user_id: str, crops: list):
        """更新作物列表"""
        # 转换为JSON
        crops_json = json.dumps([
            {
                'name': c.name,
                'plant_time': c.plant_time,
                'mature_time': c.mature_time,
                'wither_time': c.wither_time,
                'slot': c.slot
            }
            for c in crops
        ], ensure_ascii=False)
        
        self.session.query(SpiritFarmTable).filter(
            SpiritFarmTable.user_id == user_id
        ).update({'crops': crops_json})
        self.session.commit()
    
    def update_level(self, user_id: str, level: int):
        """更新灵田等级"""
        self.session.query(SpiritFarmTable).filter(
            SpiritFarmTable.user_id == user_id
        ).update({'level': level})
        self.session.commit()
