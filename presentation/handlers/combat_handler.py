"""战斗命令处理器"""
import re
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import At

from ...application.services.combat_service import CombatService
from ...core.exceptions import PlayerNotFoundException, InvalidStateException
from ..decorators import require_player


class CombatHandler:
    """战斗命令处理器"""
    
    def __init__(self, combat_service: CombatService, player_service):
        self.combat_service = combat_service
        self.player_service = player_service
    
    async def _get_target_id(self, event: AstrMessageEvent, arg: str) -> str:
        """
        从消息中提取目标玩家ID
        
        优先级：
        1. At组件
        2. 参数中的数字ID
        3. 消息文本中的数字ID
        
        Args:
            event: 消息事件
            arg: 命令参数
            
        Returns:
            目标玩家ID，如果未找到返回None
        """
        # 尝试从At组件获取
        message_chain = []
        if hasattr(event, "message_obj") and event.message_obj:
            message_chain = getattr(event.message_obj, "message", []) or []
        
        for component in message_chain:
            if isinstance(component, At):
                # 尝试多个可能的属性名
                candidate = None
                for attr in ("qq", "target", "uin", "user_id"):
                    candidate = getattr(component, attr, None)
                    if candidate:
                        break
                if candidate:
                    return str(candidate).lstrip("@")
        
        # 尝试从参数获取
        if arg:
            cleaned = arg.strip().lstrip("@")
            if cleaned.isdigit():
                return cleaned
        
        # 尝试从消息文本提取数字ID
        message_text = ""
        if hasattr(event, "get_message_str"):
            message_text = event.get_message_str() or ""
        match = re.search(r'(\d{5,})', message_text)
        if match:
            return match.group(1)
        
        return None
    
    @require_player
    async def handle_spar(self, event: AstrMessageEvent, target: str = ""):
        """
        处理切磋命令（不消耗HP/MP）
        
        Args:
            event: 消息事件
            target: 目标参数
        """
        user_id = event.get_sender_id()
        target_id = await self._get_target_id(event, target)
        
        if not target_id:
            yield event.plain_result("❌ 请指定切磋目标\n💡 使用方法：切磋 @对方 或 切磋 [对方ID]")
            return
        
        if user_id == target_id:
            yield event.plain_result("❌ 不能和自己切磋")
            return
        
        try:
            # 检查冷却
            can_fight, remaining = await self.combat_service.check_combat_cooldown(user_id, "spar")
            if not can_fight:
                yield event.plain_result(f"❌ 切磋冷却中，还需 {remaining} 秒")
                return
            
            # 检查目标是否存在
            target_stats = await self.combat_service.prepare_combat_stats(target_id)
            if not target_stats:
                yield event.plain_result("❌ 对方还未踏入修仙之路")
                return
            
            # TODO: 检查双方状态（需要状态系统）
            
            # 执行切磋
            result = await self.combat_service.execute_spar(user_id, target_id)
            
            # 格式化输出
            log_text = "\n".join(result.combat_log)
            yield event.plain_result(log_text)
            
        except PlayerNotFoundException:
            yield event.plain_result("❌ 你还未踏入修仙之路")
        except InvalidStateException as e:
            yield event.plain_result(f"❌ {str(e)}")
        except Exception as e:
            yield event.plain_result(f"❌ 切磋失败：{str(e)}")
    
    @require_player
    async def handle_duel(self, event: AstrMessageEvent, target: str = ""):
        """
        处理决斗命令（消耗HP/MP）
        
        Args:
            event: 消息事件
            target: 目标参数
        """
        user_id = event.get_sender_id()
        target_id = await self._get_target_id(event, target)
        
        if not target_id:
            yield event.plain_result("❌ 请指定决斗目标\n💡 使用方法：决斗 @对方 或 决斗 [对方ID]")
            return
        
        if user_id == target_id:
            yield event.plain_result("❌ 不能和自己决斗")
            return
        
        try:
            # 检查冷却
            can_fight, remaining = await self.combat_service.check_combat_cooldown(user_id, "duel")
            if not can_fight:
                minutes = remaining // 60
                seconds = remaining % 60
                yield event.plain_result(f"❌ 决斗冷却中，还需 {minutes} 分 {seconds} 秒")
                return
            
            # 检查目标是否存在
            target_stats = await self.combat_service.prepare_combat_stats(target_id)
            if not target_stats:
                yield event.plain_result("❌ 对方还未踏入修仙之路")
                return
            
            # TODO: 检查双方状态（需要状态系统）
            
            # 执行决斗
            result = await self.combat_service.execute_duel(user_id, target_id)
            
            # 格式化输出
            log_text = "\n".join(result.combat_log)
            yield event.plain_result(log_text)
            
        except PlayerNotFoundException:
            yield event.plain_result("❌ 你还未踏入修仙之路")
        except InvalidStateException as e:
            yield event.plain_result(f"❌ {str(e)}")
        except Exception as e:
            yield event.plain_result(f"❌ 决斗失败：{str(e)}")
    
    @require_player
    async def handle_combat_log(self, event: AstrMessageEvent):
        """
        处理查看战斗记录命令
        
        Args:
            event: 消息事件
        """
        # TODO: 实现战斗记录查询
        yield event.plain_result("⚠️ 战斗记录功能开发中...")
