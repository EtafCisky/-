"""
商店仓储层

处理商店数据的持久化。
"""
import json
from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import Session

from ...domain.models.shop import Shop, ShopItem
from ..database.schema import ShopTable


class ShopRepository:
    """商店仓储"""
    
    def __init__(self, session: Session):
        """
        初始化商店仓储
        
        Args:
            session: 数据库会话
        """
        self.session = session
    
    def get_shop_data(self, shop_id: str) -> Tuple[int, List[Dict]]:
        """
        获取商店数据
        
        Args:
            shop_id: 商店ID
            
        Returns:
            (上次刷新时间, 商品列表)
        """
        shop_record = self.session.query(ShopTable).filter_by(shop_id=shop_id).first()
        
        if not shop_record:
            return 0, []
        
        try:
            items = json.loads(shop_record.items_json) if shop_record.items_json else []
        except json.JSONDecodeError:
            items = []
        
        return shop_record.last_refresh_time, items
    
    def update_shop_data(self, shop_id: str, last_refresh_time: int, items: List[Dict]) -> None:
        """
        更新商店数据
        
        Args:
            shop_id: 商店ID
            last_refresh_time: 刷新时间
            items: 商品列表
        """
        shop_record = self.session.query(ShopTable).filter_by(shop_id=shop_id).first()
        
        items_json = json.dumps(items, ensure_ascii=False)
        
        if shop_record:
            shop_record.last_refresh_time = last_refresh_time
            shop_record.items_json = items_json
        else:
            shop_record = ShopTable(
                shop_id=shop_id,
                last_refresh_time=last_refresh_time,
                items_json=items_json
            )
            self.session.add(shop_record)
        
        self.session.commit()
    
    def decrement_item_stock(
        self, 
        shop_id: str, 
        item_name: str, 
        quantity: int = 1
    ) -> Tuple[bool, int, int]:
        """
        减少商品库存
        
        Args:
            shop_id: 商店ID
            item_name: 商品名称
            quantity: 减少数量
            
        Returns:
            (是否成功, 减少的数量, 剩余库存)
        """
        last_refresh, items = self.get_shop_data(shop_id)
        
        for item in items:
            if item['name'] == item_name:
                current_stock = item.get('stock', 0)
                
                if current_stock < quantity:
                    return False, 0, current_stock
                
                item['stock'] = current_stock - quantity
                remaining = item['stock']
                
                # 更新数据库
                self.update_shop_data(shop_id, last_refresh, items)
                
                return True, quantity, remaining
        
        return False, 0, 0
