"""传承系统服务"""
import random
from typing import Tuple, Optional, List, Dict

from ...infrastructure.repositories.impart_repo import ImpartRepository
from ...infrastructure.repositories.player_repo import PlayerRepository
from ...domain.models.impart import ImpartInfo
from ...core.config import ConfigManager


class ImpartService:
    """传承服务"""
    
    def __init__(
        self,
        impart_repo: ImpartRepository,
        player_repo: PlayerRepository,
        config_manager: ConfigManager
    ):
        self.impart_repo = impart_repo
        self.player_repo = player_repo
        self.config_manager = config_manager
    
    def get_impart_info(self, user_id: str) -> Tuple[bool, str]:
        """获取传承信息"""
        impart_info = self.impart_repo.get_impart_info(user_id)
        if not impart_info:
            # 自动创建
            impart_info = self.impart_repo.create_impart_info(user_id)
        
        msg = f"""✨ 传承信息
━━━━━━━━━━━━━━━

HP加成：{impart_info.impart_hp_per * 100:.1f}%
MP加成：{impart_info.impart_mp_per * 100:.1f}%
攻击加成：{impart_info.impart_atk_per * 100:.1f}%
会心加成：{impart_info.impart_know_per * 100:.1f}%
爆伤加成：{impart_info.impart_burst_per * 100:.1f}%

混合经验：{impart_info.impart_mix_exp}"""
        
        return True, msg
    
    def challenge_impart(self, attacker_id: str, defender_id: str) -> Tuple[bool, str]:
        """发起传承挑战"""
        if attacker_id == defender_id:
            return False, "❌ 不能挑战自己。"
        
        # 获取双方玩家
        attacker = self.player_repo.get_player(attacker_id)
        defender = self.player_repo.get_player(defender_id)
        
        if not attacker or not defender:
            return False, "❌ 对方还未踏入修仙之路。"
        
        # 获取传承信息
        attacker_impart = self.impart_repo.get_impart_info(attacker_id)
        if not attacker_impart:
            attacker_impart = self.impart_repo.create_impart_info(attacker_id)
        
        defender_impart = self.impart_repo.get_impart_info(defender_id)
        if not defender_impart:
            defender_impart = self.impart_repo.create_impart_info(defender_id)
        
        # 简化战斗计算（基于修为和攻击力）
        atk_power = attacker.physical_damage + attacker.magic_damage
        def_power = defender.physical_damage + defender.magic_damage
        
        # 战斗模拟
        rounds = 0
        max_rounds = 10
        atk_hp = attacker.max_hp
        def_hp = defender.max_hp
        
        while atk_hp > 0 and def_hp > 0 and rounds < max_rounds:
            rounds += 1
            
            # 攻击者出手
            damage = max(1, atk_power - defender.physical_defense // 2)
            damage = int(damage * random.uniform(0.8, 1.2))
            def_hp -= damage
            
            if def_hp <= 0:
                break
            
            # 防守者反击
            counter_damage = max(1, def_power - attacker.physical_defense // 2)
            counter_damage = int(counter_damage * random.uniform(0.8, 1.2))
            atk_hp -= counter_damage
        
        # 判定胜负
        attacker_wins = def_hp <= 0 or (atk_hp > 0 and atk_hp >= def_hp)
        
        if attacker_wins:
            # 胜利奖励：获得传承加成
            impart_gain = random.uniform(0.01, 0.05)  # 1%-5%
            new_atk_per = min(1.0, attacker_impart.impart_atk_per + impart_gain)
            attacker_impart.impart_atk_per = new_atk_per
            self.impart_repo.update_impart_info(attacker_impart)
            
            # 失败惩罚
            if defender_impart.impart_atk_per > 0:
                loss = min(impart_gain / 2, defender_impart.impart_atk_per)
                defender_impart.impart_atk_per -= loss
                self.impart_repo.update_impart_info(defender_impart)
            
            result_msg = (
                f"🎉 传承挑战胜利！\n"
                f"━━━━━━━━━━━━━━━\n"
                f"对手：{defender.nickname or defender_id[:8]}\n"
                f"获得ATK传承：+{impart_gain:.2%}\n"
            )
        else:
            # 失败惩罚：损失修为
            exp_loss = int(attacker.experience * 0.01)  # 1%
            attacker.experience = max(0, attacker.experience - exp_loss)
            self.player_repo.update_player(attacker)
            
            result_msg = (
                f"💀 传承挑战失败...\n"
                f"━━━━━━━━━━━━━━━\n"
                f"对手：{defender.nickname or defender_id[:8]}\n"
                f"损失修为：-{exp_loss:,}\n"
            )
        
        return True, result_msg
    
    def get_ranking(self, limit: int = 10) -> Tuple[bool, str]:
        """获取传承排行榜"""
        rankings = self.impart_repo.get_ranking(limit)
        
        if not rankings:
            return False, "📊 传承排行榜暂无数据。"
        
        lines = ["🏆 传承排行榜\n━━━━━━━━━━━━━━━"]
        for i, (user_id, atk_per, total_per) in enumerate(rankings, 1):
            player = self.player_repo.get_player(user_id)
            name = player.nickname if player and player.nickname else user_id[:8]
            lines.append(f"{i}. {name} - ATK+{atk_per:.1%}")
        lines.append("━━━━━━━━━━━━━━━")
        
        return True, "\n".join(lines)
