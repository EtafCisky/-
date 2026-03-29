"""储物戒业务服务"""
import json
from typing import Tuple, Dict, List, Optional
from pathlib import Path

from ...core.config import ConfigManager
from ...core.exceptions import XiuxianException
from ...infrastructure.repositories.storage_ring_repo import StorageRingRepository
from ...infrastructure.repositories.player_repo import PlayerRepository
from ...domain.models.item import StorageRing


class StorageRingService:
    """储物戒业务服务"""
    
    # 物品分类定义
    ITEM_CATEGORIES = {
        "材料": ["灵草", "精铁", "玄铁", "星辰石", "灵石碎片", "灵兽毛皮", "灵兽内丹",
                 "妖兽精血", "功法残页", "秘境精华", "天材地宝", "混沌精华", "神兽之骨",
                 "远古秘籍", "仙器碎片"],
        "装备": ["武器", "防具", "法器"],
        "功法": ["心法", "技能"],
        "其他": []
    }
    
    def __init__(
        self,
        storage_ring_repo: StorageRingRepository,
        player_repo: PlayerRepository,
        config_manager: ConfigManager
    ):
        self.storage_ring_repo = storage_ring_repo
        self.player_repo = player_repo
        self.config_manager = config_manager
        
        # 加载储物戒配置
        self._load_storage_rings()
    
    def _load_storage_rings(self) -> None:
        """加载储物戒配置"""
        config_path = self.config_manager.config_dir / "storage_rings.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.storage_rings = json.load(f)
        else:
            # 默认配置
            self.storage_rings = {
                "基础储物戒": {
                    "name": "基础储物戒",
                    "type": "storage_ring",
                    "rank": "凡品",
                    "description": "修士入门必备的储物法器，空间狭小但足够存放常用物品。",
                    "capacity": 20,
                    "required_level_index": 0,
                    "price": 0
                }
            }
    
    def get_storage_ring_config(self, ring_name: str) -> Optional[Dict]:
        """获取储物戒配置"""
        return self.storage_rings.get(ring_name)
    
    def get_ring_capacity(self, ring_name: str) -> int:
        """获取储物戒容量"""
        config = self.get_storage_ring_config(ring_name)
        return config.get("capacity", 20) if config else 20
    
    def get_used_slots(self, user_id: str) -> int:
        """获取已使用的格子数（每种物品占1格）"""
        items = self.storage_ring_repo.get_storage_ring_items(user_id)
        return len(items)
    
    def get_available_slots(self, user_id: str) -> int:
        """获取可用的格子数"""
        ring_name = self.storage_ring_repo.get_storage_ring_name(user_id)
        capacity = self.get_ring_capacity(ring_name)
        used = self.get_used_slots(user_id)
        return capacity - used
    
    def get_space_warning(self, user_id: str) -> Optional[str]:
        """获取储物戒空间警告"""
        available = self.get_available_slots(user_id)
        ring_name = self.storage_ring_repo.get_storage_ring_name(user_id)
        capacity = self.get_ring_capacity(ring_name)
        used = self.get_used_slots(user_id)
        
        if available == 0:
            return f"⚠️ 储物戒已满！({used}/{capacity}格)"
        elif available <= 2:
            return f"⚠️ 储物戒空间不足！仅剩{available}格({used}/{capacity}格)"
        return None
    
    def can_store_item(self, item_name: str) -> Tuple[bool, str]:
        """检查物品是否可以存入储物戒"""
        # 检查是否为储物戒
        if item_name in self.storage_rings:
            return False, f"【{item_name}】是储物戒，不能存入另一个储物戒"
        
        return True, ""
    
    def _is_pill(self, item_name: str) -> bool:
        """检查是否为丹药（已废弃，现在丹药也可以存入储物戒）"""
        # 简单检查：包含"丹"字的物品
        return "丹" in item_name
    
    async def store_item(
        self,
        user_id: str,
        item_name: str,
        count: int = 1,
        silent: bool = False
    ) -> Tuple[bool, str]:
        """存入物品到储物戒"""
        # 检查是否可以存入
        can_store, reason = self.can_store_item(item_name)
        if not can_store:
            return False, reason
        
        # 获取当前物品
        items = self.storage_ring_repo.get_storage_ring_items(user_id)
        
        # 检查是否需要新格子
        if item_name not in items:
            available = self.get_available_slots(user_id)
            if available <= 0:
                ring_name = self.storage_ring_repo.get_storage_ring_name(user_id)
                capacity = self.get_ring_capacity(ring_name)
                return False, f"储物戒已满！({capacity}/{capacity}格)"
        
        # 添加物品
        items[item_name] = items.get(item_name, 0) + count
        self.storage_ring_repo.set_storage_ring_items(user_id, items)
        
        if silent:
            return True, ""
        
        # 生成消息
        ring_name = self.storage_ring_repo.get_storage_ring_name(user_id)
        capacity = self.get_ring_capacity(ring_name)
        used = self.get_used_slots(user_id)
        
        msg = f"已将【{item_name}】x{count} 存入储物戒（{used}/{capacity}格）"
        
        warning = self.get_space_warning(user_id)
        if warning:
            msg += f"\n{warning}"
        
        return True, msg
    
    async def retrieve_item(
        self,
        user_id: str,
        item_name: str,
        count: int = 1
    ) -> Tuple[bool, str]:
        """从储物戒取出物品（内部方法，仅供赠予系统使用）
        
        警告：此方法会直接删除物品而不放到任何地方！
        不要在用户命令中直接调用此方法。
        """
        items = self.storage_ring_repo.get_storage_ring_items(user_id)
        
        if item_name not in items:
            return False, f"储物戒中没有【{item_name}】"
        
        current_count = items[item_name]
        if count > current_count:
            return False, f"储物戒中【{item_name}】数量不足（当前：{current_count}个）"
        
        # 减少数量
        if count >= current_count:
            del items[item_name]
        else:
            items[item_name] = current_count - count
        
        self.storage_ring_repo.set_storage_ring_items(user_id, items)
        
        ring_name = self.storage_ring_repo.get_storage_ring_name(user_id)
        capacity = self.get_ring_capacity(ring_name)
        used = self.get_used_slots(user_id)
        
        return True, f"已从储物戒取出【{item_name}】x{count}（{used}/{capacity}格）"
    
    async def discard_item(
        self,
        user_id: str,
        item_name: str,
        count: int = 1
    ) -> Tuple[bool, str]:
        """丢弃储物戒中的物品"""
        items = self.storage_ring_repo.get_storage_ring_items(user_id)
        
        if item_name not in items:
            return False, f"储物戒中没有【{item_name}】"
        
        current_count = items[item_name]
        if count > current_count:
            return False, f"储物戒中【{item_name}】数量不足（当前：{current_count}个）"
        
        # 减少数量
        if count >= current_count:
            del items[item_name]
            discard_count = current_count
        else:
            items[item_name] = current_count - count
            discard_count = count
        
        self.storage_ring_repo.set_storage_ring_items(user_id, items)
        
        ring_name = self.storage_ring_repo.get_storage_ring_name(user_id)
        capacity = self.get_ring_capacity(ring_name)
        used = self.get_used_slots(user_id)
        
        return True, f"已丢弃【{item_name}】x{discard_count}（{used}/{capacity}格）"
    
    def get_item_count(self, user_id: str, item_name: str) -> int:
        """获取物品数量"""
        items = self.storage_ring_repo.get_storage_ring_items(user_id)
        return items.get(item_name, 0)
    
    def has_item(self, user_id: str, item_name: str, count: int = 1) -> bool:
        """检查是否有足够数量的物品"""
        return self.get_item_count(user_id, item_name) >= count
    
    def get_storage_ring_info(self, user_id: str) -> Dict:
        """获取储物戒完整信息"""
        ring_name = self.storage_ring_repo.get_storage_ring_name(user_id)
        ring_config = self.get_storage_ring_config(ring_name) or {}
        items = self.storage_ring_repo.get_storage_ring_items(user_id)
        capacity = self.get_ring_capacity(ring_name)
        used = self.get_used_slots(user_id)
        
        return {
            "name": ring_name,
            "rank": ring_config.get("rank", "未知"),
            "description": ring_config.get("description", ""),
            "capacity": capacity,
            "used": used,
            "available": capacity - used,
            "items": items
        }
    
    def categorize_items(self, items: Dict[str, int]) -> Dict[str, List[Tuple[str, int]]]:
        """将物品按分类整理"""
        result = {cat: [] for cat in self.ITEM_CATEGORIES.keys()}
        
        for item_name, count in items.items():
            categorized = False
            for category, keywords in self.ITEM_CATEGORIES.items():
                if category == "其他":
                    continue
                # 检查物品名是否包含分类关键词
                for keyword in keywords:
                    if keyword in item_name or item_name in keyword:
                        result[category].append((item_name, count))
                        categorized = True
                        break
                if categorized:
                    break
            
            # 未分类的放入"其他"
            if not categorized:
                result["其他"].append((item_name, count))
        
        # 移除空分类
        return {k: v for k, v in result.items() if v}
    
    async def upgrade_ring(
        self,
        user_id: str,
        new_ring_name: str
    ) -> Tuple[bool, str]:
        """升级储物戒"""
        # 检查储物戒是否存在
        ring_config = self.get_storage_ring_config(new_ring_name)
        if not ring_config:
            return False, f"未找到储物戒：{new_ring_name}"
        
        if ring_config.get("type") != "storage_ring":
            return False, f"【{new_ring_name}】不是储物戒类型的物品"
        
        # 获取玩家信息
        player = await self.player_repo.get_by_id(user_id)
        if not player:
            return False, "玩家不存在"
        
        # 检查境界要求
        required_level = ring_config.get("required_level_index", 0)
        if player.level_index < required_level:
            level_name = self._format_required_level(required_level)
            return False, f"境界不足！【{new_ring_name}】（{ring_config.get('rank', '')}）需要达到【{level_name}】以上"
        
        # 检查是否为升级
        old_ring = self.storage_ring_repo.get_storage_ring_name(user_id)
        old_capacity = self.get_ring_capacity(old_ring)
        new_capacity = ring_config.get("capacity", 20)
        
        if new_capacity <= old_capacity:
            return False, f"【{new_ring_name}】容量（{new_capacity}格）不高于当前储物戒（{old_capacity}格），无法替换"
        
        # 检查价格
        price = ring_config.get("price", 0)
        if price > 0:
            if player.gold < price:
                return False, (
                    f"❌ 灵石不足！\n"
                    f"【{new_ring_name}】需要 {price:,} 灵石\n"
                    f"你当前拥有：{player.gold:,} 灵石"
                )
            player.gold -= price
            await self.player_repo.save(player)
        
        # 升级储物戒
        self.storage_ring_repo.set_storage_ring_name(user_id, new_ring_name)
        
        cost_msg = f"\n消耗灵石：{price:,}" if price > 0 else ""
        return True, (
            f"储物戒升级成功！\n"
            f"【{old_ring}】({old_capacity}格) → 【{new_ring_name}】({new_capacity}格)\n"
            f"品级：{ring_config.get('rank', '未知')}{cost_msg}"
        )
    
    def _format_required_level(self, level_index: int) -> str:
        """格式化需求境界名称"""
        level_data = self.config_manager.get_level_data(level_index)
        if level_data:
            return level_data.get("level_name", f"境界{level_index}")
        return f"境界{level_index}"
    
    def get_all_storage_rings(self) -> List[Dict]:
        """获取所有可用的储物戒列表"""
        rings = []
        for name, config in self.storage_rings.items():
            rings.append({
                "name": name,
                "rank": config.get("rank", ""),
                "capacity": config.get("capacity", 20),
                "required_level_index": config.get("required_level_index", 0),
                "price": config.get("price", 0),
                "description": config.get("description", "")
            })
        rings.sort(key=lambda x: x["capacity"])
        return rings
    
    # ===== 赠予系统 =====
    
    async def gift_item(
        self,
        sender_id: str,
        sender_name: str,
        receiver_id: str,
        item_name: str,
        count: int
    ) -> Tuple[bool, str]:
        """赠予物品"""
        # 检查物品是否存在
        if not self.has_item(sender_id, item_name, count):
            current = self.get_item_count(sender_id, item_name)
            if current == 0:
                return False, f"储物戒中没有【{item_name}】"
            else:
                return False, f"储物戒中【{item_name}】数量不足（当前：{current}个）"
        
        # 检查接收者是否存在
        receiver = await self.player_repo.get_by_id(receiver_id)
        if not receiver:
            return False, f"目标玩家（ID:{receiver_id}）尚未开始修仙"
        
        if sender_id == receiver_id:
            return False, "不能赠予物品给自己"
        
        # 从储物戒中取出物品
        success, _ = await self.retrieve_item(sender_id, item_name, count)
        if not success:
            return False, "赠予失败：无法取出物品"
        
        # 创建待处理赠予
        self.storage_ring_repo.create_pending_gift(
            receiver_id=receiver_id,
            sender_id=sender_id,
            sender_name=sender_name,
            item_name=item_name,
            count=count,
            expires_hours=24
        )
        
        return True, (
            f"📦 赠予请求已发送！\n"
            f"【{item_name}】x{count} → @{receiver_id}\n"
            f"等待对方确认...（24小时内有效）\n"
            f"对方可使用 接收 或 拒绝 命令"
        )
    
    async def accept_gift(self, receiver_id: str) -> Tuple[bool, str]:
        """接收赠予"""
        gift = self.storage_ring_repo.get_pending_gift(receiver_id)
        if not gift:
            return False, "你没有待接收的赠予物品"
        
        item_name = gift["item_name"]
        count = gift["count"]
        sender_name = gift["sender_name"]
        sender_id = gift["sender_id"]
        gift_id = gift["id"]
        
        # 尝试存入接收者的储物戒
        success, message = await self.store_item(receiver_id, item_name, count)
        
        if success:
            # 删除赠予记录
            self.storage_ring_repo.delete_pending_gift(gift_id)
            return True, (
                f"✅ 已接收来自【{sender_name}】的赠予！\n"
                f"获得：【{item_name}】x{count}"
            )
        else:
            # 存入失败，物品返还给发送者
            await self.store_item(sender_id, item_name, count, silent=True)
            self.storage_ring_repo.delete_pending_gift(gift_id)
            return False, (
                f"❌ 接收失败：{message}\n"
                f"物品已返还给【{sender_name}】"
            )
    
    async def reject_gift(self, receiver_id: str) -> Tuple[bool, str]:
        """拒绝赠予"""
        gift = self.storage_ring_repo.get_pending_gift(receiver_id)
        if not gift:
            return False, "你没有待处理的赠予请求"
        
        item_name = gift["item_name"]
        count = gift["count"]
        sender_id = gift["sender_id"]
        sender_name = gift["sender_name"]
        gift_id = gift["id"]
        
        # 物品返还给发送者
        await self.store_item(sender_id, item_name, count, silent=True)
        
        # 删除赠予记录
        self.storage_ring_repo.delete_pending_gift(gift_id)
        
        return True, (
            f"已拒绝来自【{sender_name}】的赠予\n"
            f"【{item_name}】x{count} 已返还"
        )
