"""基础仓储"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List
from sqlalchemy.orm import Session

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """基础仓储接口"""
    
    def __init__(self, session: Session):
        self.session = session
    
    @abstractmethod
    def get_by_id(self, id: str) -> Optional[T]:
        """根据ID获取实体"""
        pass
    
    @abstractmethod
    def save(self, entity: T) -> None:
        """保存实体"""
        pass
    
    @abstractmethod
    def delete(self, id: str) -> None:
        """删除实体"""
        pass
    
    @abstractmethod
    def exists(self, id: str) -> bool:
        """检查实体是否存在"""
        pass
