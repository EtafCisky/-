"""
悬赏仓储层
"""
from typing import Optional
from sqlalchemy.orm import Session

from ...domain.models.bounty import BountyTask
from ..database.schema import BountyTaskTable
from .base_repo import BaseRepository


class BountyRepository(BaseRepository):
    """悬赏仓储"""
    
    def __init__(self, session: Session):
        super().__init__(session)
    
    def get_active_bounty(self, user_id: str) -> Optional[BountyTask]:
        """
        获取进行中的悬赏
        
        Args:
            user_id: 用户ID
            
        Returns:
            悬赏任务，如果没有则返回None
        """
        task_table = self.session.query(BountyTaskTable).filter(
            BountyTaskTable.user_id == user_id,
            BountyTaskTable.status == 1
        ).first()
        
        if not task_table:
            return None
        
        return BountyTask(
            user_id=task_table.user_id,
            bounty_id=task_table.bounty_id,
            bounty_name=task_table.bounty_name,
            target_type=task_table.target_type,
            target_count=task_table.target_count,
            current_progress=task_table.current_progress,
            rewards=task_table.rewards,
            start_time=task_table.start_time,
            expire_time=task_table.expire_time,
            status=task_table.status
        )
    
    def create_task(self, task: BountyTask):
        """
        创建悬赏任务
        
        Args:
            task: 悬赏任务
        """
        task_table = BountyTaskTable(
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
        
        self.session.add(task_table)
        self.session.commit()
    
    def update_task_status(self, user_id: str, status: int):
        """
        更新任务状态
        
        Args:
            user_id: 用户ID
            status: 状态
        """
        self.session.query(BountyTaskTable).filter(
            BountyTaskTable.user_id == user_id,
            BountyTaskTable.status == 1
        ).update({"status": status})
        self.session.commit()
    
    def update_progress(self, user_id: str, progress: int):
        """
        更新任务进度
        
        Args:
            user_id: 用户ID
            progress: 进度
        """
        self.session.query(BountyTaskTable).filter(
            BountyTaskTable.user_id == user_id,
            BountyTaskTable.status == 1
        ).update({"current_progress": progress})
        self.session.commit()
    
    def get_abandon_cooldown(self, user_id: str) -> Optional[int]:
        """
        获取放弃冷却时间
        
        Args:
            user_id: 用户ID
            
        Returns:
            冷却结束时间戳，如果没有则返回None
        """
        # 使用系统配置表存储冷却时间
        from ..database.schema import SystemConfigTable
        
        config = self.session.query(SystemConfigTable).filter(
            SystemConfigTable.key == f"bounty_abandon_cd_{user_id}"
        ).first()
        
        if config:
            try:
                return int(config.value)
            except ValueError:
                return None
        return None
    
    def set_abandon_cooldown(self, user_id: str, cooldown_time: int):
        """
        设置放弃冷却时间
        
        Args:
            user_id: 用户ID
            cooldown_time: 冷却结束时间戳
        """
        from ..database.schema import SystemConfigTable
        
        config = self.session.query(SystemConfigTable).filter(
            SystemConfigTable.key == f"bounty_abandon_cd_{user_id}"
        ).first()
        
        if config:
            config.value = str(cooldown_time)
        else:
            config = SystemConfigTable(
                key=f"bounty_abandon_cd_{user_id}",
                value=str(cooldown_time)
            )
            self.session.add(config)
        
        self.session.commit()
    
    # 实现抽象方法
    def get_by_id(self, entity_id: str):
        """获取实体（悬赏仓储不需要此方法）"""
        raise NotImplementedError("悬赏仓储不支持通过ID获取")
    
    def save(self, entity):
        """保存实体（使用 create_task 代替）"""
        raise NotImplementedError("使用 create_task 方法")
    
    def delete(self, entity_id: str):
        """删除实体（使用 update_task_status 代替）"""
        raise NotImplementedError("使用 update_task_status 方法")
    
    def exists(self, entity_id: str) -> bool:
        """检查实体是否存在"""
        return self.get_active_bounty(entity_id) is not None
