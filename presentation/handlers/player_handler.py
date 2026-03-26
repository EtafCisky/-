"""玩家命令处理器"""
from astrbot.api.event import AstrMessageEvent

from ...application.services.player_service import PlayerService
from ...core.exceptions import (
    PlayerAlreadyExistsException,
    InvalidParameterException
)
from ...domain.enums import CultivationType
from ...utils.spirit_root_generator import SpiritRootGenerator
from ..decorators import require_player
from ..formatters import PlayerFormatter


class PlayerHandler:
    """玩家命令处理器"""
    
    def __init__(
        self,
        player_service: PlayerService,
        spirit_root_generator: SpiritRootGenerator,
        container=None
    ):
        self.player_service = player_service
        self.spirit_root_generator = spirit_root_generator
        self.container = container
    
    async def handle_create_player(
        self,
        event: AstrMessageEvent,
        cultivation_type: str = ""
    ):
        """
        处理创建角色命令
        
        Args:
            event: 消息事件
            cultivation_type: 修炼类型（"灵修"或"体修"）
        """
        user_id = event.get_sender_id()
        
        # 如果没有提供修炼类型，显示帮助信息
        if not cultivation_type or cultivation_type.strip() == "":
            help_msg = PlayerFormatter.format_create_help()
            yield event.plain_result(help_msg)
            return
        
        # 验证修炼类型
        cultivation_type = cultivation_type.strip()
        try:
            cult_type = CultivationType.from_string(cultivation_type)
        except ValueError:
            yield event.plain_result("❌ 职业选择错误！请选择「灵修」或「体修」。")
            return
        
        # 创建玩家
        try:
            # 获取QQ昵称
            sender_name = event.get_sender_name()
            
            player = self.player_service.create_player(user_id, cult_type, sender_name)
            
            # 获取灵根信息用于显示
            root_name = player.spiritual_root.replace("灵根", "")
            spirit_root_info = self.spirit_root_generator.generate_random_root()
            # 这里简化处理，实际应该从已生成的灵根获取描述
            # 为了演示，我们重新查找描述
            from ...utils.spirit_root_generator import SpiritRootGenerator
            description = SpiritRootGenerator.ROOT_DESCRIPTIONS.get(
                root_name,
                "【未知】神秘的灵根"
            )
            
            # 创建临时的灵根信息对象用于格式化
            from ...domain.value_objects import SpiritRootInfo
            temp_root_info = SpiritRootInfo(
                name=root_name,
                speed_multiplier=1.0,
                description=description
            )
            
            # 格式化输出
            sender_name = event.get_sender_name()
            message = PlayerFormatter.format_create_success(
                player,
                temp_root_info,
                sender_name
            )
            
            yield event.plain_result(message)
            
        except PlayerAlreadyExistsException:
            yield event.plain_result("❌ 道友，你已踏入仙途，无需重复此举。")
        except Exception as e:
            yield event.plain_result(f"❌ 创建角色失败：{str(e)}")
    
    @require_player
    async def handle_player_info(self, event: AstrMessageEvent, player):
        """
        处理查看信息命令
        
        Args:
            event: 消息事件
            player: 玩家对象（由装饰器注入）
        """
        try:
            # 获取境界名称
            level_name = self.player_service.get_level_name(player)
            
            # 获取突破所需修为
            required_exp = self.player_service.get_required_exp(player)
            
            # 计算战力
            combat_power = player.calculate_power()
            
            # 获取宗门信息（暂时使用默认值）
            sect_name = "无宗门"
            position_name = "散修"
            
            # 格式化输出
            message = PlayerFormatter.format_player_info(
                player,
                level_name,
                required_exp,
                combat_power,
                sect_name,
                position_name
            )
            
            yield event.plain_result(message)
            
        except Exception as e:
            yield event.plain_result(f"❌ 查看信息失败：{str(e)}")
    
    @require_player
    async def handle_check_in(self, event: AstrMessageEvent, player):
        """
        处理签到命令
        
        Args:
            event: 消息事件
            player: 玩家对象（由装饰器注入）
        """
        try:
            # 执行签到
            reward_gold = self.player_service.check_in(player)
            
            # 格式化输出
            message = PlayerFormatter.format_check_in_success(
                reward_gold,
                player.gold
            )
            
            yield event.plain_result(message)
            
        except ValueError as e:
            yield event.plain_result(f"❌ {str(e)}\n请明日再来。")
        except Exception as e:
            yield event.plain_result(f"❌ 签到失败：{str(e)}")
    
    @require_player
    async def handle_change_nickname(
        self,
        event: AstrMessageEvent,
        player,
        new_nickname: str = ""
    ):
        """
        处理改道号命令
        
        Args:
            event: 消息事件
            player: 玩家对象（由装饰器注入）
            new_nickname: 新道号
        """
        if not new_nickname or new_nickname.strip() == "":
            yield event.plain_result(
                "❌ 请提供新道号\n"
                "💡 使用方法：改道号 新的道号"
            )
            return
        
        try:
            # 修改道号
            self.player_service.change_nickname(player, new_nickname)
            
            # 格式化输出
            message = PlayerFormatter.format_nickname_changed(new_nickname)
            
            yield event.plain_result(message)
            
        except InvalidParameterException as e:
            yield event.plain_result(f"❌ {e.message}")
        except Exception as e:
            yield event.plain_result(f"❌ 修改道号失败：{str(e)}")
    
    @require_player
    async def handle_change_name(
        self,
        event: AstrMessageEvent,
        player,
        new_name: str = ""
    ):
        """
        处理改名命令
        
        Args:
            event: 消息事件
            player: 玩家对象（由装饰器注入）
            new_name: 新名字
        """
        if not new_name or new_name.strip() == "":
            yield event.plain_result(
                "❌ 请提供新名字\n"
                "💡 使用方法：改名 新的名字"
            )
            return
        
        try:
            # 修改名字
            self.player_service.change_name(player, new_name)
            
            # 格式化输出
            message = f"✅ 改名成功！\n你的新名字是：{new_name}"
            
            yield event.plain_result(message)
            
        except InvalidParameterException as e:
            yield event.plain_result(f"❌ {e.message}")
        except Exception as e:
            yield event.plain_result(f"❌ 改名失败：{str(e)}")

    async def handle_rebirth(
        self,
        event: AstrMessageEvent,
        confirm_text: str = ""
    ):
        """
        处理弃道重修命令
        
        Args:
            event: 消息事件
            confirm_text: 确认文本（必须为"确认"才执行）
        """
        import time
        from ...core.exceptions import BusinessException
        
        user_id = event.get_sender_id()
        
        # 检查玩家是否存在
        player = self.player_service.get_player(user_id)
        if not player:
            yield event.plain_result(
                "❌ 你还未踏入修仙之路！\n"
                "💡 发送「我要修仙」开始你的修仙之旅"
            )
            return
        
        # 检查7天冷却
        current_time = int(time.time())
        cooldown_key = f"rebirth_cooldown_{user_id}"
        
        # 从系统配置获取上次重修时间
        config_repo = None
        try:
            # 使用注入的容器获取仓储
            if self.container:
                from ...infrastructure.repositories.system_config_repo import SystemConfigRepository
                config_repo = SystemConfigRepository(self.container.json_storage())
            
            last_rebirth_str = config_repo.get_config(cooldown_key) if config_repo else None
            if last_rebirth_str:
                last_rebirth_time = int(last_rebirth_str)
                cooldown_seconds = 7 * 24 * 3600  # 7天
                
                if current_time - last_rebirth_time < cooldown_seconds:
                    remaining = cooldown_seconds - (current_time - last_rebirth_time)
                    remaining_days = remaining // 86400
                    remaining_hours = (remaining % 86400) // 3600
                    
                    yield event.plain_result(
                        f"❌ 弃道重修冷却中！\n"
                        f"还需等待：{remaining_days}天{remaining_hours}小时"
                    )
                    return
        except Exception as e:
            # 如果获取配置失败，允许继续（可能是首次使用）
            pass
        
        # 检查玩家状态
        if player.state != "idle":
            yield event.plain_result(
                "❌ 你当前正在进行其他活动，无法弃道重修！\n"
                "请先完成当前活动（闭关/历练/秘境等）"
            )
            return
        
        # 检查是否有贷款
        try:
            # 使用注入的容器获取仓储
            bank_repo = None
            if self.container:
                from ...infrastructure.repositories.bank_repo import BankRepository
                bank_repo = BankRepository(self.container.json_storage())
            
            active_loans = bank_repo.get_active_loans(user_id) if bank_repo else []
            if active_loans:
                yield event.plain_result(
                    "❌ 你还有未还清的贷款，无法弃道重修！\n"
                    "请先使用「还款」命令还清所有贷款"
                )
                return
        except Exception:
            # 如果检查失败，允许继续
            pass
        
        # 如果没有提供确认文本，显示警告
        if not confirm_text or confirm_text.strip() != "确认":
            yield event.plain_result(
                "⚠️ 弃道重修将删除当前角色的所有数据，并无法撤回！\n"
                "限制：每7天只能重修一次，且必须在空闲状态、无贷款时使用。\n"
                "━━━━━━━━━━━━━━━\n"
                "若你已做好准备，请发送：\n"
                "弃道重修 确认"
            )
            return
        
        # 执行删除
        try:
            self.player_service.delete_player(user_id)
            
            # 记录重修时间
            try:
                if config_repo:
                    config_repo.set_config(cooldown_key, str(current_time))
            except Exception:
                pass
            
            yield event.plain_result(
                "💀 你选择了弃道重修，旧生一切化为尘埃。\n"
                "━━━━━━━━━━━━━━━\n"
                "可立即使用「我要修仙」重新踏上仙途。\n"
                "（7天内不可再次重修）"
            )
            
        except Exception as e:
            yield event.plain_result(f"❌ 弃道重修失败：{str(e)}")
