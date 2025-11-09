import requests
import json
import logging
from typing import Optional, Dict, List
from schema import SCHEMA

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama client with support for model quantization and performance tracking.
    
    Supports:
    - 4-bit and 8-bit quantization for reduced memory usage
    - Model switching and management
    - Performance metrics tracking
    """
    
    def __init__(
        self,
        host: str = 'http://localhost:11434',
        enable_quantization: bool = False,
        quantization_bits: int = 8
    ):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama server host URL
            enable_quantization: Enable model quantization (default: False)
            quantization_bits: Quantization bits (4 or 8, default: 8)
        """
        self.host = host
        self.enable_quantization = enable_quantization
        self.quantization_bits = quantization_bits
        self.performance_stats = {}
        
        logger.info(
            f"Ollama client initialized (host={host}, "
            f"quantization={'enabled' if enable_quantization else 'disabled'}, "
            f"bits={quantization_bits if enable_quantization else 'N/A'})"
        )

    def _get_quantized_model_name(self, model: str) -> str:
        """
        Get quantized model name based on settings.
        
        Args:
            model: Base model name (e.g., "llama3.1:8b-instruct")
            
        Returns:
            Quantized model name if quantization is enabled, otherwise original name
        """
        if not self.enable_quantization:
            return model
        
        # Check if model already has quantization suffix
        if any(suffix in model for suffix in ['-q4', '-q8', ':q4', ':q8']):
            return model
        
        # Add quantization suffix
        if ':' in model:
            base, tag = model.rsplit(':', 1)
            return f"{base}:q{self.quantization_bits}_{tag}"
        else:
            return f"{model}:q{self.quantization_bits}"
    
    def set_quantization(self, enable: bool, bits: int = 8):
        """
        Enable or disable model quantization.
        
        Args:
            enable: Enable quantization
            bits: Quantization bits (4 or 8)
        """
        if bits not in [4, 8]:
            raise ValueError("Quantization bits must be 4 or 8")
        
        self.enable_quantization = enable
        self.quantization_bits = bits
        
        logger.info(
            f"Quantization {'enabled' if enable else 'disabled'} "
            f"(bits={bits if enable else 'N/A'})"
        )
    
    def get_quantization_settings(self) -> Dict:
        """
        Get current quantization settings.
        
        Returns:
            Dictionary with quantization settings
        """
        return {
            'enabled': self.enable_quantization,
            'bits': self.quantization_bits if self.enable_quantization else None,
            'memory_reduction': self._estimate_memory_reduction()
        }
    
    def _estimate_memory_reduction(self) -> Optional[str]:
        """
        Estimate memory reduction from quantization.
        
        Returns:
            Estimated memory reduction percentage as string
        """
        if not self.enable_quantization:
            return None
        
        if self.quantization_bits == 4:
            return "~75% (4-bit quantization)"
        elif self.quantization_bits == 8:
            return "~50% (8-bit quantization)"
        
        return None
    
    def generate_config(self, prompt, model="llama3.1:8b-instruct"):
        """
        Generates a Lightroom configuration JSON from a prompt using Ollama.
        
        Args:
            prompt: User prompt for configuration generation
            model: Model name to use
            
        Returns:
            Generated configuration dictionary or None on error
        """
        # Apply quantization if enabled
        model_name = self._get_quantized_model_name(model)
        
        system_prompt = f"""
        You are an expert in Adobe Lightroom. Your task is to generate a JSON configuration file based on the user's request.
        The JSON file must strictly adhere to the following JSON Schema.
        Do not include any comments or extra text in the JSON output.

        Schema:
        {json.dumps(SCHEMA, indent=2)}
        """

        full_prompt = f"{prompt}\n\nGenerate the JSON configuration now."

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            "stream": False,
            "format": "json"
        }

        try:
            import time
            start_time = time.time()
            
            response = requests.post(f"{self.host}/api/chat", json=payload, timeout=60)
            response.raise_for_status()

            # Extract the JSON content from the response
            response_data = response.json()
            json_content = response_data.get("message", {}).get("content", "{}")
            
            elapsed_time = time.time() - start_time
            
            # Track performance
            self._record_performance(model_name, elapsed_time, success=True)
            
            logger.info(f"Config generated in {elapsed_time:.2f}s using {model_name}")

            return json.loads(json_content)

        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama: {e}")
            self._record_performance(model_name, 0, success=False)
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from Ollama response: {e}")
            self._record_performance(model_name, 0, success=False)
            return None

    def generate(
        self,
        model: str,
        prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 500
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            model: Model name to use
            prompt: Input prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        # Apply quantization if enabled
        model_name = self._get_quantized_model_name(model)
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            import time
            start_time = time.time()
            
            response = requests.post(f"{self.host}/api/generate", json=payload, timeout=120)
            response.raise_for_status()
            
            response_data = response.json()
            generated_text = response_data.get("response", "")
            
            elapsed_time = time.time() - start_time
            
            # Track performance
            self._record_performance(model_name, elapsed_time, success=True)
            
            logger.info(f"Text generated in {elapsed_time:.2f}s using {model_name}")
            
            return generated_text
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama: {e}")
            self._record_performance(model_name, 0, success=False)
            raise
    
    def _record_performance(self, model: str, elapsed_time: float, success: bool):
        """
        Record performance metrics for a model.
        
        Args:
            model: Model name
            elapsed_time: Time taken for generation
            success: Whether generation was successful
        """
        if model not in self.performance_stats:
            self.performance_stats[model] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0
            }
        
        stats = self.performance_stats[model]
        stats['total_calls'] += 1
        
        if success:
            stats['successful_calls'] += 1
            stats['total_time'] += elapsed_time
            stats['avg_time'] = stats['total_time'] / stats['successful_calls']
            stats['min_time'] = min(stats['min_time'], elapsed_time)
            stats['max_time'] = max(stats['max_time'], elapsed_time)
        else:
            stats['failed_calls'] += 1
    
    def get_performance_stats(self, model: Optional[str] = None) -> Dict:
        """
        Get performance statistics.
        
        Args:
            model: Specific model name, or None for all models
            
        Returns:
            Performance statistics dictionary
        """
        if model:
            return self.performance_stats.get(model, {})
        return self.performance_stats.copy()
    
    def compare_quantization_performance(
        self,
        model: str,
        prompt: str,
        test_iterations: int = 3
    ) -> Dict:
        """
        Compare performance between non-quantized and quantized models.
        
        Args:
            model: Base model name
            prompt: Test prompt
            test_iterations: Number of test iterations
            
        Returns:
            Comparison results dictionary
        """
        results = {
            'model': model,
            'iterations': test_iterations,
            'non_quantized': {},
            'quantized_8bit': {},
            'quantized_4bit': {}
        }
        
        # Test non-quantized
        logger.info(f"Testing non-quantized model: {model}")
        original_setting = self.enable_quantization
        self.enable_quantization = False
        
        times = []
        for i in range(test_iterations):
            try:
                import time
                start = time.time()
                self.generate(model, prompt, temperature=0.2, max_tokens=100)
                elapsed = time.time() - start
                times.append(elapsed)
                logger.info(f"  Iteration {i+1}: {elapsed:.2f}s")
            except Exception as e:
                logger.error(f"  Iteration {i+1} failed: {e}")
        
        if times:
            results['non_quantized'] = {
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'success_rate': len(times) / test_iterations
            }
        
        # Test 8-bit quantization
        logger.info(f"Testing 8-bit quantized model: {model}")
        self.enable_quantization = True
        self.quantization_bits = 8
        
        times = []
        for i in range(test_iterations):
            try:
                import time
                start = time.time()
                self.generate(model, prompt, temperature=0.2, max_tokens=100)
                elapsed = time.time() - start
                times.append(elapsed)
                logger.info(f"  Iteration {i+1}: {elapsed:.2f}s")
            except Exception as e:
                logger.error(f"  Iteration {i+1} failed: {e}")
        
        if times:
            results['quantized_8bit'] = {
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'success_rate': len(times) / test_iterations,
                'speedup': results['non_quantized']['avg_time'] / (sum(times) / len(times)) if results['non_quantized'] else 1.0
            }
        
        # Test 4-bit quantization
        logger.info(f"Testing 4-bit quantized model: {model}")
        self.quantization_bits = 4
        
        times = []
        for i in range(test_iterations):
            try:
                import time
                start = time.time()
                self.generate(model, prompt, temperature=0.2, max_tokens=100)
                elapsed = time.time() - start
                times.append(elapsed)
                logger.info(f"  Iteration {i+1}: {elapsed:.2f}s")
            except Exception as e:
                logger.error(f"  Iteration {i+1} failed: {e}")
        
        if times:
            results['quantized_4bit'] = {
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'success_rate': len(times) / test_iterations,
                'speedup': results['non_quantized']['avg_time'] / (sum(times) / len(times)) if results['non_quantized'] else 1.0
            }
        
        # Restore original setting
        self.enable_quantization = original_setting
        
        return results
    
    def list_available_models(self) -> List[Dict]:
        """
        List available models from Ollama.
        
        Returns:
            List of model information dictionaries
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('models', [])
            
            logger.info(f"Found {len(models)} available models")
            return models
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def check_model_exists(self, model: str) -> bool:
        """
        Check if a model exists in Ollama.
        
        Args:
            model: Model name to check
            
        Returns:
            True if model exists, False otherwise
        """
        models = self.list_available_models()
        model_names = [m.get('name', '') for m in models]
        
        # Check both exact match and quantized variants
        quantized_name = self._get_quantized_model_name(model)
        
        return model in model_names or quantized_name in model_names


if __name__ == '__main__':
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    client = OllamaClient()

    if len(sys.argv) > 1 and sys.argv[1] == '--compare':
        # Performance comparison mode
        print("=" * 60)
        print("QUANTIZATION PERFORMANCE COMPARISON")
        print("=" * 60)
        
        test_prompt = "Explain the concept of quantization in machine learning in 50 words."
        
        results = client.compare_quantization_performance(
            model="llama3.1:8b-instruct",
            prompt=test_prompt,
            test_iterations=3
        )
        
        print(f"\nModel: {results['model']}")
        print(f"Iterations: {results['iterations']}\n")
        
        if results['non_quantized']:
            print("Non-Quantized:")
            print(f"  Avg Time: {results['non_quantized']['avg_time']:.2f}s")
            print(f"  Min Time: {results['non_quantized']['min_time']:.2f}s")
            print(f"  Max Time: {results['non_quantized']['max_time']:.2f}s")
            print(f"  Success Rate: {results['non_quantized']['success_rate']*100:.1f}%\n")
        
        if results['quantized_8bit']:
            print("8-bit Quantized:")
            print(f"  Avg Time: {results['quantized_8bit']['avg_time']:.2f}s")
            print(f"  Min Time: {results['quantized_8bit']['min_time']:.2f}s")
            print(f"  Max Time: {results['quantized_8bit']['max_time']:.2f}s")
            print(f"  Success Rate: {results['quantized_8bit']['success_rate']*100:.1f}%")
            print(f"  Speedup: {results['quantized_8bit']['speedup']:.2f}x\n")
        
        if results['quantized_4bit']:
            print("4-bit Quantized:")
            print(f"  Avg Time: {results['quantized_4bit']['avg_time']:.2f}s")
            print(f"  Min Time: {results['quantized_4bit']['min_time']:.2f}s")
            print(f"  Max Time: {results['quantized_4bit']['max_time']:.2f}s")
            print(f"  Success Rate: {results['quantized_4bit']['success_rate']*100:.1f}%")
            print(f"  Speedup: {results['quantized_4bit']['speedup']:.2f}x\n")
        
    else:
        # Standard config generation mode
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
