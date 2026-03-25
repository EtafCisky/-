"""输出格式化工具"""
from typing import Dict, Any

from ..domain.models.player import Player
from ..domain.enums import CultivationType
from ..domain.value_objects import SpiritRootInfo


class PlayerFormatter:
    """玩家信息格式化器"""
    
    @staticmethod
    def format_create_success(
        player: Player,
        spirit_root_info: SpiritRootInfo,
        sender_name: str
    ) -> str:
        """
        格式化创建角色成功消息
        
        Args:
            player: 玩家对象
            spirit_root_info: 灵根信息
            sender_name: 发送者名称
            
        Returns:
            格式化的消息
        """
        return (
            f"🎉 恭喜道友 {sender_name} 踏上仙途！\n"
            f"━━━━━━━━━━━━━━━\n"
            f"修炼方式：【{player.cultivation_type.value}】\n"
            f"灵根：【{player.spiritual_root}】\n"
            f"评价：{spirit_root_info.description}\n"
            f"启动资金：{player.gold} 灵石\n"
            f"━━━━━━━━━━━━━━━\n"
            f"⚠️ 修仙有风险，突破需谨慎！\n"
            f"突破失败或生命值归零会导致\n"
            f"身死道消，所有数据清除！\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 发送「我的信息」查看状态"
        )
    
    @staticmethod
    def format_create_help() -> str:
        """格式化创建角色帮助消息"""
        return (
            "🌟 欢迎踏入修仙之路！\n"
            "━━━━━━━━━━━━━━━\n"
            "请选择你的修炼方式：\n\n"
            "【灵修】以灵气为主，法术攻击\n"
            "• 寿命：100\n"
            "• 灵气：100-1000\n"
            "• 法伤：5-100\n"
            "• 物伤：5\n"
            "• 法防：0\n"
            "• 物防：5\n"
            "• 精神力：100-500\n\n"
            "【体修】以气血为主，肉身强横\n"
            "• 寿命：50-100\n"
            "• 气血：100-500\n"
            "• 法伤：0\n"
            "• 物伤：100-500\n"
            "• 法防：50-200\n"
            "• 物防：100-500\n"
            "• 精神力：100-500\n"
            "━━━━━━━━━━━━━━━\n"
            "⚠️ 修仙风险警告 ⚠️\n"
            "• 突破失败有概率走火入魔身死道消\n"
            "• 生命值归零也会导致死亡\n"
            "• 死亡后所有数据清除，需重新入仙途\n"
            "━━━━━━━━━━━━━━━\n"
            f"💡 使用方法：\n"
            f"  我要修仙 灵修\n"
            f"  我要修仙 体修"
        )
    
    @staticmethod
    def format_player_info(
        player: Player,
        level_name: str,
        required_exp: int,
        combat_power: int,
        sect_name: str = "无宗门",
        position_name: str = "散修"
    ) -> str:
        """
        格式化玩家信息
        
        Args:
            player: 玩家对象
            level_name: 境界名称
            required_exp: 突破所需修为
            combat_power: 战力
            sect_name: 宗门名称
            position_name: 职位名称
            
        Returns:
            格式化的消息
        """
        dao_hao = player.user_name if player.user_name else player.nickname
        
        # 突破加成
        breakthrough_rate = f"+{player.level_up_rate}%" if player.level_up_rate > 0 else "0%"
        
        # 装备信息
        weapon_name = player.weapon if player.weapon else "无"
        armor_name = player.armor if player.armor else "无"
        technique_name = player.main_technique if player.main_technique else "无"
        
        msg = (
            f"📋 道友 {dao_hao} 的信息\n"
            f"━━━━━━━━━━━━━━━\n"
            f"\n"
            f"【基本信息】\n"
            f"  道号：{dao_hao}\n"
            f"  境界：{level_name}\n"
            f"  修为：{int(player.experience):,}/{int(required_exp):,}\n"
            f"  灵石：{player.gold:,}\n"
            f"  战力：{combat_power:,}\n"
            f"  灵根：{player.spiritual_root}\n"
            f"  突破加成：{breakthrough_rate}\n"
            f"\n"
            f"【修炼属性】\n"
            f"  修炼方式：{player.cultivation_type.value}\n"
            f"  状态：{player.state.value}\n"
            f"  寿命：{player.lifespan}\n"
            f"  精神力：{player.mental_power}\n"
        )
        
        # 根据修炼类型添加不同属性
        if player.cultivation_type == CultivationType.SPIRITUAL:
            msg += (
                f"  灵气：{player.spiritual_qi}/{player.max_spiritual_qi}\n"
                f"  法伤：{player.magic_damage}\n"
                f"  物伤：{player.physical_damage}\n"
                f"  法防：{player.magic_defense}\n"
                f"  物防：{player.physical_defense}\n"
            )
        else:  # 体修
            msg += (
                f"  气血：{player.blood_qi}/{player.max_blood_qi}\n"
                f"  物伤：{player.physical_damage}\n"
                f"  法伤：{player.magic_damage}\n"
                f"  物防：{player.physical_defense}\n"
                f"  法防：{player.magic_defense}\n"
            )
        
        msg += (
            f"\n"
            f"【装备信息】\n"
            f"  主修功法：{technique_name}\n"
            f"  法器：{weapon_name}\n"
            f"  防具：{armor_name}\n"
            f"\n"
            f"【宗门信息】\n"
            f"  所在宗门：{sect_name}\n"
            f"  宗门职位：{position_name}\n"
            f"━━━━━━━━━━━━━━━"
        )
        
        return msg
    
    @staticmethod
    def format_check_in_success(reward_gold: int, total_gold: int) -> str:
        """
        格式化签到成功消息
        
        Args:
            reward_gold: 获得的灵石
            total_gold: 当前总灵石
            
        Returns:
            格式化的消息
        """
        return (
            "✅ 签到成功！\n"
            "━━━━━━━━━━━━━━━\n"
            f"💰 获得灵石：{reward_gold}\n"
            f"💎 当前灵石：{total_gold}\n"
            "━━━━━━━━━━━━━━━\n"
            "明日再来，莫要忘记哦~"
        )
    
    @staticmethod
    def format_nickname_changed(new_nickname: str) -> str:
        """
        格式化改道号成功消息
        
        Args:
            new_nickname: 新道号
            
        Returns:
            格式化的消息
        """
        return (
            "✅ 道号修改成功！\n"
            "━━━━━━━━━━━━━━━\n"
            f"新道号：{new_nickname}\n"
            "━━━━━━━━━━━━━━━\n"
            "从此江湖上多了一个响亮的名号！"
        )
