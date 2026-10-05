"""Scripts that run INSIDE Blender (`blender --background --python <script> -- <args>`).

They must not import avatar_forge (Blender has its own Python). Pass everything via
command-line args or a JSON file. Use avatar_forge.blender_runner.run_blender() to call them.
"""
