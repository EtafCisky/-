"""悬赏仓储"""
from typing import Optional
from sqlalchemy.orm import Session
import time

from ..database.schema import BountyTaskTable
from ...domain.models.bounty import BountyTask


class BountyRepository:
    """悬赏仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_active_bounty(self, user_id: str) -> Optional[BountyTask]:
        """获取玩家当前进行中的悬赏"""
        row = self.session.query(BountyTaskTable).filter(
            BountyTaskTable.user_id == user_id,
            BountyTaskTable.status == 1
        ).first()
        
        if not row:
            return None
        
        return self._to_domain(row)
    
    def create_bounty_task(self, task: BountyTask) -> int:
        """创建悬赏任务"""
        row = BountyTaskTable(
            user_id=task.user_id,
            bounty_id=task.bounty_id,
            bounty_name=task.bounty_name,
            target_type=task.target_type,
            target_count=task.target_count,
            current_progress=task.current_progress,
            rewards=task.rewards,
            start_time=task.start_time,
            expire_time=task.expire_time,
            status=task.status
        )
        
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        
        return row.task_id
    
    def update_progress(self, user_id: str, new_progress: int, old_progress: int) -> bool:
        """更新悬赏进度（使用乐观锁）"""
        result = self.session.query(BountyTaskTable).filter(
            BountyTaskTable.user_id == user_id,
            BountyTaskTable.status == 1,
            BountyTaskTable.current_progress == old_progress
        ).update({
            "current_progress": new_progress
        })
        self.session.commit()
        return result > 0
    
    def complete_bounty(self, user_id: str) -> None:
        """完成悬赏"""
        self.session.query(BountyTaskTable).filter(
            BountyTaskTable.user_id == user_id,
            BountyTaskTable.status == 1
        ).update({
            "status": 2
        })
        self.session.commit()
    
    def cancel_bounty(self, user_id: str) -> None:
        """取消悬赏"""
        self.session.query(BountyTaskTable).filter(
            BountyTaskTable.user_id == user_id,
            BountyTaskTable.status == 1
        ).update({
            "status": 0
        })
        self.session.commit()
    
    def expire_bounties(self) -> int:
        """过期所有超时的悬赏"""
        now = int(time.time())
        result = self.session.query(BountyTaskTable).filter(
            BountyTaskTable.status == 1,
            BountyTaskTable.expire_time < now
        ).update({
            "status": 3
        })
        self.session.commit()
        return result
    
    def _to_domain(self, row: BountyTaskTable) -> BountyTask:
        """转换为领域模型"""
        return BountyTask(
            task_id=row.task_id,
            user_id=row.user_id,
            bounty_id=row.bounty_id,
            bounty_name=row.bounty_name,
            target_type=row.target_type,
            target_count=row.target_count,
            current_progress=row.current_progress,
            rewards=row.rewards,
            start_time=row.start_time,
            expire_time=row.expire_time,
            status=row.status
        )
