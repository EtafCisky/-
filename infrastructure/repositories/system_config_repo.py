"""系统配置仓储"""
from typing import Optional
from sqlalchemy.orm import Session

from ..database.schema import SystemConfigTable


class SystemConfigRepository:
    """系统配置仓储"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_config(self, key: str) -> Optional[str]:
        """
        获取配置值
        
        Args:
            key: 配置键
            
        Returns:
            配置值，不存在则返回None
        """
        config = self.session.query(SystemConfigTable).filter_by(key=key).first()
        return config.value if config else None
    
    def set_config(self, key: str, value: str) -> None:
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        import time
        
        config = self.session.query(SystemConfigTable).filter_by(key=key).first()
        
        if config:
            config.value = value
            config.updated_at = int(time.time())
        else:
            config = SystemConfigTable(
                key=key,
                value=value,
                updated_at=int(time.time())
            )
            self.session.add(config)
        
        self.session.commit()
    
    def delete_config(self, key: str) -> None:
        """
        删除配置
        
        Args:
            key: 配置键
        """
        self.session.query(SystemConfigTable).filter_by(key=key).delete()
        self.session.commit()
