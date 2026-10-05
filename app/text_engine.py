import json
import os
import urllib.error
import urllib.request

from app.constants import (
    GEMINI_API_URL,
    OLLAMA_API_URL,
    OPENAI_API_URL,
    get_env_file_path,
    get_system_prompt,
)


def _load_env():
    env_path = get_env_file_path()
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()


class TextEngine:

    PAID_MODELS = ["gpt-4o", "gpt-4o-mini", "gemini-1.5-flash", "gemini-1.5-pro"]

    @staticmethod
    def get_ollama_models():
        url = f"{OLLAMA_API_URL}/api/tags"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = [model["name"] for model in data.get("models", [])]
                return models
        except Exception:
            return []

    @staticmethod
    def generate_text(
        model_type,
        model_name,
        lang,
        tone,
        input_text,
        length="Medium",
        custom_inject="",
    ):
        _load_env()
        system_prompt = get_system_prompt(lang, tone, length, custom_inject)

        if model_type == "Ollama":
            return TextEngine._generate_ollama(model_name, system_prompt, input_text)
        elif model_type == "Paid APIs":
            if model_name.startswith("gpt-"):
                api_key = os.getenv("OPENAI_API_KEY", "")
                if not api_key:
                    raise ValueError("API_KEY_MISSING")
                return TextEngine._generate_openai(
                    model_name, api_key, system_prompt, input_text
                )
            elif model_name.startswith("gemini-"):
                api_key = os.getenv("GEMINI_API_KEY", "")
                if not api_key:
                    raise ValueError("API_KEY_MISSING")
                return TextEngine._generate_gemini(
                    model_name, api_key, system_prompt, input_text
                )
            else:
                raise ValueError(f"Unsupported paid model: {model_name}")
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    @staticmethod
    def _generate_ollama(model_name, system_prompt, input_text):
        url = f"{OLLAMA_API_URL}/api/generate"
        payload = {
            "model": model_name,
            "prompt": input_text,
            "system": system_prompt,
            "stream": False,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip()
        except Exception as e:
            raise RuntimeError(f"Ollama Error: {e!s}")

    @staticmethod
    def _generate_openai(model_name, api_key, system_prompt, input_text):
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ],
            "temperature": 0.7,
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        req = urllib.request.Request(OPENAI_API_URL, data=data, headers=headers)

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"OpenAI Error: {e.code} - {error_body}")
        except Exception as e:
            raise RuntimeError(f"OpenAI Error: {e!s}")

    @staticmethod
    def _generate_gemini(model_name, api_key, system_prompt, input_text):
        url = GEMINI_API_URL.format(model=model_name) + f"?key={api_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"parts": [{"text": input_text}]}],
            "generationConfig": {"temperature": 0.7},
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=data, headers=headers)

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini Error: {e.code} - {error_body}")
        except Exception as e:
            raise RuntimeError(f"Gemini Error: {e!s}")
