"""Start the canonical V2 Blender GUI MCP endpoint without saving the file."""

import bpy


scene = bpy.context.scene
saved_port = scene.blendermcp_port
if scene.blendermcp_server_running:
    bpy.ops.blendermcp.stop_server()
scene.blendermcp_port = 9877
result = bpy.ops.blendermcp.start_server()
if result != {"FINISHED"} or not scene.blendermcp_server_running:
    raise RuntimeError(f"Unable to start BlenderMCP on port 9877: {result}")
# The server keeps its constructed port. Restore the persisted scene value so
# starting the endpoint does not leave an unsaved change in the source file.
scene.blendermcp_port = saved_port
print("Canonical V2 BlenderMCP listening on 127.0.0.1:9877")
