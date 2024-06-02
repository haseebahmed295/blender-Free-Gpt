import g4f
deprecated_models = [
    "codellama-34b-intruct",
    "codellama-70b-instruct",
    'gemini',
    'gemini-pro',
    'claude-v2',
    'claude-3-opus',
    'claude-3-sonnet',
    "reka",
    'dbrx-instruct',
    'gigachat',
    "pi",
    ]

def get_models():
    Models = []
    for model in g4f.models._all_models:
        if model not in deprecated_models:
            Models.append((model, model , model))
    print(len(Models))
    return Models

