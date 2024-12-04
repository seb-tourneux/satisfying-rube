import bpy
import math

print("=Launch")

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

ball_bounciness = 0.5
ball_start_location = (0, 0, 6)
platform_angle = 15

# Animation settings
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 300
bpy.context.scene.gravity[2] = -30 #m/s^-2

# frame, note
notes_list = [[40, "Do"], 
         [60, "La"],
         [100, "Fa"],
         [150 , "Mi"],
         [200 , "Sol"]
]

notes_colors = {
 'Do': (0.237, 0.631, 0.858, 1),
 'Ré': (0.865, 0.573, 0.046, 1),
 'Mi': (0.868, 0.137, 0.973, 1),
 'Fa': (0.211, 0.054, 0.771, 1),
 'Sol': (0.888, 0.888, 0.114, 1),
 'La': (0.745, 0.516, 0.314, 1),
 'Si': (0.913, 0.237, 0.667, 1)
}

def create_platform(location, rotation, note):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    platform = bpy.context.object
    platform.scale = (2, 2, 0.5)
    platform.rotation_euler = rotation
    platform.name = "Platform"
    bpy.ops.rigidbody.object_add()
    platform.rigid_body.type = 'PASSIVE'
    platform.rigid_body.friction = 0.1
    platform.rigid_body.restitution = 1
    platform.color = notes_colors[note]
    return platform

def create_ball(location, radius=0.5):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    ball = bpy.context.object
    ball.name = "Ball"
    bpy.ops.rigidbody.object_add()
    ball.rigid_body.type = 'ACTIVE'
    ball.rigid_body.mass = 1
    ball.rigid_body.friction = 0
    ball.rigid_body.restitution = ball_bounciness
    return ball

def run_simulation(stop_frame):
    # Set the frame to the start frame
    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
    bpy.ops.ptcache.free_bake_all()       
    
    # ball = bpy.data.objects["Ball"]
    # ball.location = ball_start_location

    # Loop through each frame until the stop frame
    for frame in range(bpy.context.scene.frame_start, stop_frame + 1):
        bpy.context.scene.frame_set(frame)  # Move to the next frame
        bpy.context.view_layer.update()     # Update the scene to reflect changes
        
        print("#{} position {}".format(frame, ball.matrix_world.translation))

        if frame == stop_frame:
            return ball.matrix_world.translation.copy()
    return None

def setup_camera():
    bpy.ops.object.camera_add(enter_editmode=False, align='VIEW')
    bpy.context.object.location = (9, -1.7, 2.18)
    bpy.context.object.rotation_euler = (math.radians(73), 0, math.radians(80))

    bpy.ops.object.constraint_add(type='COPY_LOCATION')
    bpy.context.object.constraints["Copy Location"].target = bpy.data.objects["Ball"]
    bpy.context.object.constraints["Copy Location"].use_offset = True



ball = create_ball(location=ball_start_location)
setup_camera()

for (i, frame_note) in enumerate(notes_list):
    (frame, note) = frame_note
    print("=== frame {} note {}".format(frame, note))
    ball_position_at_end = run_simulation(frame)
    print("ball_position_at_end {}".format(ball_position_at_end))
    
    create_platform(location=ball_position_at_end, 
                    rotation=(math.radians(platform_angle if i % 2 else -platform_angle), 0, 0), 
                    note=note)

