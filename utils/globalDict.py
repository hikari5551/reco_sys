class GlobalDict:
    _instance = None
    _data = {}

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