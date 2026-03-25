"""战斗仓储层"""
import time
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete

from ..database.schema import CombatLogTable, CombatCooldownTable
from ...domain.models.combat import CombatCooldown


class CombatRepository:
    """战斗仓储"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_combat_log(
        self,
        attacker_id: str,
        defender_id: Optional[str],
        combat_type: str,
        winner_id: Optional[str],
        combat_log: str,
        gold_reward: int = 0,
        exp_reward: int = 0
    ) -> int:
        """
        保存战斗日志
        
        Args:
            attacker_id: 攻击者ID
            defender_id: 防御者ID（可能是玩家或Boss）
            combat_type: 战斗类型（spar/duel/boss）
            winner_id: 获胜者ID
            combat_log: 战斗日志（JSON字符串）
            gold_reward: 灵石奖励
            exp_reward: 修为奖励
            
        Returns:
            战斗日志ID
        """
        stmt = insert(CombatLogTable).values(
            attacker_id=attacker_id,
            defender_id=defender_id,
            combat_type=combat_type,
            winner_id=winner_id,
            combat_log=combat_log,
            gold_reward=gold_reward,
            exp_reward=exp_reward,
            created_at=int(time.time())
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.lastrowid
    
    async def get_combat_cooldown(self, user_id: str) -> Optional[CombatCooldown]:
        """
        获取战斗冷却信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            战斗冷却信息，如果不存在返回None
        """
        stmt = select(CombatCooldownTable).where(
            CombatCooldownTable.user_id == user_id
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        
        if row is None:
            return None
        
        return CombatCooldown(
            user_id=row.user_id,
            last_duel_time=row.last_duel_time,
            last_spar_time=row.last_spar_time
        )
    
    async def update_duel_cooldown(self, user_id: str, timestamp: int):
        """
        更新决斗冷却时间
        
        Args:
            user_id: 用户ID
            timestamp: 时间戳
        """
        # 尝试插入或更新
        stmt = insert(CombatCooldownTable).values(
            user_id=user_id,
            last_duel_time=timestamp,
            last_spar_time=0
        )
        # SQLite的ON CONFLICT语法
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_={'last_duel_time': timestamp}
        )
        await self.session.execute(stmt)
        await self.session.commit()
    
    async def update_spar_cooldown(self, user_id: str, timestamp: int):
        """
        更新切磋冷却时间
        
        Args:
            user_id: 用户ID
            timestamp: 时间戳
        """
        stmt = insert(CombatCooldownTable).values(
            user_id=user_id,
            last_duel_time=0,
            last_spar_time=timestamp
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_={'last_spar_time': timestamp}
        )
        await self.session.execute(stmt)
        await self.session.commit()
    
    async def get_recent_combat_logs(
        self,
        user_id: str,
        limit: int = 10
    ) -> list[dict]:
        """
        获取最近的战斗日志
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            战斗日志列表
        """
        stmt = select(CombatLogTable).where(
            (CombatLogTable.attacker_id == user_id) |
            (CombatLogTable.defender_id == user_id)
        ).order_by(
            CombatLogTable.created_at.desc()
        ).limit(limit)
        
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        
        logs = []
        for row in rows:
            logs.append({
                'id': row.id,
                'attacker_id': row.attacker_id,
                'defender_id': row.defender_id,
                'combat_type': row.combat_type,
                'winner_id': row.winner_id,
                'combat_log': row.combat_log,
                'gold_reward': row.gold_reward,
                'exp_reward': row.exp_reward,
                'created_at': row.created_at
            })
        
        return logs
