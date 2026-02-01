import pickle
import numpy as np
import logging

from recommend.models import model_to_ckpt, model_to_cls

logger = logging.getLogger(__name__)

class RecommenderWrapper:
    def __init__(self) -> None:
        self.model_name = None
        self.model = None
    
    def set_model(self, new_model):
        """Set the recommendation model. Always reload if switching models."""
        # Always reload if switching to a different model
        if self.model_name != new_model:
            logger.info(f"Switching model from {self.model_name} to {new_model}")
            self.model_name = new_model
            
            # Create new model instance
            if new_model not in model_to_cls:
                raise KeyError(f"Model {new_model} not found in model registry")
            
            self.model = model_to_cls[new_model]()
            
            # Restore model from checkpoint
            checkpoint_path = model_to_ckpt[new_model]
            logger.info(f"Loading checkpoint from: {checkpoint_path}")
            
            # Check if checkpoint file exists
            import os
            if not os.path.exists(checkpoint_path):
                raise FileNotFoundError(
                    f"Checkpoint file not found: {checkpoint_path}. "
                    f"Please train the {new_model} model first using: "
                    f"python fit_offline.py --model {new_model} --save_dir recommend/ckpt"
                )
            
            self.model.restore(checkpoint_path)
            logger.info(f"Successfully loaded model: {new_model}")
        else:
            logger.debug(f"Model {new_model} already loaded, skipping reload")
        
    def recommend(self, user_context):
        """Get recommendations using the current model"""
        if self.model is None:
            raise ValueError("No model loaded. Call set_model() first.")
        
        if self.model_name is None:
            raise ValueError("Model name not set. Call set_model() first.")
        
        logger.info(f"Generating recommendations using model: {self.model_name}, context: {user_context}")
        
        # user context to user vec
        user_item_ids = [int(i) for i in user_context]

        # recommend
        recommendation = self.model.recommend(user_item_ids)
        
        logger.info(f"Model {self.model_name} returned {len(recommendation) if recommendation else 0} recommendations")

        return recommendation
