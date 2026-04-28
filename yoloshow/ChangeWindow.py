from utils import globalDict

# 这个文件定义了两个函数，用于在yoloshow和yoloshowvs两个窗口之间切换显示状态。通过全局字典获取窗口实例，调用hide()和show()方法实现切换。
def yoloshow2vs():
    yolo_win = globalDict.get_value("yoloshow")
    vs_win = globalDict.get_value("yoloshowvs")
    if yolo_win and vs_win:
        yolo_win.hide()
        vs_win.show()

def vs2yoloshow():
    yolo_win = globalDict.get_value("yoloshow")
    vs_win = globalDict.get_value("yoloshowvs")
    if yolo_win and vs_win:
        vs_win.hide()
        yolo_win.show()