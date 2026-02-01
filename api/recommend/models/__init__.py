import os

from recommend.models.EASE import EASE
from recommend.models.ItemKNN import ItemKNN

# Import neural models only if PyTorch is available
# Use lazy imports to prevent module-level import errors
NEURAL_MODELS_AVAILABLE = False
NeuralMF = None
DeepFM = None

try:
    import torch
    # Only import if torch is available
    from recommend.models.NeuralMF import NeuralMF
    from recommend.models.DeepFM import DeepFM
    NEURAL_MODELS_AVAILABLE = True
except ImportError:
    # PyTorch not available - create placeholder classes that raise error on instantiation
    NEURAL_MODELS_AVAILABLE = False
    
    class NeuralMFPlaceholder:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "PyTorch is not installed. NeuralMF requires torch. "
                "Install with: pip install torch"
            )
    
    class DeepFMPlaceholder:
        def __init__(self, *args, **kwargs):
            raise ImportError(
                "PyTorch is not installed. DeepFM requires torch. "
                "Install with: pip install torch"
            )
    
    NeuralMF = NeuralMFPlaceholder
    DeepFM = DeepFMPlaceholder

BASE_DIR = 'recommend/ckpt'

model_to_ckpt = {
    'EASE': os.path.join(BASE_DIR, 'EASE_100.npy'),
    'ItemKNN': os.path.join(BASE_DIR, 'ItemKNN_100.npz'),
    'NeuralMF': os.path.join(BASE_DIR, 'NeuralMF_emb64.pth'),
    'DeepFM': os.path.join(BASE_DIR, 'DeepFM_emb64.pth')
}

model_to_cls = {
    'EASE': EASE,
    'ItemKNN': ItemKNN,
}

# Add neural models only if available
if NEURAL_MODELS_AVAILABLE:
    model_to_cls['NeuralMF'] = NeuralMF
    model_to_cls['DeepFM'] = DeepFM