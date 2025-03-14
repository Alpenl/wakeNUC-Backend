# 为全局变量提供set和get方法
class GlobalValue():
    # 初始化一个空字典，用于存储全局变量
    def __init__(self):
        self._values = {}

    # 根据键获取对应的值，如果键不存在，则返回None
    def get_value(self, key: str):
        return self._values.get(key, None)

    # 根据键设置对应的值
    def set_value(self, key: str, value):
        self._values[key] = value


global_values = GlobalValue()
