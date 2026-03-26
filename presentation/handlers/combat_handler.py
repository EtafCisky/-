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
        从命令参数中提取目标玩家ID
        
        优先级：
        1. 参数中的数字ID
        2. 参数后面的At组件（排除bot自己）
        
        Args:
            event: 消息事件
            arg: 命令参数
            
        Returns:
            目标玩家ID，如果未找到返回None
        """
        # 优先从参数获取数字ID
        if arg:
            cleaned = arg.strip().lstrip("@")
            if cleaned.isdigit():
                return cleaned
        
        # 从At组件获取（只获取命令参数部分的At，排除艾特bot的）
        message_chain = []
        if hasattr(event, "message_obj") and event.message_obj:
            message_chain = getattr(event.message_obj, "message", []) or []
        
        # 获取bot自己的ID（如果可用）
        bot_id = None
        if hasattr(event, "get_bot_id"):
            bot_id = str(event.get_bot_id())
        
        # 遍历消息链，找到命令后面的At组件
        found_command = False
        for component in message_chain:
            # 检查是否是文本组件且包含命令
            if hasattr(component, "text"):
                text = getattr(component, "text", "")
                if "切磋" in text or "决斗" in text:
                    found_command = True
                    continue
            
            # 如果已经找到命令，且当前是At组件
            if found_command and isinstance(component, At):
                # 尝试多个可能的属性名
                candidate = None
                for attr in ("qq", "target", "uin", "user_id"):
                    candidate = getattr(component, attr, None)
                    if candidate:
                        break
                
                if candidate:
                    target_id = str(candidate).lstrip("@")
                    # 排除bot自己
                    if bot_id and target_id == bot_id:
                        continue
                    return target_id
        
        return None
    
    @require_player
    async def handle_spar(self, event: AstrMessageEvent, player, target: str = ""):
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
    async def handle_duel(self, event: AstrMessageEvent, player, target: str = ""):
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
    async def handle_combat_log(self, event: AstrMessageEvent, player):
        """
        处理查看战斗记录命令
        
        Args:
            event: 消息事件
        """
        # TODO: 实现战斗记录查询
        yield event.plain_result("⚠️ 战斗记录功能开发中...")
