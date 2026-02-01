"""
Deep Factorization Machine Model
Implements DeepFM using PyTorch for recommendation systems
"""
import os
import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm

class DeepFMDataset(Dataset):
    """Dataset for DeepFM training"""
    def __init__(self, train_matrix):
        self.train_matrix = train_matrix
        # Extract positive interactions
        users, items = train_matrix.nonzero()
        self.users = users.astype(np.int64)
        self.items = items.astype(np.int64)
        self.labels = np.ones(len(users), dtype=np.float32)
        
    def __len__(self):
        return len(self.users)
    
    def __getitem__(self, idx):
        return self.users[idx], self.items[idx], self.labels[idx]

class FMComponent(nn.Module):
    """Factorization Machine component"""
    def __init__(self, num_users, num_items, embedding_dim):
        super(FMComponent, self).__init__()
        self.embedding_dim = embedding_dim
        
        # User and item embeddings
        self.user_embedding = nn.Embedding(num_users, embedding_dim)
        self.item_embedding = nn.Embedding(num_items, embedding_dim)
        
        # Linear layer for first-order interactions
        self.linear = nn.Linear(2, 1)  # 2 features: user and item
        
        # Initialize embeddings
        nn.init.normal_(self.user_embedding.weight, std=0.01)
        nn.init.normal_(self.item_embedding.weight, std=0.01)
        
    def forward(self, user_ids, item_ids):
        # Get embeddings
        user_emb = self.user_embedding(user_ids)  # [batch_size, embedding_dim]
        item_emb = self.item_embedding(item_ids)  # [batch_size, embedding_dim]
        
        # First-order interactions (linear part)
        # We'll use a simple approach: sum of embeddings
        first_order = user_emb.sum(dim=1, keepdim=True) + item_emb.sum(dim=1, keepdim=True)
        
        # Second-order interactions (FM part)
        # (sum of embeddings)^2 - sum of (embeddings^2)
        sum_square = (user_emb + item_emb).pow(2).sum(dim=1, keepdim=True)
        square_sum = (user_emb.pow(2) + item_emb.pow(2)).sum(dim=1, keepdim=True)
        second_order = 0.5 * (sum_square - square_sum)
        
        return first_order + second_order

class DeepComponent(nn.Module):
    """Deep neural network component"""
    def __init__(self, input_dim, hidden_dims=[128, 64], dropout=0.2):
        super(DeepComponent, self).__init__()
        layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
            prev_dim = hidden_dim
        self.mlp = nn.Sequential(*layers)
        
    def forward(self, x):
        return self.mlp(x)

class DeepFMModel(nn.Module):
    """Deep Factorization Machine Model"""
    def __init__(self, num_users, num_items, embedding_dim=64, 
                 deep_hidden_dims=[128, 64], dropout=0.2):
        super(DeepFMModel, self).__init__()
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        
        # FM component
        self.fm = FMComponent(num_users, num_items, embedding_dim)
        
        # Deep component
        deep_input_dim = embedding_dim * 2  # Concatenated user and item embeddings
        self.deep = DeepComponent(deep_input_dim, deep_hidden_dims, dropout)
        
        # Output layer
        self.output = nn.Linear(deep_hidden_dims[-1] + 1, 1)  # +1 for FM output
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, user_ids, item_ids):
        # FM component output
        fm_output = self.fm(user_ids, item_ids)  # [batch_size, 1]
        
        # Deep component input: concatenated embeddings
        user_emb = self.fm.user_embedding(user_ids)
        item_emb = self.fm.item_embedding(item_ids)
        deep_input = torch.cat([user_emb, item_emb], dim=1)  # [batch_size, embedding_dim*2]
        
        # Deep component output
        deep_output = self.deep(deep_input)  # [batch_size, hidden_dim]
        
        # Concatenate FM and Deep outputs
        concat_output = torch.cat([fm_output, deep_output], dim=1)  # [batch_size, hidden_dim+1]
        
        # Final output
        output = self.output(concat_output)
        return self.sigmoid(output).squeeze()

class DeepFM:
    """
    Deep Factorization Machine model for recommendation systems.
    Combines factorization machines (for low-order interactions) with 
    deep neural networks (for high-order interactions).
    """
    
    def __init__(self, embedding_dim=64, deep_hidden_dims=[128, 64], dropout=0.2,
                 batch_size=256, epochs=20, learning_rate=0.001, device=None):
        self.embedding_dim = embedding_dim
        self.deep_hidden_dims = deep_hidden_dims
        self.dropout = dropout
        self.batch_size = batch_size
        self.epochs = epochs
        self.learning_rate = learning_rate
        
        # Set device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = device
            
        self.num_users = 0
        self.num_items = 0
        self.model = None
        self.model_loaded = False
        
    @property
    def save_filename(self):
        return f'DeepFM_emb{self.embedding_dim}.pth'
    
    def fit(self, train_matrix, save_path):
        """Train the DeepFM model"""
        self.num_users, self.num_items = train_matrix.shape
        
        print(f"Training DeepFM: {self.num_users} users, {self.num_items} items")
        print(f"Device: {self.device}")
        
        # Create dataset and dataloader
        dataset = DeepFMDataset(train_matrix)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, num_workers=0)
        
        # Initialize model
        self.model = DeepFMModel(
            self.num_users,
            self.num_items,
            self.embedding_dim,
            self.deep_hidden_dims,
            self.dropout
        ).to(self.device)
        
        # Loss and optimizer
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Training loop
        self.model.train()
        for epoch in range(self.epochs):
            total_loss = 0
            num_batches = 0
            
            for batch_users, batch_items, batch_labels in tqdm(dataloader, desc=f"Epoch {epoch+1}/{self.epochs}"):
                batch_users = batch_users.to(self.device)
                batch_items = batch_items.to(self.device)
                batch_labels = batch_labels.to(self.device)
                
                optimizer.zero_grad()
                predictions = self.model(batch_users, batch_items)
                loss = criterion(predictions, batch_labels)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                num_batches += 1
            
            avg_loss = total_loss / num_batches if num_batches > 0 else 0
            print(f"Epoch {epoch+1}/{self.epochs}, Average Loss: {avg_loss:.4f}")
        
        # Save model
        self.save(save_path)
        print(f"Model saved to {save_path}")
        
        # BUG FIX: Set model_loaded to True after training completes
        # This allows predict() to be called immediately after fit()
        self.model_loaded = True
        self.model.eval()  # Set to evaluation mode
    
    def predict(self, rating_matrix):
        """Predict scores for all user-item pairs"""
        if not self.model_loaded:
            raise ValueError("Model not loaded. Call restore() first.")
        
        self.model.eval()
        num_users, num_items = rating_matrix.shape
        
        predictions = np.zeros((num_users, num_items))
        
        with torch.no_grad():
            # Process in batches to avoid memory issues
            batch_size = 1000
            all_items = np.arange(num_items)
            
            for u in tqdm(range(num_users), desc="Predicting"):
                user_tensor = torch.LongTensor([u] * num_items).to(self.device)
                item_tensor = torch.LongTensor(all_items).to(self.device)
                
                # Get predictions in batches
                for i in range(0, num_items, batch_size):
                    end_idx = min(i + batch_size, num_items)
                    batch_items = item_tensor[i:end_idx]
                    batch_users = user_tensor[i:end_idx]
                    
                    batch_pred = self.model(batch_users, batch_items)
                    predictions[u, i:end_idx] = batch_pred.cpu().numpy()
        
        # Mask out items user has already interacted with
        predictions[rating_matrix.nonzero()] = float('-inf')
        
        return predictions
    
    def recommend(self, user_context, top_k=10):
        """
        Generate recommendations for user based on their item history
        
        Args:
            user_context: List of item IDs the user has interacted with
            top_k: Number of recommendations to return
            
        Returns:
            List of recommended item IDs
        """
        if not self.model_loaded:
            raise ValueError("Model not loaded. Call restore() first.")
        
        if len(user_context) == 0:
            return []
        
        self.model.eval()
        
        # Create a dummy user (we'll use user 0 as proxy for new users)
        user_id = 0
        
        # Get predictions for all items
        all_items = torch.LongTensor(np.arange(self.num_items)).to(self.device)
        user_tensor = torch.LongTensor([user_id] * self.num_items).to(self.device)
        
        with torch.no_grad():
            # Process in batches
            batch_size = 1000
            scores = np.zeros(self.num_items)
            
            for i in range(0, self.num_items, batch_size):
                end_idx = min(i + batch_size, self.num_items)
                batch_items = all_items[i:end_idx]
                batch_users = user_tensor[i:end_idx]
                
                batch_scores = self.model(batch_users, batch_items)
                scores[i:end_idx] = batch_scores.cpu().numpy()
        
        # Mask out items user has already seen
        scores[user_context] = float('-inf')
        
        # Get top-k items
        top_k_indices = np.argpartition(-scores, top_k)[:top_k]
        top_k_indices = top_k_indices[np.argsort(-scores[top_k_indices])]
        
        return top_k_indices.tolist()
    
    def save(self, save_dir):
        """Save model to disk"""
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, self.save_filename)
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'num_users': self.num_users,
            'num_items': self.num_items,
            'embedding_dim': self.embedding_dim,
            'deep_hidden_dims': self.deep_hidden_dims,
            'dropout': self.dropout
        }, save_path)
    
    def restore(self, ckpt):
        """Restore model from checkpoint"""
        if not os.path.exists(ckpt):
            raise FileNotFoundError(
                f"DeepFM checkpoint file not found: {ckpt}\n"
                f"Please train the model first using fit_offline.py or ensure the checkpoint file exists."
            )
        
        checkpoint = torch.load(ckpt, map_location=self.device)
        
        self.num_users = checkpoint['num_users']
        self.num_items = checkpoint['num_items']
        self.embedding_dim = checkpoint['embedding_dim']
        self.deep_hidden_dims = checkpoint['deep_hidden_dims']
        self.dropout = checkpoint['dropout']
        
        # Initialize model
        self.model = DeepFMModel(
            self.num_users,
            self.num_items,
            self.embedding_dim,
            self.deep_hidden_dims,
            self.dropout
        ).to(self.device)
        
        # Load weights
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        self.model_loaded = True
        
        print(f"DeepFM model loaded from {ckpt}")
        print(f"Users: {self.num_users}, Items: {self.num_items}")





