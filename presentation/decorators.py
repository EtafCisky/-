"""表现层装饰器"""
from functools import wraps
from typing import Callable

from astrbot.api.event import AstrMessageEvent


def require_player(func: Callable):
    """
    装饰器：要求玩家存在
    
    如果玩家不存在，返回提示消息
    如果玩家存在，将玩家对象作为参数传递给处理函数
    """
    @wraps(func)
    async def wrapper(self, event: AstrMessageEvent, *args, **kwargs):
        user_id = event.get_sender_id()
        
        # 从服务层获取玩家
        player = self.player_service.get_player(user_id)
        
        if not player:
            yield event.plain_result(
                "❌ 你还未踏入修仙之路！\n"
                "💡 发送「我要修仙」开始你的修仙之旅"
            )
            return
        
        # 将玩家对象传递给处理函数
        async for result in func(self, event, player, *args, **kwargs):
            yield result
    
    return wrapper


def check_player_state(required_state: str):
    """
    装饰器：检查玩家状态
    
    Args:
        required_state: 要求的状态
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, event: AstrMessageEvent, player, *args, **kwargs):
            if player.state.value != required_state:
                yield event.plain_result(
                    f"❌ 当前状态「{player.state.value}」无法执行此操作\n"
                    f"需要状态：{required_state}"
                )
                return
            
            async for result in func(self, event, player, *args, **kwargs):
                yield result
        
        return wrapper
    return decorator
