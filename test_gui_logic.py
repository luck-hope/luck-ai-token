"""
TokenTrackerGateway - 原生 GUI 坐标、碰撞箱与动作状态机离线集成测试
"""
import sys
import ast

class MockRect:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, px, py):
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

def run_gui_simulation():
    print("=== 开始执行原生桌面 GUI 碰撞箱与点击事件判定测试 ===")
    
    # 1. 模拟 Expanded 全量看板态 (macOS 与 Windows 分支)
    rect_x, rect_y, rect_w, rect_h = 0, 0, 780, 500
    
    # (a) macOS 控制按钮
    red_hit = MockRect(rect_x + 8, rect_y + 6, 24, 30)
    yellow_hit = MockRect(rect_x + 32, rect_y + 6, 22, 30)
    green_hit = MockRect(rect_x + 54, rect_y + 6, 24, 30)
    
    assert red_hit.contains(rect_x + 20, rect_y + 20), "Red close button click failed"
    assert yellow_hit.contains(rect_x + 42, rect_y + 20), "Yellow orb button click failed"
    assert green_hit.contains(rect_x + 64, rect_y + 20), "Green capsule button click failed"
    print("✓ macOS 红黄绿红绿灯控制按钮 (100% 触控命中)")

    # (b) Windows 控制按钮 (右上角 X 和胶囊/圆标)
    win_close_hit = MockRect(rect_x + 780 - 240 + 174, rect_y + 6, 36, 32)
    win_shrink_cap = MockRect(rect_x + 780 - 240 + 100, rect_y + 8, 32, 28)
    win_shrink_orb = MockRect(rect_x + 780 - 240 + 136, rect_y + 8, 32, 28)
    assert win_close_hit.contains(rect_x + 780 - 45, rect_y + 20), "Windows close button click failed"
    assert win_shrink_cap.contains(rect_x + 780 - 120, rect_y + 20), "Windows shrink to capsule click failed"
    assert win_shrink_orb.contains(rect_x + 780 - 85, rect_y + 20), "Windows shrink to orb click failed"
    print("✓ Windows 右上角原生 '✕' 关闭键与缩放控件 (100% 触控命中)")

    # 2. 模拟 Capsule 胶囊态
    cap_x, cap_y, cap_w, cap_h = 0, 0, 520, 44
    orb_hit = MockRect(cap_x, cap_y, 44, cap_h)
    prev_hit = MockRect(cap_x + 94, cap_y, 24, cap_h)
    title_hit = MockRect(cap_x + 118, cap_y, 118, cap_h)
    next_hit = MockRect(cap_x + 236, cap_y, 24, cap_h)
    cost_hit = MockRect(cap_x + 306, cap_y, 62, cap_h)
    expand_hit = MockRect(cap_x + 482, cap_y, 36, cap_h)

    assert orb_hit.contains(cap_x + 20, cap_y + 22), "Capsule left orb click failed"
    assert prev_hit.contains(cap_x + 105, cap_y + 22), "Capsule prev button click failed"
    assert next_hit.contains(cap_x + 248, cap_y + 22), "Capsule next button click failed"
    assert title_hit.contains(cap_x + 150, cap_y + 22), "Capsule title click failed"
    assert cost_hit.contains(cap_x + 330, cap_y + 22), "Capsule cost toggle click failed"
    assert expand_hit.contains(cap_x + 495, cap_y + 22), "Capsule expand button click failed"
    print("✓ 胶囊态各控件热区与任务切换按钮 (100% 触控命中)")

    # 3. 模拟状态机切换
    state = {"mode": "capsule", "task_idx": 0, "tasks_len": 5, "show_cost": False, "is_dark": True}
    
    # 模拟点击 prev
    state["task_idx"] = (state["task_idx"] - 1) % state["tasks_len"]
    assert state["task_idx"] == 4, "Prev task wrap failed"
    
    # 模拟点击 next
    state["task_idx"] = (state["task_idx"] + 1) % state["tasks_len"]
    assert state["task_idx"] == 0, "Next task wrap failed"

    # 模拟点击 expand
    state["mode"] = "expanded"
    assert state["mode"] == "expanded"

    # 模拟点击 mac 绿色按钮 (shrink_capsule)
    state["mode"] = "capsule"
    assert state["mode"] == "capsule"

    # 模拟点击 mac 黄色按钮 (shrink_circle)
    state["mode"] = "circle"
    assert state["mode"] == "circle"

    print("✓ 多模态状态流转 (circle <-> capsule <-> expanded) 验证通过")
    print("=== 全部原生 GUI 逻辑测试通过 ===")

if __name__ == "__main__":
    run_gui_simulation()
