import bpy
import math
import colorsys
import time

print("=Launch")

ball_bounciness = 0.05
ball_start_location = (0, 0, 6)
platform_base_angle = 70
frame_rate = 24

bpy.context.scene.frame_start = 1
bpy.context.scene.gravity[2] = -9.81 #m/s^-2


notes_US = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
notes_EU = ["La", "La#", "Si", "Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#"]

# time(sec), note, octave
notes_list = [
[3.720, "B", 0],
[4.200, "E", 1],
[4.921, "G", 1],
[5.155, "F#", 1],
[5.555, "E", 1],
[6.573, "B", 1],
[7.040, "A", 1],
[8.391, "F#", 1],
[9.743, "E", 1],
[10.477, "G", 1],
[10.744, "F#", 1],
[11.177, "D#", 1],
[12.062, "F", 1],
[12.612, "B", 0]
]


def generate_color(note_index, total_notes):
    hue = note_index / total_notes
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 0.95)
    return (r, g, b, 1)

note_colors_US = {note: generate_color(i, len(notes_US)) for i, note in enumerate(notes_US)}
note_colors_EU = {note: generate_color(i, len(notes_EU)) for i, note in enumerate(notes_EU)}

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def load_base_scene():
    bpy.ops.wm.open_mainfile(filepath="ressources/base.blend")
    # wait for the scene to be correctly loaded
    time.sleep(1)

def create_platform(i, frame, location, rotation, note):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0,0,-0.5))
    collider = bpy.context.object
    # top surface of platform at origin
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
    
    collider.location = location
    collider.scale = (2, 2, 0.5)
    collider.rotation_euler = rotation
    if i < 0:
        collider.name = f"Platform_base"
    else:
        collider.name = f"Platform_{i}_f{frame}_{note}"
    bpy.ops.rigidbody.object_add()
    collider.rigid_body.type = 'PASSIVE'
    collider.rigid_body.friction = 0.1
    collider.rigid_body.restitution = 1
    
    # Pretty platform (only for render)
    pretty_platform_ref = bpy.data.objects.get("S_pretty_platform")
    pretty_platform_ref.hide_render = False
    pretty_platform_ref.hide_set(False)
    
    bpy.ops.object.select_all(action='DESELECT')
    pretty_platform_ref.select_set(True)
    bpy.ops.object.duplicate(linked=True)
    instance_pretty = bpy.context.selected_objects[0]
    instance_pretty.location = collider.location
    instance_pretty.rotation_euler = collider.rotation_euler
    instance_pretty.hide_render = False
    instance_pretty.hide_set(False)
    if frame >= 0:

        bpy.context.scene.frame_set(frame-1)
        data_path_color = "color"
        activated_prop = "Prop_activated"
        data_path_activated = f'["{activated_prop}"]'
        instance_pretty[activated_prop] = 0.0
        instance_pretty.keyframe_insert(data_path=data_path_color, frame=frame-1)
        instance_pretty.keyframe_insert(data_path=data_path_activated, frame=frame-1)

        bpy.context.scene.frame_set(frame)
        if note in note_colors_US:
            instance_pretty.color = note_colors_US[note]
        if note in note_colors_EU:
            instance_pretty.color = note_colors_EU[note]

        instance_pretty[activated_prop] = 1.0
        instance_pretty.keyframe_insert(data_path=data_path_activated, frame=frame)
        instance_pretty.keyframe_insert(data_path=data_path_color, frame=frame)
    
    instance_pretty.name = collider.name + "_pretty"

    mat = bpy.data.materials.get("M_platform_plate")
    collider.data.materials.append(mat)
    instance_pretty.data.materials.append(mat)
        
    return collider

def create_ball(location, radius=0.5):
    ball = bpy.data.objects.get("Ball")
    ball.rigid_body.type = 'ACTIVE'
    ball.rigid_body.mass = 1
    ball.rigid_body.friction = 0.1
    ball.rigid_body.restitution = ball_bounciness
    return ball

def create_wall(ball_position_at_the_end):
    wall = bpy.data.objects.get("wall")
    wall.scale = (1, 100, abs(ball_position_at_the_end[2]) + 50)


def run_simulation(ball, stop_frame):
    bpy.ops.ptcache.free_bake_all()
    bpy.context.scene.frame_set(bpy.context.scene.frame_start)

    for frame in range(bpy.context.scene.frame_start, stop_frame + 1):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        
        #print("#{} position {}".format(frame, ball.matrix_world.translation))

        if frame == stop_frame:
            # we want the rigid body transfo location, not the object location
            return ball.matrix_world.translation.copy()
    return None

def setup_cameras():
    #empty
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    empty_loc = bpy.context.object
    empty_loc.name = "E_Ball_loc"
    bpy.ops.object.constraint_add(type='COPY_LOCATION')
    empty_loc.constraints["Copy Location"].target = bpy.data.objects["Ball"]
    empty_loc.constraints["Copy Location"].use_offset = True
    
    bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    empty_rot = bpy.context.object
    empty_rot.name = "E_Ball_rot"
    empty_rot.rotation_euler = (math.radians(73), 0, math.radians(80))
    empty_rot.parent = empty_loc
        
    # close-up camera
    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW')
    cam = bpy.context.object
    cam.parent = empty_rot
    cam.name = "C_close"
    cam.location[2] = 24
    
    # large camera
    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW')
    cam = bpy.context.object
    cam.parent = empty_rot
    cam.name = "C_large"
    cam.location[2] = 50


def generate_platforms_from_notes(platforms_colliders):
    ball_position_at_end = (0,0,0)
    ball = bpy.data.objects.get("Ball")

    for (i, frame_note) in enumerate(notes_list):
        (time, note, octave) = frame_note
        frame = int(time * frame_rate)
        print(f"=== {frame=} {note=}")
        ball_position_at_end = run_simulation(ball, frame)
        print(f"=== {ball_position_at_end=}")

        # TODO : better angle for platforms :
        # if notes are close, we might want to have close platform orientation
        # so the ball is more rolling on successive platforms, rather than bouncing back and forth
        platform_angle = platform_base_angle if i % 2 else -platform_base_angle
        platforms_colliders.append(create_platform(i, frame,
                                                    location=ball_position_at_end, 
                                                    rotation=(math.radians(platform_angle), 0, 0), 
                                                    note=note))
    return ball_position_at_end

def hide_colliders(platforms_colliders):
    for collider in platforms_colliders:
        collider.hide_render = True
        collider.hide_set(True)

    pretty_platform_ref = bpy.data.objects.get("S_pretty_platform")
    pretty_platform_ref.hide_render = True
    pretty_platform_ref.hide_set(True)

def main():
    platforms_colliders = []
    ball = create_ball(location=ball_start_location)
    setup_cameras()
    platforms_colliders.append(create_platform(-1, -1,
                                location=(0,0,-20), 
                                rotation=(math.radians(20.0), 0, 0), 
                                note="")
                                )
    
    ball_position_at_end = generate_platforms_from_notes(platforms_colliders)

    create_wall(ball_position_at_end)
    hide_colliders(platforms_colliders)


if __name__ == '__main__':
    load_base_scene()
    bpy.app.timers.register(main, first_interval=0.01)


