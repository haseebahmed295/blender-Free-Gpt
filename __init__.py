import sys
import os
import bpy
import bpy.props
import re
import json

# Add the 'libs' folder to the Python path
libs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
if libs_path not in sys.path:
    sys.path.append(libs_path)
from .response import *

bl_info = {
    "name": "Blender Free Gpt",
    "blender": (3, 00, 0),
    "category": "Object",
    "author": "haseebahmed295",
    "version": (1, 0, 0),
    "location": "3D View > UI > Free Gpt",
    "description": "Automate Blender using GPT without an API key.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
}

from .system_commad import system_prompt

class Chat_History_Panel(bpy.types.Panel):
    bl_label = "Chat History"
    bl_idname = "G4fchat_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Free Gpt'

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)
        column.label(text="Chat history:")
        for index, message in enumerate(context.scene.g4f_chat_history):
            if index % 2 == 0:
                box = column.box()
            row = box.row()
            if message.type == 'assistant':
                row.label(text="Assistant: ")
                code_part = row.operator(G4F_OT_ShowCode.bl_idname, text="Show Code")
                code_part.code = message.content
            else:
                row.label(text=f"User: {message.content}")
            row.operator(G4T_Del_Message.bl_idname, text="", icon="TRASH", emboss=False).index = index
        layout.operator("gpt4.clear_chat", text="Clear Chat")
        column.separator()


class G4F_PT_Panel(bpy.types.Panel):
    bl_label = "Assistant GPT"
    bl_idname = "G4T_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Free Gpt'

    def draw(self, context):
        layout = self.layout
        column = layout.column(align=True)

        column.label(text="GPT Model:")
        column.prop(context.scene, "gpt4_model", text="")

        column.label(text="Enter your message:")
        column.prop(context.scene, "g4f_chat_input", text="")
        
        column.scale_y = 1.25
        
        button_label = "Please wait..." if context.scene.g4f_button_pressed else "Execute"
        row = column.row(align=True)
        row.operator(G4F_OT_Execute.bl_idname, text=button_label)
        column.separator()


class G4F_OT_ClearChat(bpy.types.Operator):
    bl_idname = "gpt4.clear_chat"
    bl_label = "Clear Chat"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.g4f_chat_history.clear()
        return {'FINISHED'}


class G4F_OT_Execute(bpy.types.Operator):
    bl_idname = "g4f.prompt"
    bl_label = "Send Message"
    bl_options = {'REGISTER', 'UNDO'}

    natural_language_input: bpy.props.StringProperty(
        name="Command",
        description="Enter the natural language command",
        default="",
    )

    def execute(self, context):
        context.scene.g4f_button_pressed = True
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        ## add context to system prompt
        # Get the minimal scene data
        scene_data = {
            "objects": []
        }

        for obj in bpy.context.scene.objects:
            scene_data["objects"].append({
                "name": obj.name,
                "type": obj.type,
                # "location": list(obj.location),
                # "rotation_euler": list(obj.rotation_euler),
                # "scale": list(obj.scale),
            })

        if len(scene_data["objects"]) == 0: scene_data = None
        # if scene_data:
        #     system_prompt = system_prompt + """Below is the minimal scene context.\n""" + json.dumps(scene_data)

        blender_code = generate_g4f_code(context.scene.g4f_chat_input, context.scene.g4f_chat_history, context, system_prompt)

        message = context.scene.g4f_chat_history.add()
        message.type = 'user'
        message.content = context.scene.g4f_chat_input

        # Clear the chat input field
        context.scene.g4f_chat_input = ""

        if blender_code:
            message = context.scene.g4f_chat_history.add()
            message.type = 'assistant'
            message.content = blender_code

            global_namespace = globals().copy()

        try:
            exec(blender_code, global_namespace)
        except Exception as e:
            self.report({'ERROR'}, f"Error executing generated code: {e}")
            context.scene.g4f_button_pressed = False
            return {'CANCELLED'}

        context.scene.g4f_button_pressed = False
        return {'FINISHED'}

class G4T_Del_Message(bpy.types.Operator):
    bl_idname = "gpt.del_message"
    bl_label = "Delete Message from History"
    bl_options = {'REGISTER', 'UNDO'}

    index : bpy.props.IntProperty()

    def execute(self, context):
        context.scene.g4f_chat_history.remove(self.index)
        return {'FINISHED'}

class G4F_OT_ShowCode(bpy.types.Operator):
    bl_idname = "g4f.show_code"
    bl_label = "Show Code"
    bl_options = {'REGISTER', 'UNDO'}

    code:bpy.props.StringProperty(
        name="Code",
        description="The generated code",
        default="",
    )

    def execute(self, context):
        code_name = "G4F_Code.py"
        code_text = bpy.data.texts.get(code_name)
        if code_text is None:
            code_text = bpy.data.texts.new(code_name)

        code_text.clear()
        code_text.write(self.code)

        editor_area = next((area for area in context.screen.areas if area.type == 'TEXT_EDITOR'), None)

        if editor_area is None:
            editor_area = split_area_to_text_editor(context)

        editor_area.spaces.active.text = code_text

        return {'FINISHED'}


class G4FPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__


    def draw(self, context):
        layout = self.layout
        

classes = (
    G4FPreferences,
    G4F_OT_Execute,
    Chat_History_Panel,
    G4F_PT_Panel,
    G4F_OT_ClearChat,
    G4F_OT_ShowCode,
    G4T_Del_Message,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.g4f_chat_history = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    bpy.types.Scene.gpt4_model = bpy.props.EnumProperty(
        name="GPT Model",
        description="Select the GPT model to use",
        items=[
            ("gpt-4-turbo", "GPT-4 (powerful, expensive)", "Use GPT-4"),
            ("gpt-3.5-turbo", "GPT-3.5 Turbo (less powerful, cheaper)", "Use GPT-3.5 Turbo"),
        ],
        default="gpt-4-turbo",
    )
    bpy.types.Scene.g4f_chat_input = bpy.props.StringProperty(
        name="Message",
        description="Enter your message",
        default="",
    )
    bpy.types.Scene.g4f_button_pressed = bpy.props.BoolProperty(default=False)
    bpy.types.PropertyGroup.type = bpy.props.StringProperty()
    bpy.types.PropertyGroup.content = bpy.props.StringProperty()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.g4f_chat_history
    del bpy.types.Scene.g4f_chat_input
    del bpy.types.Scene.g4f_button_pressed


if __name__ == "__main__":
    register()
