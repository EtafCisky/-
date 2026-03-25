"""储物戒仓储层"""
import json
import time
from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session

from ..database.schema import PlayerTable, PendingGiftTable


class StorageRingRepository:
    """储物戒仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_storage_ring_items(self, user_id: str) -> Dict[str, int]:
        """获取储物戒物品"""
        player = self.session.query(PlayerTable).filter_by(user_id=user_id).first()
        if not player or not player.storage_ring_items:
            return {}
        
        try:
            return json.loads(player.storage_ring_items)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_storage_ring_items(self, user_id: str, items: Dict[str, int]) -> None:
        """设置储物戒物品"""
        player = self.session.query(PlayerTable).filter_by(user_id=user_id).first()
        if player:
            player.storage_ring_items = json.dumps(items, ensure_ascii=False)
            player.updated_at = int(time.time())
            self.session.commit()
    
    def get_storage_ring_name(self, user_id: str) -> str:
        """获取储物戒名称"""
        player = self.session.query(PlayerTable).filter_by(user_id=user_id).first()
        return player.storage_ring if player else "基础储物戒"
    
    def set_storage_ring_name(self, user_id: str, ring_name: str) -> None:
        """设置储物戒名称"""
        player = self.session.query(PlayerTable).filter_by(user_id=user_id).first()
        if player:
            player.storage_ring = ring_name
            player.updated_at = int(time.time())
            self.session.commit()
    
    # ===== 赠予系统 =====
    
    def create_pending_gift(
        self,
        receiver_id: str,
        sender_id: str,
        sender_name: str,
        item_name: str,
        count: int,
        expires_hours: int = 24
    ) -> int:
        """创建待处理赠予"""
        current_time = int(time.time())
        expires_at = current_time + (expires_hours * 3600)
        
        gift = PendingGiftTable(
            receiver_id=receiver_id,
            sender_id=sender_id,
            sender_name=sender_name,
            item_name=item_name,
            count=count,
            created_at=current_time,
            expires_at=expires_at
        )
        
        self.session.add(gift)
        self.session.commit()
        return gift.id
    
    def get_pending_gift(self, receiver_id: str) -> Optional[Dict]:
        """获取待处理赠予（最早的一个）"""
        current_time = int(time.time())
        
        # 先删除过期的赠予
        self.session.query(PendingGiftTable).filter(
            PendingGiftTable.expires_at < current_time
        ).delete()
        self.session.commit()
        
        # 获取最早的待处理赠予
        gift = self.session.query(PendingGiftTable).filter_by(
            receiver_id=receiver_id
        ).order_by(PendingGiftTable.created_at).first()
        
        if not gift:
            return None
        
        return {
            "id": gift.id,
            "receiver_id": gift.receiver_id,
            "sender_id": gift.sender_id,
            "sender_name": gift.sender_name,
            "item_name": gift.item_name,
            "count": gift.count,
            "created_at": gift.created_at,
            "expires_at": gift.expires_at
        }
    
    def delete_pending_gift(self, gift_id: int) -> None:
        """删除待处理赠予"""
        self.session.query(PendingGiftTable).filter_by(id=gift_id).delete()
        self.session.commit()
    
    def cleanup_expired_gifts(self) -> int:
        """清理过期赠予，返回清理数量"""
        current_time = int(time.time())
        count = self.session.query(PendingGiftTable).filter(
            PendingGiftTable.expires_at < current_time
        ).delete()
        self.session.commit()
        return count
