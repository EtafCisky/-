"""银行命令处理器"""
import time
from typing import AsyncGenerator
from astrbot.api.event import AstrMessageEvent

from ...application.services.bank_service import BankService
from ...core.exceptions import GameException


class BankHandler:
    """银行命令处理器"""
    
    def __init__(self, bank_service: BankService):
        self.bank_service = bank_service
    
    async def handle_bank_info(self, event: AstrMessageEvent) -> AsyncGenerator:
        """处理查看银行信息命令"""
        try:
            user_id = event.get_sender_id()
            
            # 获取银行信息
            info = self.bank_service.get_bank_info(user_id)
            
            # 获取玩家信息
            from ...infrastructure.repositories.player_repo import PlayerRepository
            from ...core.container import Container
            container = Container()
            player_repo = container.player_repository()
            player = player_repo.get_player(user_id)
            
            msg_lines = [
                "🏦 灵石银行",
                "━━━━━━━━━━━━━━━",
                f"💰 存款余额：{info.balance:,} 灵石",
                f"📈 待领利息：{info.pending_interest:,} 灵石",
                f"📊 日利率：0.1%（复利）",
                "━━━━━━━━━━━━━━━",
                f"💎 持有灵石：{player.gold:,}",
            ]
            
            # 显示贷款信息
            if info.has_loan():
                loan_info = self.bank_service.get_loan_info(user_id)
                if loan_info:
                    loan_type_name = "突破贷款" if loan_info.loan_type == "breakthrough" else "普通贷款"
                    status = "⚠️ 已逾期！" if loan_info.is_overdue else f"剩余 {loan_info.days_remaining} 天"
                    msg_lines.extend([
                        "━━━━━━━━━━━━━━━",
                        f"📋 当前贷款（{loan_type_name}）",
                        f"   本金：{loan_info.principal:,} 灵石",
                        f"   当前利息：{loan_info.current_interest:,} 灵石",
                        f"   应还总额：{loan_info.total_due:,} 灵石",
                        f"   状态：{status}",
                    ])
            
            msg_lines.extend([
                "━━━━━━━━━━━━━━━",
                "💡 指令：",
                "  存灵石 <数量>",
                "  取灵石 <数量>",
                "  领取利息",
                "  贷款 <数量>",
                "  还款",
                "  银行流水",
            ])
            
            yield event.plain_result("\n".join(msg_lines))
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"查询银行信息失败：{e}")
    
    async def handle_deposit(self, event: AstrMessageEvent, amount: str = "") -> AsyncGenerator:
        """处理存款命令"""
        try:
            user_id = event.get_sender_id()
            
            # 解析金额
            if not amount:
                yield event.plain_result("❌ 请输入存款金额，例如：存灵石 10000")
                return
            
            try:
                amount_int = int(amount)
            except ValueError:
                yield event.plain_result("❌ 金额必须是数字")
                return
            
            result = self.bank_service.deposit(user_id, amount_int)
            yield event.plain_result(f"✅ {result}")
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"存款失败：{e}")
    
    async def handle_withdraw(self, event: AstrMessageEvent, amount: str = "") -> AsyncGenerator:
        """处理取款命令"""
        try:
            user_id = event.get_sender_id()
            
            # 解析金额
            if not amount:
                yield event.plain_result("❌ 请输入取款金额，例如：取灵石 10000")
                return
            
            try:
                amount_int = int(amount)
            except ValueError:
                yield event.plain_result("❌ 金额必须是数字")
                return
            
            result = self.bank_service.withdraw(user_id, amount_int)
            yield event.plain_result(f"✅ {result}")
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"取款失败：{e}")
    
    async def handle_claim_interest(self, event: AstrMessageEvent) -> AsyncGenerator:
        """处理领取利息命令"""
        try:
            user_id = event.get_sender_id()
            result = self.bank_service.claim_interest(user_id)
            yield event.plain_result(f"✅ {result}")
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"领取利息失败：{e}")
    
    async def handle_loan(self, event: AstrMessageEvent, amount: str = "") -> AsyncGenerator:
        """处理贷款命令"""
        try:
            user_id = event.get_sender_id()
            
            # 如果没有输入金额，显示帮助
            if not amount:
                yield event.plain_result(
                    "🏦 贷款说明\n"
                    "━━━━━━━━━━━━━━━\n"
                    "📌 普通贷款：\n"
                    "   日利率：0.5%\n"
                    "   期限：7天\n"
                    "   额度：1,000 - 1,000,000 灵石\n"
                    "━━━━━━━━━━━━━━━\n"
                    "💀 逾期后果：被银行追杀致死！\n"
                    "   所有修为和装备将化为虚无\n"
                    "━━━━━━━━━━━━━━━\n"
                    "💡 用法：贷款 <金额>\n"
                    "   例如：贷款 50000"
                )
                return
            
            # 解析金额
            try:
                amount_int = int(amount)
            except ValueError:
                yield event.plain_result("❌ 金额必须是数字")
                return
            
            result = self.bank_service.borrow(user_id, amount_int, "normal")
            yield event.plain_result(result)
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"贷款失败：{e}")
    
    async def handle_repay(self, event: AstrMessageEvent) -> AsyncGenerator:
        """处理还款命令"""
        try:
            user_id = event.get_sender_id()
            result = self.bank_service.repay(user_id)
            yield event.plain_result(result)
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"还款失败：{e}")
    
    async def handle_transactions(self, event: AstrMessageEvent) -> AsyncGenerator:
        """处理查看银行流水命令"""
        try:
            user_id = event.get_sender_id()
            transactions = self.bank_service.get_transactions(user_id, 15)
            
            if not transactions:
                yield event.plain_result("📋 暂无交易记录")
                return
            
            msg_lines = [
                "📋 银行交易流水（最近15条）",
                "━━━━━━━━━━━━━━━",
            ]
            
            type_names = {
                "deposit": "💰 存入",
                "withdraw": "💸 取出",
                "interest": "📈 利息",
                "loan": "📥 贷款",
                "repay": "📤 还款",
                "bank_kill": "💀 追杀",
            }
            
            for trans in transactions:
                trans_time = time.strftime("%m-%d %H:%M", time.localtime(trans.created_at))
                type_name = type_names.get(trans.trans_type, trans.trans_type)
                amount = trans.amount
                amount_str = f"+{amount:,}" if amount > 0 else f"{amount:,}"
                
                msg_lines.append(f"{trans_time} {type_name} {amount_str}")
            
            msg_lines.extend([
                "━━━━━━━━━━━━━━━",
                f"当前余额：{transactions[0].balance_after:,} 灵石" if transactions else ""
            ])
            
            yield event.plain_result("\n".join(msg_lines))
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"查询流水失败：{e}")
    
    async def handle_breakthrough_loan(self, event: AstrMessageEvent, amount: str = "") -> AsyncGenerator:
        """处理突破贷款命令"""
        try:
            user_id = event.get_sender_id()
            
            # 如果没有输入金额，显示帮助
            if not amount:
                yield event.plain_result(
                    "🏦 突破贷款说明\n"
                    "━━━━━━━━━━━━━━━\n"
                    "📌 专为突破准备的短期贷款：\n"
                    "   日利率：0.8%（较高）\n"
                    "   期限：3天（较短）\n"
                    "   额度：1,000 - 1,000,000 灵石\n"
                    "━━━━━━━━━━━━━━━\n"
                    "✨ 突破成功后自动还款\n"
                    "━━━━━━━━━━━━━━━\n"
                    "💀 逾期后果：被银行追杀致死！\n"
                    "   所有修为和装备将化为虚无\n"
                    "━━━━━━━━━━━━━━━\n"
                    "💡 用法：突破贷款 <金额>"
                )
                return
            
            # 解析金额
            try:
                amount_int = int(amount)
            except ValueError:
                yield event.plain_result("❌ 金额必须是数字")
                return
            
            result = self.bank_service.borrow(user_id, amount_int, "breakthrough")
            yield event.plain_result(result)
            
        except GameException as e:
            yield event.plain_result(str(e))
        except Exception as e:
            yield event.plain_result(f"突破贷款失败：{e}")
