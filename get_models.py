import g4f
deprecated_models = [
    ]

def get_models():
    Models = []
    for model in g4f.models._all_models:
        if model not in deprecated_models:
            Models.append((model, model , model))
    return Models

