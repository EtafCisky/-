"""双修系统服务"""
import time
from typing import Tuple

from ...infrastructure.repositories.dual_cultivation_repo import DualCultivationRepository
from ...infrastructure.repositories.player_repo import PlayerRepository
from ...core.exceptions import GameException
from ...domain.enums import PlayerState


# 双修配置
DUAL_CULT_COOLDOWN = 3600  # 1小时冷却
DUAL_CULT_EXP_BONUS = 0.1  # 10%修为互增
DUAL_CULT_REQUEST_EXPIRE = 300  # 请求过期时间（5分钟）
DUAL_CULT_MAX_EXP_RATIO = 3.0  # 双修双方修为差距最大3倍


class DualCultivationService:
    """双修服务"""
    
    def __init__(
        self,
        dual_repo: DualCultivationRepository,
        player_repo: PlayerRepository
    ):
        self.dual_repo = dual_repo
        self.player_repo = player_repo
    
    def send_request(self, initiator_id: str, target_id: str) -> Tuple[bool, str]:
        """发起双修请求"""
        if initiator_id == target_id:
            return False, "❌ 不能与自己双修。"
        
        # 获取发起者
        initiator = self.player_repo.get_player(initiator_id)
        if not initiator:
            return False, "❌ 你还未踏入修仙之路！"
        
        # 检查发起者状态
        if initiator.state != PlayerState.IDLE:
            return False, f"❌ 你当前正{initiator.state.value}，无法发起双修！"
        
        # 检查目标是否存在
        target = self.player_repo.get_player(target_id)
        if not target:
            return False, "❌ 对方还未踏入修仙之路。"
        
        # 检查修为差距
        exp_ratio = max(initiator.experience, target.experience) / max(min(initiator.experience, target.experience), 1)
        if exp_ratio > DUAL_CULT_MAX_EXP_RATIO:
            return False, f"❌ 双方修为差距过大（最大{DUAL_CULT_MAX_EXP_RATIO}倍），无法双修。"
        
        # 检查目标状态
        if target.state != PlayerState.IDLE:
            return False, "❌ 对方正忙，无法接受双修请求。"
        
        # 检查发起者冷却
        now = int(time.time())
        initiator_cooldown = self.dual_repo.get_cooldown(initiator_id)
        if initiator_cooldown and (now - initiator_cooldown.last_dual_time) < DUAL_CULT_COOLDOWN:
            remaining = DUAL_CULT_COOLDOWN - (now - initiator_cooldown.last_dual_time)
            return False, f"❌ 双修冷却中，还需 {remaining // 60} 分钟。"
        
        # 检查目标冷却
        target_cooldown = self.dual_repo.get_cooldown(target_id)
        if target_cooldown and (now - target_cooldown.last_dual_time) < DUAL_CULT_COOLDOWN:
            remaining = DUAL_CULT_COOLDOWN - (now - target_cooldown.last_dual_time)
            return False, f"❌ 对方正在双修冷却，还需 {remaining // 60} 分钟。"
        
        # 创建请求
        expires_at = now + DUAL_CULT_REQUEST_EXPIRE
        self.dual_repo.create_request(
            initiator_id,
            initiator.nickname or initiator_id[:8],
            target_id,
            expires_at
        )
        
        return True, (
            f"💕 已向【{target.nickname or target_id[:8]}】发起双修请求！\n"
            f"对方使用 /接受双修 或 /拒绝双修 响应。\n"
            f"请求将在5分钟后过期。"
        )
    
    def accept_request(self, acceptor_id: str) -> Tuple[bool, str]:
        """接受双修请求"""
        # 获取待处理请求
        request = self.dual_repo.get_pending_request(acceptor_id)
        if not request:
            return False, "❌ 没有待处理的双修请求。"
        
        # 获取双方玩家
        acceptor = self.player_repo.get_player(acceptor_id)
        initiator = self.player_repo.get_player(request.from_id)
        
        if not acceptor or not initiator:
            self.dual_repo.delete_request(request.id)
            return False, "❌ 请求发起者数据异常。"
        
        # 再次检查修为差距
        exp_ratio = max(initiator.experience, acceptor.experience) / max(min(initiator.experience, acceptor.experience), 1)
        if exp_ratio > DUAL_CULT_MAX_EXP_RATIO:
            self.dual_repo.delete_request(request.id)
            return False, f"❌ 双方修为差距已超过限制，双修取消。"
        
        # 检查双方冷却
        now = int(time.time())
        acceptor_cooldown = self.dual_repo.get_cooldown(acceptor_id)
        if acceptor_cooldown and (now - acceptor_cooldown.last_dual_time) < DUAL_CULT_COOLDOWN:
            self.dual_repo.delete_request(request.id)
            remaining = DUAL_CULT_COOLDOWN - (now - acceptor_cooldown.last_dual_time)
            return False, f"❌ 你的双修冷却中，还需 {remaining // 60} 分钟。"
        
        initiator_cooldown = self.dual_repo.get_cooldown(request.from_id)
        if initiator_cooldown and (now - initiator_cooldown.last_dual_time) < DUAL_CULT_COOLDOWN:
            self.dual_repo.delete_request(request.id)
            remaining = DUAL_CULT_COOLDOWN - (now - initiator_cooldown.last_dual_time)
            return False, f"❌ 对方仍在双修冷却，还需 {remaining // 60} 分钟。"
        
        # 计算双修收益
        init_exp_gain = int(acceptor.experience * DUAL_CULT_EXP_BONUS)
        accept_exp_gain = int(initiator.experience * DUAL_CULT_EXP_BONUS)
        
        # 应用收益
        initiator.experience += init_exp_gain
        acceptor.experience += accept_exp_gain
        self.player_repo.update_player(initiator)
        self.player_repo.update_player(acceptor)
        
        # 记录冷却
        self.dual_repo.set_cooldown(initiator.user_id, now)
        self.dual_repo.set_cooldown(acceptor.user_id, now)
        
        # 清除请求
        self.dual_repo.delete_request(request.id)
        
        return True, (
            f"💕 双修成功！\n"
            f"━━━━━━━━━━━━━━━\n"
            f"与【{request.from_name}】双修\n"
            f"{request.from_name} 获得修为：+{init_exp_gain:,}\n"
            f"你 获得修为：+{accept_exp_gain:,}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"下次双修：1小时后"
        )
    
    def reject_request(self, rejecter_id: str) -> Tuple[bool, str]:
        """拒绝双修请求"""
        request = self.dual_repo.get_pending_request(rejecter_id)
        if not request:
            return False, "❌ 没有待处理的双修请求。"
        
        from_name = request.from_name
        self.dual_repo.delete_request(request.id)
        
        return True, f"已拒绝【{from_name}】的双修请求。"
