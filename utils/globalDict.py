class GlobalDict:
    _instance = None
    _data = {}

# 全局字典类，使用单例模式实现，提供全局共享的键值存储功能
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init(self):
        self._data.clear()

    def set_value(self, key, value):
        self._data[key] = value

    def get_value(self, key, default=None):
        return self._data.get(key, default)

globalDict = GlobalDict()