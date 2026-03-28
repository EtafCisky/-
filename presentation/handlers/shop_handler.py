"""
商店命令处理器

处理商店相关的命令。
"""
import re
from typing import AsyncGenerator

from astrbot.api.event import AstrMessageEvent

from ...application.services.shop_service import ShopService
from ...core.exceptions import BusinessException
from ..decorators import require_player


class ShopHandler:
    """商店命令处理器"""
    
    def __init__(self, shop_service: ShopService, player_service):
        """
        初始化商店命令处理器
        
        Args:
            shop_service: 商店服务
            player_service: 玩家服务
        """
        self.shop_service = shop_service
        self.player_service = player_service
    
    async def handle_pill_pavilion(
        self, 
        event: AstrMessageEvent
    ) -> AsyncGenerator[str, None]:
        """
        处理丹阁命令 - 展示丹药列表
        
        Args:
            event: 消息事件
            
        Yields:
            响应消息
        """
        try:
            # 丹药过滤器
            def pill_filter(item):
                return item['type'] in ['pill', 'exp_pill', 'utility_pill']
            
            shop = self.shop_service.ensure_shop_refreshed(
                shop_id="pill_pavilion",
                shop_name="丹阁",
                item_filter=pill_filter,
                count=10,
                refresh_hours=6
            )
            
            display = self.shop_service.format_shop_display(shop)
            yield event.plain_result(display)
        except Exception as e:
            yield event.plain_result(f"❌ 系统错误：{str(e)}")
    
    async def handle_weapon_pavilion(
        self, 
        event: AstrMessageEvent
    ) -> AsyncGenerator[str, None]:
        """
        处理器阁命令 - 展示武器装备列表
        
        Args:
            event: 消息事件
            
        Yields:
            响应消息
        """
        try:
            # 武器装备过滤器
            def weapon_filter(item):
                return item['type'] in ['weapon', 'armor', 'accessory']
            
            shop = self.shop_service.ensure_shop_refreshed(
                shop_id="weapon_pavilion",
                shop_name="器阁",
                item_filter=weapon_filter,
                count=10,
                refresh_hours=6
            )
            
            display = self.shop_service.format_shop_display(shop)
            yield event.plain_result(display)
        except Exception as e:
            yield event.plain_result(f"❌ 系统错误：{str(e)}")
    
    async def handle_treasure_pavilion(
        self, 
        event: AstrMessageEvent
    ) -> AsyncGenerator[str, None]:
        """
        处理百宝阁命令 - 展示所有物品
        
        Args:
            event: 消息事件
            
        Yields:
            响应消息
        """
        try:
            # 不过滤，显示所有物品
            shop = self.shop_service.ensure_shop_refreshed(
                shop_id="treasure_pavilion",
                shop_name="百宝阁",
                item_filter=None,
                count=15,
                refresh_hours=6
            )
            
            display = self.shop_service.format_shop_display(shop)
            yield event.plain_result(display)
        except Exception as e:
            yield event.plain_result(f"❌ 系统错误：{str(e)}")
    
    @require_player
    async def handle_buy(
        self, 
        event: AstrMessageEvent,
        player,
        args: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        处理购买物品命令
        
        Args:
            event: 消息事件
            player: 玩家对象（由装饰器注入）
            args: 参数（物品名 [数量]）
            
        Yields:
            响应消息
        """
        user_id = event.get_sender_id()
        
        print(f"[DEBUG] handle_buy 接收到的参数: args='{args}'")
        
        if not args or args.strip() == "":
            yield event.plain_result("请指定要购买的物品名称，例如：购买 青铜剑 或 购买 一品凝气丹 10")
            return
        
        # 解析物品名和数量
        item_name, quantity = self._parse_buy_args(args)
        
        print(f"[DEBUG] 解析结果: item_name='{item_name}', quantity={quantity}")
        
        if not item_name:
            yield event.plain_result("请指定要购买的物品名称")
            return
        
        try:
            # 在所有阁楼中查找物品
            shop_id = self._find_item_in_pavilions(item_name)
            if not shop_id:
                yield event.plain_result(f"没有找到【{item_name}】，请检查物品名称或等待刷新。")
                return
            
            # 购买物品
            print(f"[DEBUG] 调用 buy_item: user_id={user_id}, shop_id={shop_id}, item_name={item_name}, quantity={quantity}")
            success, message = self.shop_service.buy_item(
                user_id, shop_id, item_name, quantity
            )
            yield event.plain_result(message)
        except BusinessException as e:
            yield event.plain_result(f"❌ {str(e)}")
        except Exception as e:
            yield event.plain_result(f"❌ 系统错误：{str(e)}")
    
    def _parse_buy_args(self, args: str) -> tuple:
        """
        解析购买参数
        
        Args:
            args: 参数字符串
            
        Returns:
            (物品名, 数量)
        """
        args = args.strip()
        
        # 使用 rsplit 从右边分割，只分割最后一个空格
        # 这样可以正确处理带空格的物品名，如"一品凝气丹"
        parts = args.rsplit(" ", 1)
        
        # 解析物品名和数量
        if len(parts) == 2:
            item_name = parts[0].strip()
            qty_str = parts[1].strip()
            
            # 检查是否是数字（支持全角数字）
            qty_str_normalized = qty_str.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
            
            # 支持 "x10" 或 "*10" 格式
            if qty_str_normalized.startswith(('x', 'X', '*', '＊')):
                qty_str_normalized = qty_str_normalized[1:]
            
            if qty_str_normalized.isdigit():
                quantity = max(1, int(qty_str_normalized))
                print(f"[DEBUG] 解析购买参数: args='{args}' -> item_name='{item_name}', quantity={quantity}")
                return item_name, quantity
        
        # 没有数量或格式不对，默认为1
        print(f"[DEBUG] 解析购买参数(无数量): args='{args}' -> item_name='{args}', quantity=1")
        return args, 1
    
    def _find_item_in_pavilions(self, item_name: str) -> str:
        """
        在所有阁楼中查找物品
        
        Args:
            item_name: 物品名称
            
        Returns:
            商店ID，如果未找到则返回空字符串
        """
        for pavilion_id in ["pill_pavilion", "weapon_pavilion", "treasure_pavilion"]:
            last_refresh, items = self.shop_service.shop_repo.get_shop_data(pavilion_id)
            if items:
                for item in items:
                    if item['name'] == item_name and item.get('stock', 0) > 0:
                        return pavilion_id
        return ""
