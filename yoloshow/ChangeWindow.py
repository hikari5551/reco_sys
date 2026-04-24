from utils import globalDict

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