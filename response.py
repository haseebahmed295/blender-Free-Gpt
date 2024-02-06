import bpy
import g4f
g4f.debug.version_check = False
def wrap_prompt(prompt):
    wrapped = f"""Can you please write Blender code for me that accomplishes the following task: \n
    {prompt}\n Don't use bpy.context.active_object. Color requires an alpha channel ex: red = (1,0,0,1). 
    Make sure to return all  code in only one code blocks\n 
    """
    return wrapped

def split_area_to_text_editor(context):
    area = context.area
    for region in area.regions:
        if region.type == 'WINDOW':
            with context.temp_override(area=area, region=region):
                # bpy.ops.screen.area_split(direction='VERTICAL', factor=0.5)
                bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
            break

    new_area = context.screen.areas[-1]
    new_area.type = 'TEXT_EDITOR'
    return new_area

def append_error_as_comment(code_str, error):
    error_lines = str(error).splitlines()
    commented_error = "\n".join("# " + line for line in error_lines)
    updated_code = code_str + "\n # Code Output:\n" + commented_error
    return updated_code