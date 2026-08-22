import ollama


DEFAULT_MODEL = "llama3.1:8b"


def check_ollama():
    """Check whether Ollama is running."""
    try:
        ollama.list()
        return True
    except Exception:
        return False


def list_models():
    """Return the models available in Ollama."""
    try:
        response = ollama.list()
        return response.models
    except Exception as e:
        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        ) from e


def generate(prompt, system_prompt=None, model=DEFAULT_MODEL):
    """Generate text using Ollama."""
    ensure_model(model)

    messages = []

    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })

    messages.append({
        "role": "user",
        "content": prompt
    })

    response = ollama.chat(
        model=model,
        messages=messages
    )

    return response.message.content


def generate_json(prompt, model=DEFAULT_MODEL):
    """Generate structured JSON using Ollama."""
    ensure_model(model)

    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        format="json"
    )

    return response.message.content


def pull_model(model=DEFAULT_MODEL):
    """Download a model if needed."""
    if not check_ollama():
        raise RuntimeError(
            "Ollama is not running. Please start Ollama and try again."
        )

    return ollama.pull(model)

def ensure_model(model=DEFAULT_MODEL):
    """Check whether a model exists and pull it if missing."""
    if not check_ollama():
        raise RuntimeError(
            "Ollama is not running. Please start Ollama and try again."
        )

    models = list_models()

    model_names = [m.model for m in models]

    if model not in model_names:
        print(f"Model '{model}' not found. Downloading it...")
        return pull_model(model)

    return True