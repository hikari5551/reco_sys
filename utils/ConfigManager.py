# 这个文件定义了一个ConfigManager类，提供了获取配置项的接口。当前的实现只是一个占位符，返回一个空字典和默认值。你可以根据实际需求修改这个类，从配置文件或者环境变量中读取配置项，并实现缓存机制来提高性能。同时也提供了一个清除配置缓存的方法，以便在需要时刷新配置。
class ConfigManager:
    @staticmethod
    def get_config(path):
        return {}

    @staticmethod
    def get_item_bool(config, key):
        return False

    @staticmethod
    def clear_config_cache():
        pass