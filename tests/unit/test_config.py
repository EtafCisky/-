"""配置管理测试"""
import pytest
from xiuxian_v3.core.config import ConfigManager, Settings


def test_default_config():
    """测试默认配置"""
    config_manager = ConfigManager()
    settings = config_manager.settings
    
    assert isinstance(settings, Settings)
    assert settings.values.initial_gold == 100
    assert settings.values.base_exp_per_minute == 100
    assert settings.values.check_in_gold_min == 50
    assert settings.values.check_in_gold_max == 500


def test_astrbot_config_loading():
    """测试从 AstrBot 配置加载"""
    astrbot_config = {
        "VALUES": {
            "INITIAL_GOLD": 200,
            "BASE_EXP_PER_MINUTE": 150
        },
        "SPIRIT_ROOT_SPEEDS": {
            "HEAVENLY_ROOT_SPEED": 2.0
        }
    }
    
    config_manager = ConfigManager(astrbot_config=astrbot_config)
    settings = config_manager.settings
    
    assert settings.values.initial_gold == 200
    assert settings.values.base_exp_per_minute == 150
    assert settings.spirit_root_speeds.heavenly_root_speed == 2.0


def test_access_control_config():
    """测试访问控制配置"""
    astrbot_config = {
        "ACCESS_CONTROL": {
            "WHITELIST_GROUPS": ["123456", "789012"],
            "SHOP_MANAGERS": ["user1", "user2"]
        }
    }
    
    config_manager = ConfigManager(astrbot_config=astrbot_config)
    settings = config_manager.settings
    
    assert settings.access_control.whitelist_groups == ["123456", "789012"]
    assert settings.access_control.shop_managers == ["user1", "user2"]


def test_spirit_root_weights():
    """测试灵根权重配置"""
    config_manager = ConfigManager()
    settings = config_manager.settings
    
    assert settings.spirit_root_weights.pseudo_root_weight == 1
    assert settings.spirit_root_weights.wuxing_root_weight == 200
    assert settings.spirit_root_weights.divine_body_weight == 1
