"""依赖注入容器"""
from pathlib import Path
from typing import Optional

from .config import ConfigManager


class Container:
    """
    依赖注入容器
    
    管理所有组件的生命周期和依赖关系
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化容器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        
        # 单例组件
        self._config_manager: Optional[ConfigManager] = None
        self._database = None
        
        # 仓储层（每次创建新实例）
        # 将在后续实现
        
        # 服务层（每次创建新实例）
        # 将在后续实现
    
    def config_manager(self) -> ConfigManager:
        """获取配置管理器（单例）"""
        if self._config_manager is None:
            config_dir = None
            if self.data_dir:
                config_dir = self.data_dir.parent / "config"
            self._config_manager = ConfigManager(config_dir)
        return self._config_manager
    
    def database(self):
        """获取数据库连接（单例）"""
        if self._database is None:
            from ..infrastructure.database.connection import DatabaseConnection
            db_path = self.data_dir / "xiuxian_v3.db" if self.data_dir else "xiuxian_v3.db"
            self._database = DatabaseConnection(str(db_path), echo=False)
        return self._database
    
    # 仓储层工厂方法
    def player_repository(self):
        """获取玩家仓储"""
        from ..infrastructure.repositories.player_repo import PlayerRepository
        session = self.database().create_session()
        return PlayerRepository(session)
    
    def combat_repository(self):
        """获取战斗仓储"""
        from ..infrastructure.repositories.combat_repo import CombatRepository
        session = self.database().create_session()
        return CombatRepository(session)
    
    def storage_ring_repository(self):
        """获取储物戒仓储"""
        from ..infrastructure.repositories.storage_ring_repo import StorageRingRepository
        session = self.database().create_session()
        return StorageRingRepository(session)
    
    def equipment_repository(self):
        """获取装备仓储"""
        from ..infrastructure.repositories.equipment_repo import EquipmentRepository
        session = self.database().create_session()
        config_dir = self.data_dir.parent / "config" if self.data_dir else Path("config")
        return EquipmentRepository(session, config_dir)
    
    def shop_repository(self):
        """获取商店仓储"""
        from ..infrastructure.repositories.shop_repo import ShopRepository
        session = self.database().create_session()
        return ShopRepository(session)
    
    def sect_repository(self):
        """获取宗门仓储"""
        from ..infrastructure.repositories.sect_repo import SectRepository
        session = self.database().create_session()
        return SectRepository(session)
    
    def rift_repository(self):
        """获取秘境仓储"""
        from ..infrastructure.repositories.rift_repo import RiftRepository
        session = self.database().create_session()
        return RiftRepository(session)
    
    def boss_repository(self):
        """获取Boss仓储"""
        from ..infrastructure.repositories.boss_repo import BossRepository
        session = self.database().create_session()
        return BossRepository(session)
    
    def bounty_repository(self):
        """获取悬赏仓储"""
        from ..infrastructure.repositories.bounty_repo import BountyRepository
        session = self.database().create_session()
        return BountyRepository(session)
    
    def bank_repository(self):
        """获取银行仓储"""
        from ..infrastructure.repositories.bank_repo import BankRepository
        session = self.database().create_session()
        return BankRepository(session)
    
    def blessed_land_repository(self):
        """获取洞天福地仓储"""
        from ..infrastructure.repositories.blessed_land_repo import BlessedLandRepository
        session = self.database().create_session()
        return BlessedLandRepository(session)
    
    def spirit_farm_repository(self):
        """获取灵田仓储"""
        from ..infrastructure.repositories.spirit_farm_repo import SpiritFarmRepository
        session = self.database().create_session()
        return SpiritFarmRepository(session)
    
    def spirit_eye_repository(self):
        """获取天地灵眼仓储"""
        from ..infrastructure.repositories.spirit_eye_repo import SpiritEyeRepository
        session = self.database().create_session()
        return SpiritEyeRepository(session)
    
    def dual_cultivation_repository(self):
        """获取双修仓储"""
        from ..infrastructure.repositories.dual_cultivation_repo import DualCultivationRepository
        session = self.database().create_session()
        return DualCultivationRepository(session)
    
    def impart_repository(self):
        """获取传承仓储"""
        from ..infrastructure.repositories.impart_repo import ImpartRepository
        session = self.database().create_session()
        return ImpartRepository(session)
    
    # 工具类工厂方法
    def spirit_root_generator(self):
        """获取灵根生成器"""
        from ..utils.spirit_root_generator import SpiritRootGenerator
        return SpiritRootGenerator(self.config_manager())
    
    # 服务层工厂方法
    def player_service(self):
        """获取玩家服务"""
        from ..application.services.player_service import PlayerService
        return PlayerService(
            self.player_repository(),
            self.config_manager()
        )
    
    def cultivation_service(self):
        """获取修炼服务"""
        from ..application.services.cultivation_service import CultivationService
        return CultivationService(
            self.player_repository(),
            self.config_manager(),
            self.spirit_root_generator()
        )
    
    def breakthrough_service(self):
        """获取突破服务"""
        from ..application.services.breakthrough_service import BreakthroughService
        return BreakthroughService(
            self.player_repository(),
            self.config_manager()
        )
    
    def combat_service(self):
        """获取战斗服务"""
        from ..application.services.combat_service import CombatService
        return CombatService(
            self.player_repository(),
            self.combat_repository(),
            self.config_manager()
        )
    
    def storage_ring_service(self):
        """获取储物戒服务"""
        from ..application.services.storage_ring_service import StorageRingService
        return StorageRingService(
            self.storage_ring_repository(),
            self.player_repository(),
            self.config_manager()
        )
    
    def equipment_service(self):
        """获取装备服务"""
        from ..application.services.equipment_service import EquipmentService
        return EquipmentService(
            self.equipment_repository(),
            self.player_repository(),
            self.storage_ring_repository()
        )
    
    def pill_service(self):
        """获取丹药服务"""
        from ..application.services.pill_service import PillService
        return PillService(
            self.player_repository(),
            self.config_manager()
        )
    
    def alchemy_service(self):
        """获取炼丹服务"""
        from ..application.services.alchemy_service import AlchemyService
        return AlchemyService(
            self.player_repository(),
            self.storage_ring_repository(),
            self.config_manager()
        )
    
    def shop_service(self):
        """获取商店服务"""
        from ..application.services.shop_service import ShopService
        return ShopService(
            self.shop_repository(),
            self.player_repository(),
            self.storage_ring_repository(),
            self.config_manager()
        )
    
    def sect_service(self):
        """获取宗门服务"""
        from ..application.services.sect_service import SectService
        return SectService(
            self.sect_repository(),
            self.player_repository(),
            self.config_manager()
        )
    
    def adventure_service(self):
        """获取历练服务"""
        from ..application.services.adventure_service import AdventureService
        return AdventureService(
            self.player_repository(),
            self.storage_ring_repository(),
            self.config_manager()
        )
    
    def rift_service(self):
        """获取秘境服务"""
        from ..application.services.rift_service import RiftService
        return RiftService(
            self.player_repository(),
            self.rift_repository(),
            self.storage_ring_repository(),
            self.config_manager()
        )
    
    def boss_service(self):
        """获取Boss服务"""
        from ..application.services.boss_service import BossService
        return BossService(
            self.player_repository(),
            self.boss_repository(),
            self.storage_ring_repository(),
            self.config_manager()
        )
    
    def bounty_service(self):
        """获取悬赏服务"""
        from ..application.services.bounty_service import BountyService
        return BountyService(
            self.player_repository(),
            self.bounty_repository(),
            self.storage_ring_repository(),
            self.config_manager()
        )
    
    def bank_service(self):
        """获取银行服务"""
        from ..application.services.bank_service import BankService
        return BankService(
            self.player_repository(),
            self.bank_repository(),
            self.config_manager()
        )
    
    def blessed_land_service(self):
        """获取洞天福地服务"""
        from ..application.services.blessed_land_service import BlessedLandService
        return BlessedLandService(
            self.player_repository(),
            self.blessed_land_repository(),
            self.config_manager()
        )
    
    def spirit_farm_service(self):
        """获取灵田服务"""
        from ..application.services.spirit_farm_service import SpiritFarmService
        return SpiritFarmService(
            self.player_repository(),
            self.spirit_farm_repository(),
            self.storage_ring_repository(),
            self.config_manager()
        )
    
    def spirit_eye_service(self):
        """获取天地灵眼服务"""
        from ..application.services.spirit_eye_service import SpiritEyeService
        return SpiritEyeService(
            self.player_repository(),
            self.spirit_eye_repository(),
            self.config_manager()
        )
    
    def dual_cultivation_service(self):
        """获取双修服务"""
        from ..application.services.dual_cultivation_service import DualCultivationService
        return DualCultivationService(
            self.dual_cultivation_repository(),
            self.player_repository()
        )
    
    def impart_service(self):
        """获取传承服务"""
        from ..application.services.impart_service import ImpartService
        return ImpartService(
            self.impart_repository(),
            self.player_repository(),
            self.config_manager()
        )
    
    def ranking_service(self):
        """获取排行榜服务"""
        from ..application.services.ranking_service import RankingService
        return RankingService(
            self.player_repository(),
            self.sect_repository(),
            self.bank_repository(),
            self.config_manager()
        )
    
    def cleanup(self):
        """清理资源"""
        if self._database:
            # 关闭数据库连接
            pass
