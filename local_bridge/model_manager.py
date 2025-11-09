"""
Multi-Model Management System

Manages multiple LLM models for the Junmai AutoDev system, including:
- Model list management
- Model switching
- Model download
- Model metadata management
- Performance tracking per model

Requirements: 18.1, 18.2, 18.3, 18.4
"""

import logging
import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ModelPurpose(Enum):
    """Model purpose categories."""
    SPEED = "speed"  # Fast inference, lower quality
    BALANCED = "balanced"  # Balance between speed and quality
    QUALITY = "quality"  # High quality, slower inference
    SPECIALIZED = "specialized"  # Specialized tasks


@dataclass
class ModelMetadata:
    """Metadata for a model."""
    name: str
    size: str  # e.g., "8b", "13b", "70b"
    purpose: ModelPurpose
    description: str
    recommended_use: str
    min_vram_gb: float
    quantization_support: List[str]  # e.g., ["q4", "q8"]
    download_size_mb: Optional[int] = None
    installed: bool = False
    last_used: Optional[str] = None
    usage_count: int = 0
    avg_inference_time: Optional[float] = None
    success_rate: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['purpose'] = self.purpose.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ModelMetadata':
        """Create from dictionary."""
        data = data.copy()
        if 'purpose' in data and isinstance(data['purpose'], str):
            data['purpose'] = ModelPurpose(data['purpose'])
        return cls(**data)


class ModelManager:
    """
    Multi-model management system for LLM models.
    
    Features:
    - Model list management with metadata
    - Model switching
    - Model download from Ollama
    - Performance tracking per model
    - Recommended model selection
    """
    
    # Predefined model catalog
    MODEL_CATALOG = {
        "llama3.1:8b-instruct": ModelMetadata(
            name="llama3.1:8b-instruct",
            size="8b",
            purpose=ModelPurpose.BALANCED,
            description="Llama 3.1 8B Instruct - Balanced performance",
            recommended_use="General photo evaluation and tagging",
            min_vram_gb=6.0,
            quantization_support=["q4", "q8"],
            download_size_mb=4700
        ),
        "llama3.1:13b-instruct": ModelMetadata(
            name="llama3.1:13b-instruct",
            size="13b",
            purpose=ModelPurpose.QUALITY,
            description="Llama 3.1 13B Instruct - High quality",
            recommended_use="Detailed photo analysis and critique",
            min_vram_gb=8.0,
            quantization_support=["q4", "q8"],
            download_size_mb=7400
        ),
        "llama3.1:70b-instruct": ModelMetadata(
            name="llama3.1:70b-instruct",
            size="70b",
            purpose=ModelPurpose.QUALITY,
            description="Llama 3.1 70B Instruct - Highest quality",
            recommended_use="Professional photo evaluation",
            min_vram_gb=40.0,
            quantization_support=["q4", "q8"],
            download_size_mb=40000
        ),
        "mixtral:8x7b-instruct": ModelMetadata(
            name="mixtral:8x7b-instruct",
            size="8x7b",
            purpose=ModelPurpose.QUALITY,
            description="Mixtral 8x7B - Mixture of Experts",
            recommended_use="Complex photo analysis",
            min_vram_gb=24.0,
            quantization_support=["q4", "q8"],
            download_size_mb=26000
        ),
        "llama3.2:3b-instruct": ModelMetadata(
            name="llama3.2:3b-instruct",
            size="3b",
            purpose=ModelPurpose.SPEED,
            description="Llama 3.2 3B Instruct - Fast inference",
            recommended_use="Quick photo tagging and basic evaluation",
            min_vram_gb=2.0,
            quantization_support=["q4", "q8"],
            download_size_mb=2000
        ),
        "llama3.2:1b-instruct": ModelMetadata(
            name="llama3.2:1b-instruct",
            size="1b",
            purpose=ModelPurpose.SPEED,
            description="Llama 3.2 1B Instruct - Ultra-fast",
            recommended_use="Rapid batch processing",
            min_vram_gb=1.0,
            quantization_support=["q4", "q8"],
            download_size_mb=1300
        ),
    }
    
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        metadata_file: str = "data/model_metadata.json"
    ):
        """
        Initialize Model Manager.
        
        Args:
            ollama_host: Ollama server host URL
            metadata_file: Path to model metadata storage file
        """
        self.ollama_host = ollama_host
        self.metadata_file = Path(metadata_file)
        self.current_model: Optional[str] = None
        self.models: Dict[str, ModelMetadata] = {}
        
        # Load metadata
        self._load_metadata()
        
        # Sync with Ollama
        self._sync_with_ollama()
        
        logger.info(f"Model Manager initialized (host={ollama_host})")
    
    def _load_metadata(self):
        """Load model metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Load models
                    for model_name, model_data in data.get('models', {}).items():
                        self.models[model_name] = ModelMetadata.from_dict(model_data)
                    
                    # Load current model
                    self.current_model = data.get('current_model')
                    
                    logger.info(f"Loaded metadata for {len(self.models)} models")
            
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self._initialize_default_metadata()
        else:
            self._initialize_default_metadata()
    
    def _initialize_default_metadata(self):
        """Initialize with default model catalog."""
        self.models = self.MODEL_CATALOG.copy()
        self.current_model = "llama3.1:8b-instruct"
        logger.info("Initialized with default model catalog")
    
    def _save_metadata(self):
        """Save model metadata to file."""
        try:
            # Ensure directory exists
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'current_model': self.current_model,
                'models': {
                    name: metadata.to_dict()
                    for name, metadata in self.models.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("Metadata saved")
        
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _sync_with_ollama(self):
        """Sync model list with Ollama server."""
        try:
            installed_models = self.list_installed_models()
            
            # Update installed status
            for model_name in self.models:
                self.models[model_name].installed = model_name in installed_models
            
            # Add any new models found in Ollama
            for model_name in installed_models:
                if model_name not in self.models:
                    # Create basic metadata for unknown models
                    self.models[model_name] = ModelMetadata(
                        name=model_name,
                        size="unknown",
                        purpose=ModelPurpose.BALANCED,
                        description=f"Custom model: {model_name}",
                        recommended_use="General use",
                        min_vram_gb=4.0,
                        quantization_support=[],
                        installed=True
                    )
            
            self._save_metadata()
            logger.info(f"Synced with Ollama: {len(installed_models)} models installed")
        
        except Exception as e:
            logger.warning(f"Could not sync with Ollama: {e}")
    
    def list_installed_models(self) -> List[str]:
        """
        List models installed in Ollama.
        
        Returns:
            List of installed model names
        """
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('models', [])
            
            model_names = [m.get('name', '') for m in models if m.get('name')]
            
            logger.info(f"Found {len(model_names)} installed models")
            return model_names
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error listing installed models: {e}")
            return []
    
    def list_available_models(
        self,
        purpose: Optional[ModelPurpose] = None,
        max_vram_gb: Optional[float] = None,
        installed_only: bool = False
    ) -> List[ModelMetadata]:
        """
        List available models with optional filtering.
        
        Args:
            purpose: Filter by purpose (speed/balanced/quality/specialized)
            max_vram_gb: Filter by maximum VRAM requirement
            installed_only: Only show installed models
            
        Returns:
            List of model metadata
        """
        models = list(self.models.values())
        
        # Apply filters
        if purpose:
            models = [m for m in models if m.purpose == purpose]
        
        if max_vram_gb:
            models = [m for m in models if m.min_vram_gb <= max_vram_gb]
        
        if installed_only:
            models = [m for m in models if m.installed]
        
        # Sort by size (smaller first)
        size_order = {"1b": 1, "3b": 2, "8b": 3, "13b": 4, "8x7b": 5, "70b": 6, "unknown": 99}
        models.sort(key=lambda m: size_order.get(m.size, 99))
        
        return models
    
    def get_model_info(self, model_name: str) -> Optional[ModelMetadata]:
        """
        Get detailed information about a model.
        
        Args:
            model_name: Model name
            
        Returns:
            Model metadata or None if not found
        """
        return self.models.get(model_name)
    
    def get_current_model(self) -> Optional[str]:
        """
        Get currently selected model.
        
        Returns:
            Current model name or None
        """
        return self.current_model
    
    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different model.
        
        Args:
            model_name: Model name to switch to
            
        Returns:
            True if successful, False otherwise
        """
        if model_name not in self.models:
            logger.error(f"Model not found: {model_name}")
            return False
        
        model = self.models[model_name]
        
        if not model.installed:
            logger.error(f"Model not installed: {model_name}")
            return False
        
        # Update current model
        old_model = self.current_model
        self.current_model = model_name
        
        # Update last used timestamp
        model.last_used = datetime.now().isoformat()
        
        self._save_metadata()
        
        logger.info(f"Switched model: {old_model} -> {model_name}")
        return True
    
    def download_model(
        self,
        model_name: str,
        progress_callback: Optional[callable] = None
    ) -> Tuple[bool, str]:
        """
        Download a model from Ollama.
        
        Args:
            model_name: Model name to download
            progress_callback: Optional callback for progress updates
            
        Returns:
            Tuple of (success, message)
        """
        if model_name not in self.models:
            return False, f"Model not found in catalog: {model_name}"
        
        model = self.models[model_name]
        
        if model.installed:
            return True, f"Model already installed: {model_name}"
        
        try:
            logger.info(f"Starting download: {model_name}")
            
            # Call Ollama pull API
            payload = {"name": model_name}
            
            response = requests.post(
                f"{self.ollama_host}/api/pull",
                json=payload,
                stream=True,
                timeout=3600  # 1 hour timeout for large models
            )
            response.raise_for_status()
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        status = data.get('status', '')
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(data)
                        
                        # Log progress
                        if 'completed' in data and 'total' in data:
                            completed = data['completed']
                            total = data['total']
                            percent = (completed / total * 100) if total > 0 else 0
                            logger.info(f"Download progress: {percent:.1f}% ({completed}/{total} bytes)")
                        
                        # Check for completion
                        if status == 'success':
                            logger.info(f"Download complete: {model_name}")
                            break
                    
                    except json.JSONDecodeError:
                        continue
            
            # Update metadata
            model.installed = True
            self._save_metadata()
            
            # Sync to get actual model info
            self._sync_with_ollama()
            
            return True, f"Successfully downloaded: {model_name}"
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading model: {e}")
            return False, f"Download failed: {str(e)}"
    
    def delete_model(self, model_name: str) -> Tuple[bool, str]:
        """
        Delete a model from Ollama.
        
        Args:
            model_name: Model name to delete
            
        Returns:
            Tuple of (success, message)
        """
        if model_name not in self.models:
            return False, f"Model not found: {model_name}"
        
        model = self.models[model_name]
        
        if not model.installed:
            return False, f"Model not installed: {model_name}"
        
        if model_name == self.current_model:
            return False, "Cannot delete currently selected model"
        
        try:
            logger.info(f"Deleting model: {model_name}")
            
            # Call Ollama delete API
            payload = {"name": model_name}
            
            response = requests.delete(
                f"{self.ollama_host}/api/delete",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            # Update metadata
            model.installed = False
            self._save_metadata()
            
            logger.info(f"Model deleted: {model_name}")
            return True, f"Successfully deleted: {model_name}"
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting model: {e}")
            return False, f"Delete failed: {str(e)}"
    
    def record_usage(
        self,
        model_name: str,
        inference_time: float,
        success: bool
    ):
        """
        Record model usage statistics.
        
        Args:
            model_name: Model name
            inference_time: Time taken for inference (seconds)
            success: Whether inference was successful
        """
        if model_name not in self.models:
            return
        
        model = self.models[model_name]
        
        # Update usage count
        model.usage_count += 1
        
        # Update last used
        model.last_used = datetime.now().isoformat()
        
        # Update average inference time
        if success:
            if model.avg_inference_time is None:
                model.avg_inference_time = inference_time
            else:
                # Exponential moving average
                alpha = 0.2
                model.avg_inference_time = (
                    alpha * inference_time +
                    (1 - alpha) * model.avg_inference_time
                )
        
        # Update success rate
        if model.success_rate is None:
            model.success_rate = 1.0 if success else 0.0
        else:
            # Update success rate
            total_attempts = model.usage_count
            successful_attempts = int(model.success_rate * (total_attempts - 1)) + (1 if success else 0)
            model.success_rate = successful_attempts / total_attempts
        
        self._save_metadata()
    
    def get_model_statistics(self, model_name: str) -> Optional[Dict]:
        """
        Get usage statistics for a model.
        
        Args:
            model_name: Model name
            
        Returns:
            Statistics dictionary or None if not found
        """
        if model_name not in self.models:
            return None
        
        model = self.models[model_name]
        
        return {
            'name': model.name,
            'usage_count': model.usage_count,
            'last_used': model.last_used,
            'avg_inference_time': model.avg_inference_time,
            'success_rate': model.success_rate,
            'installed': model.installed
        }
    
    def get_all_statistics(self) -> Dict[str, Dict]:
        """
        Get usage statistics for all models.
        
        Returns:
            Dictionary mapping model names to statistics
        """
        return {
            name: self.get_model_statistics(name)
            for name in self.models
            if self.get_model_statistics(name) is not None
        }
    
    def recommend_model(
        self,
        available_vram_gb: float,
        priority: str = "balanced"  # "speed", "balanced", "quality"
    ) -> Optional[str]:
        """
        Recommend a model based on available resources and priority.
        
        Args:
            available_vram_gb: Available VRAM in GB
            priority: Priority ("speed", "balanced", "quality")
            
        Returns:
            Recommended model name or None
        """
        # Map priority to purpose
        purpose_map = {
            "speed": ModelPurpose.SPEED,
            "balanced": ModelPurpose.BALANCED,
            "quality": ModelPurpose.QUALITY
        }
        
        purpose = purpose_map.get(priority, ModelPurpose.BALANCED)
        
        # Get models that fit in VRAM and match purpose
        candidates = self.list_available_models(
            purpose=purpose,
            max_vram_gb=available_vram_gb,
            installed_only=True
        )
        
        if not candidates:
            # Fallback: get any installed model that fits
            candidates = self.list_available_models(
                max_vram_gb=available_vram_gb,
                installed_only=True
            )
        
        if not candidates:
            logger.warning(f"No suitable model found for {available_vram_gb}GB VRAM")
            return None
        
        # Select best candidate based on performance stats
        best_model = None
        best_score = -1
        
        for model in candidates:
            score = 0
            
            # Prefer models with good success rate
            if model.success_rate:
                score += model.success_rate * 50
            
            # Prefer faster models for speed priority
            if priority == "speed" and model.avg_inference_time:
                score += (1.0 / model.avg_inference_time) * 20
            
            # Prefer models with more usage (proven)
            if model.usage_count > 0:
                score += min(model.usage_count / 100, 10)
            
            # Prefer larger models for quality priority
            if priority == "quality":
                size_bonus = {"1b": 0, "3b": 5, "8b": 10, "13b": 15, "8x7b": 18, "70b": 20}
                score += size_bonus.get(model.size, 0)
            
            if score > best_score:
                best_score = score
                best_model = model.name
        
        logger.info(f"Recommended model: {best_model} (priority={priority}, vram={available_vram_gb}GB)")
        return best_model
    
    def check_model_compatibility(
        self,
        model_name: str,
        available_vram_gb: float
    ) -> Tuple[bool, str]:
        """
        Check if a model is compatible with available resources.
        
        Args:
            model_name: Model name
            available_vram_gb: Available VRAM in GB
            
        Returns:
            Tuple of (compatible, message)
        """
        if model_name not in self.models:
            return False, f"Model not found: {model_name}"
        
        model = self.models[model_name]
        
        if model.min_vram_gb > available_vram_gb:
            return False, (
                f"Insufficient VRAM: {model_name} requires {model.min_vram_gb}GB, "
                f"but only {available_vram_gb}GB available"
            )
        
        return True, f"Model compatible: {model_name}"
    
    def export_metadata(self, output_file: str):
        """
        Export model metadata to a file.
        
        Args:
            output_file: Output file path
        """
        try:
            data = {
                'current_model': self.current_model,
                'models': {
                    name: metadata.to_dict()
                    for name, metadata in self.models.items()
                },
                'exported_at': datetime.now().isoformat()
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Metadata exported to: {output_file}")
        
        except Exception as e:
            logger.error(f"Error exporting metadata: {e}")
    
    def import_metadata(self, input_file: str):
        """
        Import model metadata from a file.
        
        Args:
            input_file: Input file path
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Import models
            for model_name, model_data in data.get('models', {}).items():
                self.models[model_name] = ModelMetadata.from_dict(model_data)
            
            # Import current model if valid
            current = data.get('current_model')
            if current and current in self.models:
                self.current_model = current
            
            self._save_metadata()
            logger.info(f"Metadata imported from: {input_file}")
        
        except Exception as e:
            logger.error(f"Error importing metadata: {e}")


def main():
    """Example usage of Model Manager."""
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    manager = ModelManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            print("\n" + "=" * 60)
            print("AVAILABLE MODELS")
            print("=" * 60)
            
            models = manager.list_available_models()
            for model in models:
                status = "✓ Installed" if model.installed else "✗ Not installed"
                print(f"\n{model.name} ({model.size}) - {status}")
                print(f"  Purpose: {model.purpose.value}")
                print(f"  Description: {model.description}")
                print(f"  Min VRAM: {model.min_vram_gb}GB")
                print(f"  Recommended: {model.recommended_use}")
                if model.usage_count > 0:
                    print(f"  Usage: {model.usage_count} times")
                    if model.avg_inference_time:
                        print(f"  Avg Time: {model.avg_inference_time:.2f}s")
                    if model.success_rate:
                        print(f"  Success Rate: {model.success_rate*100:.1f}%")
        
        elif command == "current":
            current = manager.get_current_model()
            print(f"\nCurrent model: {current}")
            
            if current:
                info = manager.get_model_info(current)
                if info:
                    print(f"  Purpose: {info.purpose.value}")
                    print(f"  Description: {info.description}")
        
        elif command == "recommend":
            vram = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
            priority = sys.argv[3] if len(sys.argv) > 3 else "balanced"
            
            recommended = manager.recommend_model(vram, priority)
            print(f"\nRecommended model for {vram}GB VRAM ({priority} priority): {recommended}")
        
        elif command == "stats":
            print("\n" + "=" * 60)
            print("MODEL STATISTICS")
            print("=" * 60)
            
            stats = manager.get_all_statistics()
            for name, stat in stats.items():
                if stat['usage_count'] > 0:
                    print(f"\n{name}:")
                    print(f"  Usage Count: {stat['usage_count']}")
                    print(f"  Last Used: {stat['last_used']}")
                    if stat['avg_inference_time']:
                        print(f"  Avg Time: {stat['avg_inference_time']:.2f}s")
                    if stat['success_rate']:
                        print(f"  Success Rate: {stat['success_rate']*100:.1f}%")
    
    else:
        print("Usage:")
        print("  python model_manager.py list              - List all models")
        print("  python model_manager.py current            - Show current model")
        print("  python model_manager.py recommend <vram> <priority>  - Recommend model")
        print("  python model_manager.py stats              - Show statistics")


if __name__ == '__main__':
    main()
