import g4f

deprecated_models = [
    'pi', 
    'openchat_3.5',
    'bard' , 
    'claude-v2' ,
    'gpt-4' ,
    'gpt-4-32k-0613' ,
    "gpt-4-32k" ,
    'gpt-4-0613'
    ]

def get_models():
    Models = []
    for model in g4f.models._all_models:
        if model not in deprecated_models:
            Models.append((model, model , model))
    return Models

