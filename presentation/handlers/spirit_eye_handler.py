"""天地灵眼命令处理器"""
from typing import AsyncGenerator
from astrbot.api.event import AstrMessageEvent

from ...application.services.spirit_eye_service import SpiritEyeService
from ...core.exceptions import GameException


class SpiritEyeHandler:
    """天地灵眼命令处理器"""
    
    def __init__(self, spirit_eye_service: SpiritEyeService):
        self.spirit_eye_service = spirit_eye_service
    
    async def handle_spirit_eye_info(self, event: AstrMessageEvent) -> AsyncGenerator:
        """处理查看灵眼信息命令"""
        try:
            user_id = event.get_sender_id()
            
            # 获取灵眼信息
            my_eye, available_eyes = self.spirit_eye_service.get_spirit_eye_info(user_id)
            
            lines = ["👁️ 天地灵眼", "━━━━━━━━━━━━━━━"]
            
            if my_eye:
                lines.append(f"【我的灵眼】{my_eye.eye_name}")
                lines.append(f"每小时：+{my_eye.exp_per_hour:,} 修为")
                lines.append(f"待收取：约 +{my_eye.pending_exp:,} 修为")
                lines.append("")
            
            if available_eyes:
                lines.append("【可抢占的灵眼】")
                for eye in available_eyes:
                    lines.append(f"  [{eye.eye_id}] {eye.eye_name} (+{eye.exp_per_hour}/时)")
                lines.append("")
                lines.append("💡 抢占灵眼 <ID>")
            else:
                lines.append("当前没有无主灵眼。")
            
            yield event.plain_result("\n".join(lines))
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"查询灵眼信息失败：{e}")
    
    async def handle_claim(self, event: AstrMessageEvent, eye_id: str = "") -> AsyncGenerator:
        """处理抢占灵眼命令"""
        try:
            user_id = event.get_sender_id()
            
            # 解析灵眼ID
            if not eye_id:
                yield event.plain_result("❌ 请输入灵眼ID，例如：抢占灵眼 1")
                return
            
            try:
                eye_id_int = int(eye_id)
            except ValueError:
                yield event.plain_result("❌ 灵眼ID必须是数字")
                return
            
            result = self.spirit_eye_service.claim_spirit_eye(user_id, eye_id_int)
            yield event.plain_result(result)
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"抢占灵眼失败：{e}")
    
    async def handle_collect(self, event: AstrMessageEvent) -> AsyncGenerator:
        """处理收取灵眼命令"""
        try:
            user_id = event.get_sender_id()
            result = self.spirit_eye_service.collect_spirit_eye(user_id)
            yield event.plain_result(result)
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"收取灵眼失败：{e}")
    
    async def handle_release(self, event: AstrMessageEvent) -> AsyncGenerator:
        """处理释放灵眼命令"""
        try:
            user_id = event.get_sender_id()
            result = self.spirit_eye_service.release_spirit_eye(user_id)
            yield event.plain_result(result)
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"释放灵眼失败：{e}")
