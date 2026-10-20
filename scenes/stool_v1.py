import bpy
import os
import math
from mathutils import Vector

OUT = os.environ.get("OUTPUT_DIR", os.path.expanduser("~/blender_output"))
os.makedirs(OUT, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = 0.75
    return m

wood = material("Natural_Oak_Light", (0.58, 0.39, 0.22))
endwood = material("Oak_End_Grain", (0.47, 0.29, 0.14))
parts = []

def cube(name, dimensions, location, mat, bevel=0.003):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    o=bpy.context.object
    o.name=name
    o.dimensions=dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new("Soft_Rounded_Edges", "BEVEL")
        mod.width=bevel
        mod.segments=3
        mod.limit_method='ANGLE'
        mod2=o.modifiers.new("Weighted_Normals", "WEIGHTED_NORMAL")
    parts.append(o)
    return o

def beam(name, p1, p2, thickness, mat):
    a,b=Vector(p1),Vector(p2)
    mid=(a+b)/2
    direction=b-a
    o=cube(name, (thickness, thickness, direction.length), mid, mat, 0.0025)
    o.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
    return o

# Z=0 floor, 450mm finished height. Seat occupies Z=420..450mm.
seat=cube("01_Seat_Solid_Oak_360x360x30mm", (.36,.36,.03), (0,0,.435),wood,.017)
# Four inclined legs, top centre +/- 115mm, foot centre +/- 145mm.
# Beam ends at the seat's lower surface and ground.
for sx,sy,label in [(-1,-1,"Front_Left"),(1,-1,"Front_Right"),(-1,1,"Back_Left"),(1,1,"Back_Right")]:
    beam("02_Leg_"+label, (sx*.145, sy*.145, .022), (sx*.115,sy*.115,.42), .044,wood)

# Apron/under-seat braces: four independent rectangular members at 350 mm.
for sy,lab in [(-1,"Front"),(1,"Back")]:
    cube("03_Apron_"+lab,(.255,.025,.048),(0,sy*.115,.371),wood,.003)
for sx,lab in [(-1,"Left"),(1,"Right")]:
    cube("03_Apron_"+lab,(.025,.255,.048),(sx*.115,0,.371),wood,.003)

# Small foot pads guarantee feet reach floor visually while preserving editable parts.
for sx,sy,label in [(-1,-1,"FL"),(1,-1,"FR"),(-1,1,"BL"),(1,1,"BR")]:
    cube("04_Foot_"+label,(.044,.044,.012),(sx*.145,sy*.145,.006),endwood,.002)

# Studio camera and lights; none are joined with the stool components.
target=Vector((0,0,.24))
cam_data=bpy.data.cameras.new("Studio_Camera")
cam_data.type='ORTHO'
cam_data.ortho_scale=.83
cam=bpy.data.objects.new("Studio_Camera",cam_data)
bpy.context.collection.objects.link(cam)
cam.location=(.85,-1.0,.73)
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.scene.camera=cam

def area(name,pos,power,size):
    data=bpy.data.lights.new(name,'AREA')
    data.energy=power
    data.shape='DISK'
    data.size=size
    obj=bpy.data.objects.new(name,data)
    bpy.context.collection.objects.link(obj)
    obj.location=pos
    obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
area("Key_Light",(.6,-.7,1.5),130,.9)
area("Fill_Light",(-.8,-.3,.9),65,.9)
area("Rim_Light",(.3,.7,1.1),100,.8)

scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.device='CPU'
scene.cycles.samples=24
for vl in scene.view_layers:
    if hasattr(vl,'cycles'):
        vl.cycles.use_denoising=False
scene.render.resolution_x=1280
scene.render.resolution_y=960
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGBA'
scene.render.film_transparent=True
world=bpy.data.world
world.color=(.75,.75,.75)
if world.use_nodes:
    bg=world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value=(.8,.8,.8,1)
        bg.inputs["Strength"].default_value=.8

scene.render.filepath=os.path.join(OUT,"stool_v1_preview.png")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"stool_v1.blend"))
bpy.ops.render.render(write_still=True)
print("Editable stool pieces:",len(parts))
print("Output:",OUT)
