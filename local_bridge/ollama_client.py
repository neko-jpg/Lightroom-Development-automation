import requests
import json
from schema import SCHEMA

class OllamaClient:
    def __init__(self, host='http://localhost:11434'):
        self.host = host

    def generate_config(self, prompt, model="llama3.1:8b-instruct"):
        """
        Generates a Lightroom configuration JSON from a prompt using Ollama.
        """
        system_prompt = f"""
        You are an expert in Adobe Lightroom. Your task is to generate a JSON configuration file based on the user's request.
        The JSON file must strictly adhere to the following JSON Schema.
        Do not include any comments or extra text in the JSON output.

        Schema:
        {json.dumps(SCHEMA, indent=2)}
        """

        full_prompt = f"{prompt}\n\nGenerate the JSON configuration now."

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            "stream": False,
            "format": "json"
        }

        try:
            response = requests.post(f"{self.host}/api/chat", json=payload, timeout=60)
            response.raise_for_status()

            # Extract the JSON content from the response
            response_data = response.json()
            json_content = response_data.get("message", {}).get("content", "{}")

            return json.loads(json_content)

        except requests.exceptions.RequestException as e:
            print(f"Error communicating with Ollama: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from Ollama response: {e}")
            print(f"Raw response: {response.text}")
            return None

if __name__ == '__main__':
    client = OllamaClient()

    test_prompt = """
    被写体: 秋の屋外ポートレート（逆光）
    質感: 透明感、肌は柔らかく、空色は転びすぎない
    作風: WhiteLayer透明感系 v4 を60%相当
    制約: 肌の橙-4/彩度-6/輝度+4、空の青は彩度-8/輝度-6、トーンカーブはS弱
    """

    config = client.generate_config(test_prompt)

    if config:
        print("Generated Config:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        # Basic validation
        from jsonschema import validate
        try:
            validate(instance=config, schema=SCHEMA)
            print("\nValidation successful!")
        except Exception as e:
            print(f"\nValidation failed: {e}")
