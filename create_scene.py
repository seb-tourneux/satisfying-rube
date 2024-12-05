import bpy
import math
import colorsys

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

frame_end = int(notes_list[-1][0] * frame_rate + 10)
bpy.context.scene.use_custom_simulation_range = True
bpy.context.scene.simulation_frame_end = frame_end
bpy.context.scene.frame_end = frame_end

def generate_color(note_index, total_notes):
    hue = note_index / total_notes
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 0.95)
    return (r, g, b, 1)

note_colors_US = {note: generate_color(i, len(notes_US)) for i, note in enumerate(notes_US)}
note_colors_EU = {note: generate_color(i, len(notes_EU)) for i, note in enumerate(notes_EU)}

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def create_platform(i, frame, location, rotation, note):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    platform = bpy.context.object
    platform.scale = (2, 2, 0.5)
    platform.rotation_euler = rotation
    platform.name = f"Platform_{i}_f{frame}_{note}"
    bpy.ops.rigidbody.object_add()
    platform.rigid_body.type = 'PASSIVE'
    platform.rigid_body.friction = 0.1
    platform.rigid_body.restitution = 1

    bpy.context.scene.frame_set(frame-1)
    data_path = "color"
    platform.keyframe_insert(data_path=data_path, frame=frame-1)

    if note in note_colors_US:
        platform.color = note_colors_US[note]
    if note in note_colors_EU:
        platform.color = note_colors_EU[note]

    platform.keyframe_insert(data_path=data_path, frame=frame)
    bpy.context.scene.frame_set(frame)
    platform.keyframe_insert(data_path=data_path, frame=frame)

    return platform

def create_ball(location, radius=0.5):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    ball = bpy.context.object
    ball.name = "Ball"
    bpy.ops.rigidbody.object_add()
    ball.rigid_body.type = 'ACTIVE'
    ball.rigid_body.mass = 1
    ball.rigid_body.friction = 0.1
    ball.rigid_body.restitution = ball_bounciness
    return ball

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
    # large camera
    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW')
    bpy.context.object.location = (100, -9, 24)
    bpy.context.object.rotation_euler = (math.radians(73), 0, math.radians(80))

    bpy.ops.object.constraint_add(type='COPY_LOCATION')
    bpy.context.object.constraints["Copy Location"].target = bpy.data.objects["Ball"]
    bpy.context.object.constraints["Copy Location"].use_offset = True
    
    # close-up camera
    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW')
    bpy.context.object.location = (9, -1.7, 2.18)
    bpy.context.object.rotation_euler = (math.radians(73), 0, math.radians(80))

    bpy.ops.object.constraint_add(type='COPY_LOCATION')
    bpy.context.object.constraints["Copy Location"].target = bpy.data.objects["Ball"]
    bpy.context.object.constraints["Copy Location"].use_offset = True

def generate_platforms_from_notes():
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
        create_platform(i, frame,
                        location=ball_position_at_end, 
                        rotation=(math.radians(platform_angle), 0, 0), 
                        note=note)



if __name__ == '__main__':
    clear_scene()

    ball = create_ball(location=ball_start_location)
    setup_cameras()
    create_platform(-1, 0,
                    location=(0,0,-20), 
                    rotation=(math.radians(20.0), 0, 0), 
                    note="")
    
    generate_platforms_from_notes()


