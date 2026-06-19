from app.model_loader import load_model


def check_safety_ml(text: str):
    text = text.strip()
    if not text:
        return "safe", 0.0
    model = load_model()
    pred = model.predict([text])[0]
    proba = model.predict_proba([text])[0]
    score = float(proba[list(model.classes_).index(pred)])
    return pred, score
