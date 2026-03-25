"""表现层装饰器"""
import inspect
from functools import wraps
from typing import Callable

from astrbot.api.event import AstrMessageEvent


def require_player(func: Callable):
    """
    装饰器：要求玩家存在
    
    如果玩家不存在，返回提示消息
    如果玩家存在，将玩家对象作为参数传递给处理函数
    
    支持异步生成器和普通异步函数
    """
    @wraps(func)
    async def wrapper(self, event: AstrMessageEvent, *args, **kwargs):
        user_id = event.get_sender_id()
        
        # 从服务层获取玩家
        player = self.player_service.get_player(user_id)
        
        # 关闭读取玩家时使用的会话
        try:
            if hasattr(self.player_service, 'player_repo') and hasattr(self.player_service.player_repo, 'session'):
                self.player_service.player_repo.session.close()
        except Exception:
            pass  # 忽略关闭错误
        
        if not player:
            yield event.plain_result(
                "❌ 你还未踏入修仙之路！\n"
                "💡 发送「我要修仙」开始你的修仙之旅"
            )
            return
        
        # 检查被装饰函数的类型
        result = func(self, event, player, *args, **kwargs)
        
        # 如果是异步生成器，使用 async for
        if inspect.isasyncgen(result):
            async for item in result:
                yield item
        # 如果是协程（普通异步函数），使用 await
        elif inspect.iscoroutine(result):
            yield await result
        else:
            # 不应该到达这里，但为了安全起见
            raise TypeError(
                f"被装饰的函数 {func.__name__} 必须是异步生成器或异步函数，"
                f"但得到了 {type(result)}"
            )
    
    return wrapper


def check_player_state(required_state: str):
    """
    装饰器：检查玩家状态
    
    Args:
        required_state: 要求的状态
        
    支持异步生成器和普通异步函数
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
            
            # 检查被装饰函数的类型
            result = func(self, event, player, *args, **kwargs)
            
            # 如果是异步生成器，使用 async for
            if inspect.isasyncgen(result):
                async for item in result:
                    yield item
            # 如果是协程（普通异步函数），使用 await
            elif inspect.iscoroutine(result):
                yield await result
            else:
                # 不应该到达这里，但为了安全起见
                raise TypeError(
                    f"被装饰的函数 {func.__name__} 必须是异步生成器或异步函数，"
                    f"但得到了 {type(result)}"
                )
        
        return wrapper
    return decorator
