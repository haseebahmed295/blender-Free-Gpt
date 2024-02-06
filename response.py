import bpy
import re
import os
import sys
import g4f

def wrap_prompt(prompt):
    wrapped = f"""Can you please write Blender code for me that accomplishes the following task: \n
    {prompt}\n Don't use bpy.context.active_object. Color requires an alpha channel ex: red = (1,0,0,1). 
    Make sure to return all  code in only one code blocks\n 
    """
    return wrapped


def generate_g4f_code(prompt, chat_history, context, system_prompt):
    messages = [{"role": "system", "content": system_prompt}]
    for message in chat_history[-10:]:
        if message.type == "assistant":
            messages.append({"role": "assistant", "content": "```\n" + message.content + "\n```"})
        else:
            messages.append({"role": message.type.lower(), "content": message.content})

    # Add the current user message
    messages.append({"role": "user", "content": wrap_prompt(prompt)})

    response = g4f.ChatCompletion.create(
        model=context.scene.gpt4_model,
        messages=messages,
        stream=True,
    )

    try:
        completion_text = ''
        for chunk in response:
            completion_text += chunk
            print(chunk, flush=True, end='')
        completion_text = re.findall(r'```(.*?)```', completion_text, re.DOTALL)[0]
        completion_text = re.sub(r'^python', '', completion_text, flags=re.MULTILINE)

        return completion_text
    except IndexError:
        return None


def split_area_to_text_editor(context):
    area = context.area
    for region in area.regions:
        if region.type == 'WINDOW':
            with context.temp_override(area=area, region=region):
                bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
            break

    new_area = context.screen.areas[-1]
    new_area.type = 'TEXT_EDITOR'
    return new_area

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
