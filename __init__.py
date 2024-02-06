import re
import sys
import os
import traceback
import bpy
import bpy.props
import threading

libs_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
if libs_path not in sys.path:
    sys.path.append(libs_path)

from .response import *
from .get_models import *
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
            if index % 2 == 0:
                row.operator(G4T_Del_Message.bl_idname, text="", icon="TRASH", emboss=False).index = index
        layout.operator(G4F_OT_ClearChat.bl_idname, text="Clear Chat")
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
        column.prop(context.scene, "ai_models", text="")

        column.label(text="Enter your message:")
        column.prop(context.scene, "g4f_chat_input", text="")
        
        column.scale_y = 1.25
        
        button_label = "Please wait..." if context.scene.g4f_button_pressed else "Prompt"
        row = column.row(align=True)
        row.operator(G4F_OT_Execute.bl_idname, text=button_label)
        column.separator()


class G4F_OT_ClearChat(bpy.types.Operator):
    bl_idname = "g4f.clear_whole_chat"
    bl_label = "Clear Chat"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return False if len(context.scene.g4f_chat_history) ==0 else True
    def execute(self, context):
        context.scene.g4f_chat_history.clear()
        return {'FINISHED'}


class G4F_OT_Execute(bpy.types.Operator):
    bl_idname = "g4f.prompt"
    bl_label = "Send Message"
    bl_description = "Send Prompy to AI see console for live response"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True if not context.scene.g4f_button_pressed else False
    def execute(self, context):
        context.scene.g4f_button_pressed = True

        def callback(output):
            blender_code = output
            message = context.scene.g4f_chat_history.add()
            message.type = 'user'
            message.content = context.scene.g4f_chat_input
            context.scene.g4f_chat_input = ""

            if blender_code:
                global_namespace = globals().copy()
                try:
                    exec(blender_code, global_namespace)
                except Exception as e:
                    self.report({'ERROR'}, f"Error executing code from Ai: {e}")
                    error = traceback.format_exc()
                    blender_code = append_error_as_comment(blender_code,error)
                finally:
                    message = context.scene.g4f_chat_history.add()
                    message.type = 'assistant'
                    message.content = blender_code

            context.scene.g4f_button_pressed = False   

        model = context.scene.ai_models
        long_running_thread = threading.Thread(target=self.generate_g4f_code , args=(context.scene.g4f_chat_input, 
                                                                                    context.scene.g4f_chat_history,
                                                                                    model, system_prompt,callback,))
        long_running_thread.start()
        
        return {'FINISHED'}
    def generate_g4f_code(self, prompt, chat_history, model, system_prompt, callback):
        formatted_messages = [{"role": "system", "content": system_prompt}]
        for message in chat_history[-10:]:
            if message.type == "assistant":
                formatted_messages.append({"role": "assistant", "content": "```\n" + message.content + "\n```"})
            else:
                formatted_messages.append({"role": message.type.lower(), "content": message.content})

        formatted_messages.append({"role": "user", "content": wrap_prompt(prompt)})
        stream = g4f.ModelUtils.convert[model].best_provider.supports_stream
        try:
            response = g4f.ChatCompletion.create(
                model=model,
                messages=formatted_messages,
                stream=stream,
            )
            if stream:
                completion_text = ''
                for chunk in response:
                    completion_text += chunk
                    print(chunk, flush=True, end='')
            else:
                completion_text = response
            completion_text = re.findall(r'```(.*?)```', completion_text, re.DOTALL)[0]
            completion_text = re.sub(r'^python', '', completion_text, flags=re.MULTILINE)

            callback(completion_text)
        except Exception as e:
            self.report({'ERROR'}, f"Error with Ai: {e}")
            bpy.context.scene.g4f_button_pressed = False

class G4T_Del_Message(bpy.types.Operator):
    bl_idname = "gpt.del_message"
    bl_label = "Delete Message from History"
    bl_options = {'REGISTER', 'UNDO'}

    index : bpy.props.IntProperty(options={'HIDDEN'})

    def execute(self, context):
        context.scene.g4f_chat_history.remove(self.index)
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
        bpy.ops.text.jump(line=1)

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
    bpy.types.Scene.ai_models = bpy.props.EnumProperty(
        name="AI Model",
        description="Select the AI model to use",
        items=get_models(),
    )
    bpy.types.Scene.g4f_chat_input = bpy.props.StringProperty(
        name="Message",
        description="Enter your Command",
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
