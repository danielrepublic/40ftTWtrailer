"""Start the canonical v1.1 Blender GUI MCP endpoint without saving the file."""

import bpy


scene = bpy.context.scene
if scene.blendermcp_server_running:
    bpy.ops.blendermcp.stop_server()
if scene.blendermcp_port != 9876:
    raise RuntimeError(
        f"Canonical source MCP port is {scene.blendermcp_port}, expected 9876"
    )
result = bpy.ops.blendermcp.start_server()
if result != {"FINISHED"} or not scene.blendermcp_server_running:
    raise RuntimeError(f"Unable to start BlenderMCP on port 9876: {result}")
print("Canonical BlenderMCP listening on 127.0.0.1:9876")
