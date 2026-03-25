"""传承命令处理器"""
import re
from astrbot.api.event import AstrMessageEvent

from ...application.services.impart_service import ImpartService


class ImpartHandler:
    """传承命令处理器"""
    
    def __init__(self, impart_service: ImpartService):
        self.impart_service = impart_service
    
    async def handle_impart_info(self, event: AstrMessageEvent):
        """查看传承信息"""
        user_id = str(event.get_sender_id())
        success, msg = self.impart_service.get_impart_info(user_id)
        yield event.plain_result(msg)
    
    async def handle_impart_challenge(self, event: AstrMessageEvent, target_info: str = ""):
        """发起传承挑战"""
        user_id = str(event.get_sender_id())
        
        # 解析目标
        target_id = self._extract_user_id(target_info, event)
        if not target_id:
            yield event.plain_result(
                "⚔️ 传承挑战\n"
                "━━━━━━━━━━━━━━━\n"
                "争夺对方的传承加成！\n"
                "胜利：获得传承ATK加成\n"
                "失败：损失1%修为\n"
                "━━━━━━━━━━━━━━━\n"
                "💡 用法：/传承挑战 @某人"
            )
            return
        
        success, msg = self.impart_service.challenge_impart(user_id, target_id)
        yield event.plain_result(msg)
    
    async def handle_impart_ranking(self, event: AstrMessageEvent):
        """传承排行榜"""
        success, msg = self.impart_service.get_ranking(10)
        yield event.plain_result(msg)
    
    def _extract_user_id(self, msg: str, event: AstrMessageEvent) -> str:
        """从消息中提取用户ID"""
        if not msg:
            return ""
        
        # 匹配 @xxx 或纯数字
        at_match = re.search(r'\[CQ:at,qq=(\d+)\]', msg)
        if at_match:
            return at_match.group(1)
        
        # 纯数字
        num_match = re.search(r'(\d{5,12})', msg)
        if num_match:
            return num_match.group(1)
        
        return ""
