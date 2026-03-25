"""传承系统仓储"""
from typing import Optional, List
from sqlalchemy.orm import Session

from ...domain.models.impart import ImpartInfo
from ..database.schema import ImpartInfoTable


class ImpartRepository:
    """传承仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_impart_info(self, user_id: str) -> Optional[ImpartInfo]:
        """获取传承信息"""
        row = self.session.query(ImpartInfoTable).filter_by(user_id=user_id).first()
        if not row:
            return None
        return ImpartInfo(
            user_id=row.user_id,
            impart_hp_per=row.impart_hp_per,
            impart_mp_per=row.impart_mp_per,
            impart_atk_per=row.impart_atk_per,
            impart_know_per=row.impart_know_per,
            impart_burst_per=row.impart_burst_per,
            impart_mix_exp=row.impart_mix_exp
        )
    
    def create_impart_info(self, user_id: str) -> ImpartInfo:
        """创建传承信息"""
        new_row = ImpartInfoTable(user_id=user_id)
        self.session.add(new_row)
        self.session.commit()
        return ImpartInfo(user_id=user_id)
    
    def update_impart_info(self, impart_info: ImpartInfo):
        """更新传承信息"""
        row = self.session.query(ImpartInfoTable).filter_by(user_id=impart_info.user_id).first()
        if row:
            row.impart_hp_per = impart_info.impart_hp_per
            row.impart_mp_per = impart_info.impart_mp_per
            row.impart_atk_per = impart_info.impart_atk_per
            row.impart_know_per = impart_info.impart_know_per
            row.impart_burst_per = impart_info.impart_burst_per
            row.impart_mix_exp = impart_info.impart_mix_exp
            self.session.commit()
    
    def get_ranking(self, limit: int = 10) -> List[tuple]:
        """获取传承排行榜
        
        Returns:
            List of (user_id, impart_atk_per, total_per)
        """
        rows = self.session.query(
            ImpartInfoTable.user_id,
            ImpartInfoTable.impart_atk_per,
            (ImpartInfoTable.impart_hp_per + ImpartInfoTable.impart_mp_per + 
             ImpartInfoTable.impart_atk_per + ImpartInfoTable.impart_know_per + 
             ImpartInfoTable.impart_burst_per).label('total_per')
        ).order_by(ImpartInfoTable.impart_atk_per.desc()).limit(limit).all()
        
        return [(row.user_id, row.impart_atk_per, row.total_per) for row in rows]
