"""
炼丹命令处理器

处理炼丹相关的命令。
"""
from typing import AsyncGenerator

from astrbot.api.event import AstrMessageEvent

from ...application.services.alchemy_service import AlchemyService
from ...core.exceptions import BusinessException
from ..decorators import require_player


class AlchemyHandler:
    """炼丹命令处理器"""
    
    def __init__(self, alchemy_service: AlchemyService):
        """
        初始化炼丹命令处理器
        
        Args:
            alchemy_service: 炼丹服务
        """
        self.alchemy_service = alchemy_service
    
    @require_player
    async def handle_show_recipes(
        self, 
        event: AstrMessageEvent
    ) -> AsyncGenerator[str, None]:
        """
        处理查看丹药配方命令
        
        Args:
            event: 消息事件
            
        Yields:
            响应消息
        """
        user_id = event.get_sender_id()
        
        try:
            message = self.alchemy_service.format_recipes(user_id)
            yield event.plain_result(message)
        except BusinessException as e:
            yield event.plain_result(f"❌ {str(e)}")
        except Exception as e:
            yield event.plain_result(f"❌ 系统错误：{str(e)}")
    
    @require_player
    async def handle_craft_pill(
        self, 
        event: AstrMessageEvent,
        recipe_id: str = None
    ) -> AsyncGenerator[str, None]:
        """
        处理炼丹命令
        
        Args:
            event: 消息事件
            recipe_id: 配方ID
            
        Yields:
            响应消息
        """
        user_id = event.get_sender_id()
        
        # 检查是否提供了配方ID
        if not recipe_id:
            yield event.plain_result("❌ 请输入丹药配方ID\n💡 使用 丹药配方 查看可用配方")
            return
        
        try:
            # 转换配方ID为整数
            recipe_id_int = int(recipe_id)
        except ValueError:
            yield event.plain_result("❌ 配方ID必须是数字")
            return
        
        try:
            success, message, result_data = self.alchemy_service.craft_pill(
                user_id, 
                recipe_id_int
            )
            yield event.plain_result(message)
        except BusinessException as e:
            yield event.plain_result(f"❌ {str(e)}")
        except Exception as e:
            yield event.plain_result(f"❌ 系统错误：{str(e)}")
