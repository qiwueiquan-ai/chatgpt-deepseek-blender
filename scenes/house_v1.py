import bpy
import math
import os
from mathutils import Vector

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", os.path.expanduser("~/blender_output"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------- 清空场景 ----------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for block in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
    for b in list(block):
        block.remove(b)

# ---------- 材质 ----------
def mat(name, color, rough=0.8, metal=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = 'BLEND'
    return m

M_WALL = mat("Wall_Mat", (0.78, 0.76, 0.73), 0.9)
M_TRIM = mat("Trim_Mat", (0.30, 0.29, 0.28), 0.7)
M_GLASS = mat("Glass_Mat", (0.05, 0.07, 0.09), 0.15, 0.0, 1.0)
M_CHIMNEY = mat("Chimney_Mat", (0.55, 0.53, 0.50), 0.9)

# ---------- 工具 ----------
def box(name, size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=2, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj

def bevel(obj, w=0.02, seg=2):
    m = obj.modifiers.new("Bevel", 'BEVEL')
    m.width = w
    m.segments = seg
    m.limit_method = 'ANGLE'

# 尺寸
W, D, H = 6.0, 5.0, 3.2
T = 0.18                       # 墙厚
parts = []

# ---------- 正面墙，使用真正的分段墙体洞口 ----------
fy = -D / 2
def add(name, cx, cz, sx, sz):
    parts.append(box(name, (sx, T, sz), (cx, fy, cz), M_WALL))

# --- 正式正面墙分段 z：0..0.9 底带；0.9..2.2 中带；2.2..3.2 顶带 ---
# 底带 (z0..0.9)：门洞 x[-0.5,0.5]，窗洞不触及底部，故：
add("House_Wall_Front_B1", (-3 - 0.5) / 2, 0.45, 2.5, 0.9)   # -3..-0.5
add("House_Wall_Front_B2", (0.5 + 3) / 2, 0.45, 2.5, 0.9)     # 0.5..3
# 中带 (z0.9..2.2)：门洞 x[-0.5,0.5] 全开；左窗 x[-2.4,-0.9] 全开；右窗 x[1.0,2.5] 全开
add("House_Wall_Front_M1", (-3 - 2.4) / 2, 1.55, 0.6, 1.3)    # -3..-2.4
add("House_Wall_Front_M2", (-0.9 - 0.5) / 2, 1.55, 0.4, 1.3)  # -0.9..-0.5
add("House_Wall_Front_M3", (0.5 + 1.0) / 2, 1.55, 0.5, 1.3)   # 0.5..1.0
add("House_Wall_Front_M4", (2.5 + 3) / 2, 1.55, 0.5, 1.3)     # 2.5..3
# 顶带 (z2.2..3.2)：整条
add("House_Wall_Front_T", 0, 2.7, 6.0, 1.0)

# ---------- 背面墙 (+Y) 整面 ----------
parts.append(box("House_Wall_Back", (W, T, H), (0, D / 2, H / 2), M_WALL))

# ---------- 左右侧墙 ----------
# 左墙 x=-3，跨 y[-2.5,2.5] 长度 5，z 0..3.2
parts.append(box("House_Wall_Left", (T, D, H), (-W / 2, 0, H / 2), M_WALL))
# 右墙 x=+3 有窗：窗洞 1.5 宽（沿 y）×1.3 高，竖直位置 z0.9..2.2，让窗户中心 y=0.8
# 右墙分段：沿 y 从 -2.5..2.5；窗 y∈[0.05,1.55]
def right_wall():
    ry = W / 2
    # 底带 z0..0.9 整条
    parts.append(box("House_Wall_Right_B", (T, D, 0.9), (ry, 0, 0.45), M_WALL))
    # 中带 z0.9..2.2：前段 y[-2.5,0.05]，后段 y[1.55,2.5]，窗洞 y[0.05,1.55]
    parts.append(box("House_Wall_Right_M1", (T, (0.05 + 2.5), 1.3), (ry, (-2.5 + 0.05) / 2, 1.55), M_WALL))
    parts.append(box("House_Wall_Right_M2", (T, (2.5 - 1.55), 1.3), (ry, (1.55 + 2.5) / 2, 1.55), M_WALL))
    # 顶带 z2.2..3.2 整条
    parts.append(box("House_Wall_Right_T", (T, D, 1.0), (ry, 0, 2.7), M_WALL))
right_wall()

# ---------- 门框/窗框/玻璃/门槛/窗台/台阶 ----------
def frame(name, cx, cy, cz, sx, sy, sz):
    parts.append(box(name, (sx, sy, sz), (cx, cy, cz), M_TRIM))

# 入户门 (在 -Y 面)：门洞 x[-0.5,0.5] z[0,2.1]，门厚 0.06，向内 y=-2.45+0.06
fy = -D / 2
door_w, door_h = 1.0, 2.1
# 门框（四边）
frame("Door_Frame_L", -0.5, fy + 0.03, 1.05, 0.07, 0.08, 2.1)
frame("Door_Frame_R", 0.5, fy + 0.03, 1.05, 0.07, 0.08, 2.1)
frame("Door_Frame_T", 0, fy + 0.03, 2.13, 1.0, 0.08, 0.07)
frame("Door_Frame_B", 0, fy + 0.03, 0.03, 1.0, 0.08, 0.06)
# 门面板
parts.append(box("Door_Panel", (0.92, 0.06, 2.0), (0, fy + 0.09, 1.05), M_TRIM))
# 门槛/小台阶
parts.append(box("Door_Sill", (1.2, 0.35, 0.08), (0, fy + 0.02, 0.04), M_TRIM))

# 正面左窗：x[-2.4,-0.9] z[0.9,2.2]，1.5×1.3
def make_window(name, cx, cy, cz, sx, sy, sz, rot_axis=None):
    # 框 (四边)
    fw = 0.07
    parts.append(box(name + "_FrameL", (fw, sy, sz), (cx - sx / 2 + fw / 2, cy, cz), M_TRIM))
    parts.append(box(name + "_FrameR", (fw, sy, sz), (cx + sx / 2 - fw / 2, cy, cz), M_TRIM))
    parts.append(box(name + "_FrameT", (sx, sy, fw), (cx, cy, cz + sz / 2 - fw / 2), M_TRIM))
    parts.append(box(name + "_FrameB", (sx, sy, fw), (cx, cy, cz - sz / 2 + fw / 2), M_TRIM))
    # 玻璃
    parts.append(box(name + "_Glass", (sx - 2 * fw, 0.02, sz - 2 * fw), (cx, cy, cz), M_GLASS))

make_window("Window_Front_L", -1.65, fy + 0.05, 1.55, 1.5, 0.06, 1.3)
make_window("Window_Front_R", 1.75, fy + 0.05, 1.55, 1.5, 0.06, 1.3)
# 窗台/窗下墙外挑
parts.append(box("Window_Front_L_Sill", (1.6, 0.1, 0.08), (-1.65, fy - 0.06, 0.9), M_TRIM))
parts.append(box("Window_Front_R_Sill", (1.6, 0.1, 0.08), (1.75, fy - 0.06, 0.9), M_TRIM))

# 右窗（+X 面），沿 y 方向宽度 1.5，竖直 z 1.3 中心 1.55
def make_window_side(name, cx, cy, cz, sx, sy, sz):
    fw = 0.07
    # y 方向是窗口宽 sy，x 是墙厚方向
    parts.append(box(name + "_FrameF", (sx, fw, sz), (cx, cy - sy / 2 + fw / 2, cz), M_TRIM))
    parts.append(box(name + "_FrameK", (sx, fw, sz), (cx, cy + sy / 2 - fw / 2, cz), M_TRIM))
    parts.append(box(name + "_FrameT", (sx, sy, fw), (cx, cy, cz + sz / 2 - fw / 2), M_TRIM))
    parts.append(box(name + "_FrameB", (sx, sy, fw), (cx, cy, cz - sz / 2 + fw / 2), M_TRIM))
    parts.append(box(name + "_Glass", (0.02, sy - 2 * fw, sz - 2 * fw), (cx, cy, cz), M_GLASS))

make_window_side("Window_Right", W / 2 + 0.05, 0.8, 1.55, 0.06, 1.5, 1.3)
parts.append(box("Window_Right_Sill", (0.1, 1.6, 0.08), (W / 2 + 0.06, 0.8, 0.9), M_TRIM))

# ---------- 屋顶 + 女儿墙 + 挑檐 ----------
# 平屋顶板：略大于墙体，形成挑檐
roof_t = 0.16
parts.append(box("House_Roof_Slab", (W + 0.5, D + 0.5, roof_t), (0, 0, H + roof_t / 2), M_WALL))
# 女儿墙：四周随屋顶边缘上翻 0.35
pw_h = 0.35
pw_t = 0.12
parts.append(box("House_Roof_Parapet_F", (W + 0.5, pw_t, pw_h), (0, -(D + 0.5) / 2 + pw_t / 2, H + roof_t + pw_h / 2), M_WALL))
parts.append(box("House_Roof_Parapet_B", (W + 0.5, pw_t, pw_h), (0, (D + 0.5) / 2 - pw_t / 2, H + roof_t + pw_h / 2), M_WALL))
parts.append(box("House_Roof_Parapet_L", (pw_t, D + 0.5, pw_h), (-(W + 0.5) / 2 + pw_t / 2, 0, H + roof_t + pw_h / 2), M_WALL))
parts.append(box("House_Roof_Parapet_R", (pw_t, D + 0.5, pw_h), ((W + 0.5) / 2 - pw_t / 2, 0, H + roof_t + pw_h / 2), M_WALL))
# 细挑檐边条
parts.append(box("House_Roof_Eave", (W + 0.7, D + 0.7, 0.04), (0, 0, H + 0.02), M_TRIM))

# ---------- 烟囱（后侧） ----------
ch_x, ch_y = 1.8, 1.5
ch_w, ch_d = 0.5, 0.5
ch_h = H + 0.9
parts.append(box("Chimney_Body", (ch_w, ch_d, ch_h), (ch_x, ch_y, ch_h / 2), M_CHIMNEY))
parts.append(box("Chimney_Cap", (ch_w + 0.14, ch_d + 0.14, 0.08), (ch_x, ch_y, ch_h + 0.04), M_TRIM))

# ---------- Bevel 适度应用到所有部件 ----------
for p in parts:
    bevel(p, 0.015, 2)

# ---------- 相机：正前偏右 3/4 正交 ----------
cam_data = bpy.data.cameras.new("Camera")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = 9.5
cam = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (11.0, -10.0, 8.5)
target = Vector((0, 0, 1.8))
direction = target - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam

# ---------- 灯光：2-3 组 area ----------
def add_area(name, loc, energy, size, color=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = energy
    ld.size = size
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = loc
    d = target - Vector(loc)
    lo.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.collection.objects.link(lo)

add_area("Light_Key", (6, -7, 9), 1200, 6, (1.0, 0.97, 0.92))
add_area("Light_Fill", (-7, -4, 5), 500, 6, (0.9, 0.94, 1.0))
add_area("Light_Rim", (2, 8, 7), 600, 5, (1.0, 1.0, 1.0))

# ---------- 世界环境透明 ----------
world = bpy.data.worlds.new("World") if not bpy.data.worlds else bpy.data.worlds[0]
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.9, 0.9, 0.9, 1.0)
    bg.inputs[1].default_value = 0.3

# ---------- 渲染设置 ----------
scene = bpy.context.scene
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
# Use CPU Cycles for reliable headless rendering on GitHub Actions.
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
# Ubuntu package Blender is built without OpenImageDenoiser.
# Disable all Cycles denoising to support CPU-only GitHub runners.
for view_layer in scene.view_layers:
    if hasattr(view_layer, 'cycles'):
        view_layer.cycles.use_denoising = False

# ---------- 保存与渲染 ----------
blend_path = os.path.join(OUTPUT_DIR, "house_v1.blend")
png_path = os.path.join(OUTPUT_DIR, "house_v1_preview.png")
scene.render.filepath = png_path
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
try:
    bpy.ops.render.render(write_still=True)
except Exception:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.cycles.device = 'CPU'
    bpy.ops.render.render(write_still=True)

print("Model objects:", len([o for o in bpy.data.objects if o.type == 'MESH']))
print("Saved blend:", blend_path)
print("Saved preview:", png_path)