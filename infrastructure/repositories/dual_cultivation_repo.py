"""双修系统仓储"""
import time
from typing import Optional
from sqlalchemy.orm import Session

from ...domain.models.dual_cultivation import DualCultivationCooldown, DualCultivationRequest
from ..database.schema import DualCultivationTable, DualCultivationRequestTable


class DualCultivationRepository:
    """双修仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_cooldown(self, user_id: str) -> Optional[DualCultivationCooldown]:
        """获取冷却信息"""
        row = self.session.query(DualCultivationTable).filter_by(user_id=user_id).first()
        if not row:
            return None
        return DualCultivationCooldown(
            user_id=row.user_id,
            last_dual_time=row.last_dual_time
        )
    
    def set_cooldown(self, user_id: str, timestamp: int):
        """设置冷却时间"""
        row = self.session.query(DualCultivationTable).filter_by(user_id=user_id).first()
        if row:
            row.last_dual_time = timestamp
        else:
            new_row = DualCultivationTable(user_id=user_id, last_dual_time=timestamp)
            self.session.add(new_row)
        self.session.commit()
    
    def create_request(self, from_id: str, from_name: str, target_id: str, expires_at: int) -> int:
        """创建双修请求"""
        now = int(time.time())
        
        # 删除目标的旧请求
        self.session.query(DualCultivationRequestTable).filter_by(target_id=target_id).delete()
        
        # 创建新请求
        new_request = DualCultivationRequestTable(
            from_id=from_id,
            from_name=from_name,
            target_id=target_id,
            created_at=now,
            expires_at=expires_at
        )
        self.session.add(new_request)
        self.session.commit()
        self.session.refresh(new_request)
        return new_request.id
    
    def get_pending_request(self, target_id: str) -> Optional[DualCultivationRequest]:
        """获取待处理的请求"""
        now = int(time.time())
        
        # 清理过期请求
        self.session.query(DualCultivationRequestTable).filter(
            DualCultivationRequestTable.expires_at < now
        ).delete()
        self.session.commit()
        
        # 获取有效请求
        row = self.session.query(DualCultivationRequestTable).filter(
            DualCultivationRequestTable.target_id == target_id,
            DualCultivationRequestTable.expires_at > now
        ).order_by(DualCultivationRequestTable.created_at.desc()).first()
        
        if not row:
            return None
        
        return DualCultivationRequest(
            id=row.id,
            from_id=row.from_id,
            from_name=row.from_name,
            target_id=row.target_id,
            created_at=row.created_at,
            expires_at=row.expires_at
        )
    
    def delete_request(self, request_id: int):
        """删除请求"""
        self.session.query(DualCultivationRequestTable).filter_by(id=request_id).delete()
        self.session.commit()
