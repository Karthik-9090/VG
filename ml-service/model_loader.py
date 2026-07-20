"""
model_loader.py

Singleton pattern for loading and managing the Lasso production model.
Supports model versioning and graceful error handling.

Usage:
  from model_loader import ModelLoader
  model_loader = ModelLoader()
  model = model_loader.get_model()
  version = model_loader.get_version()
"""

import pickle
import json
import os
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Singleton pattern for loading and managing the Lasso production model.
    
    Features:
    - Loads model once on startup (lazy loading)
    - Singleton pattern (single instance across application)
    - Version management support
    - Graceful error handling with fallback
    - Caching for performance
    """
    
    _instance = None
    _model = None
    _metadata = None
    _loaded = False
    _error = None
    
    # Determine paths relative to workspace root and container runtime
    _WORKSPACE_ROOT = str(Path(__file__).parent.parent)
    _APP_ROOT = str(Path(__file__).parent)
    _MODEL_CANDIDATES = [
        os.path.join(_WORKSPACE_ROOT, "models", "production_lasso.pkl"),
        os.path.join(_APP_ROOT, "models", "production_lasso.pkl"),
        os.path.join(_APP_ROOT, "production_lasso.pkl"),
        os.path.join("/models", "production_lasso.pkl"),
    ]
    MODEL_PATH = None
    METADATA_PATH = os.path.join(_WORKSPACE_ROOT, "production_metrics.json")
    
    def __new__(cls):
        """Singleton pattern - ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(ModelLoader, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the loader on first instantiation."""
        logger.info("ModelLoader initializing...")
        self._load_model()
    
    def _load_model(self):
        """Load the production model from disk."""
        try:
            # Resolve the first existing model file from the runtime candidates
            self.MODEL_PATH = next((p for p in self._MODEL_CANDIDATES if os.path.exists(p)), None)
            if not self.MODEL_PATH:
                raise FileNotFoundError(f"Model file not found in any expected location: {self._MODEL_CANDIDATES}")
            
            # Load model
            logger.info(f"Loading model from {self.MODEL_PATH}...")
            with open(self.MODEL_PATH, 'rb') as f:
                self._model = pickle.load(f)
            
            # Load metadata
            if os.path.exists(self.METADATA_PATH):
                logger.info(f"Loading metadata from {self.METADATA_PATH}...")
                with open(self.METADATA_PATH, 'r') as f:
                    self._metadata = json.load(f)
            else:
                logger.warning(f"Metadata file not found: {self.METADATA_PATH}")
                self._metadata = {
                    'model_version': 'v1.0',
                    'deployment_date': datetime.now().isoformat(),
                    'model_type': 'Lasso Regression'
                }
            
            self._loaded = True
            self._error = None
            logger.info(f"[OK] Model loaded successfully (version: {self.get_version()})")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to load model: {str(e)}")
            self._model = None
            self._loaded = False
            self._error = str(e)
            raise
    
    def get_model(self):
        """
        Get the loaded Lasso model.
        
        Returns:
            The Lasso regression model object, or None if loading failed.
            
        Raises:
            RuntimeError if model failed to load.
        """
        if self._error:
            raise RuntimeError(f"Model failed to load: {self._error}")
        
        if not self._loaded or self._model is None:
            raise RuntimeError("Model is not loaded")
        
        return self._model
    
    def get_version(self):
        """Get the model version string."""
        if self._metadata:
            return self._metadata.get('model_version', 'unknown')
        return 'unknown'
    
    def get_metadata(self):
        """Get complete model metadata."""
        if self._metadata:
            return self._metadata.copy()
        return {}
    
    def is_loaded(self):
        """Check if model is successfully loaded."""
        return self._loaded and self._model is not None
    
    def get_status(self):
        """Get detailed status information."""
        return {
            'loaded': self._loaded,
            'version': self.get_version(),
            'model_type': self._metadata.get('model_type', 'unknown') if self._metadata else 'unknown',
            'deployment_date': self._metadata.get('deployment_date', None) if self._metadata else None,
            'error': self._error,
            'model_file': self.MODEL_PATH,
            'file_exists': os.path.exists(self.MODEL_PATH) if self.MODEL_PATH else False
        }
    
    def get_features(self):
        """Get list of features the model expects."""
        if self._metadata and 'features' in self._metadata:
            return self._metadata['features']
        return None
    
    def get_training_metrics(self):
        """Get training metrics from metadata."""
        if self._metadata and 'training_metrics' in self._metadata:
            return self._metadata['training_metrics']
        return None


# Application-wide model loader instance
_model_loader = None


def get_model_loader():
    """Get or create the singleton model loader instance."""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader


# Convenience functions for direct access
def load_model():
    """Load and return the production model."""
    loader = get_model_loader()
    return loader.get_model()


def get_model_version():
    """Get the model version."""
    loader = get_model_loader()
    return loader.get_version()


def is_model_loaded():
    """Check if model is loaded."""
    loader = get_model_loader()
    return loader.is_loaded()


def get_model_status():
    """Get detailed model status."""
    loader = get_model_loader()
    return loader.get_status()
