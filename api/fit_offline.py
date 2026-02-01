import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load .env file before importing config
WEB_DIR_PATH = Path(__file__).resolve().parents[1] / "backend"
load_dotenv(WEB_DIR_PATH / ".env")

DB_PATH = WEB_DIR_PATH / "app.db"
sys.path.append(WEB_DIR_PATH.__str__())

from config import Config, BASE_DIR
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.model import User, Movie, Interaction
from mongodb_client import mongodb_client
import numpy as np
import scipy.sparse as sp
from tqdm import tqdm
from recommend.utils import split_train_test
from recommend.models import model_to_cls
from recommend.evaluate import extract_top_k, evaluate

parser = argparse.ArgumentParser()
parser.add_argument('--model', type=str, default='ItemKNN')
parser.add_argument('--save_dir', type=str, default='recommend/ckpt')
parser.add_argument('--test_ratio', type=float, default=0.1)
parser.add_argument('--k', type=int, default=100)
args = parser.parse_args()

app = Flask(__name__)
app.config.from_object(Config)
app.app_context().push()

# Connect to MongoDB
mongodb_client.connect()
mongodb = mongodb_client.get_database()

# Load rating matrix from MongoDB
def load_rating_matrix_from_mongodb():
    """Load rating matrix from MongoDB interactions"""
    interactions_collection = mongodb['interactions']
    users_collection = mongodb['users']
    
    # Get all interactions
    all_interactions = list(interactions_collection.find())
    
    # Get unique user and movie IDs to build matrix dimensions
    user_ids = sorted(users_collection.distinct('_id'))
    movie_ids = sorted(mongodb['movies'].distinct('_id'))
    
    # Create mapping from MongoDB IDs to matrix indices
    user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
    movie_id_to_idx = {mid: idx for idx, mid in enumerate(movie_ids)}
    
    users = []
    items = []
    ratings = []
    
    for interaction in tqdm(all_interactions, total=len(all_interactions), desc="Loading interactions"):
        user_id = interaction.get('user_id')
        movie_id = interaction.get('movie_id')
        
        if user_id in user_id_to_idx and movie_id in movie_id_to_idx:
            users.append(user_id_to_idx[user_id])
            items.append(movie_id_to_idx[movie_id])
            ratings.append(1)  # implicit feedback
    
    num_users = len(user_ids)
    num_items = len(movie_ids)
    rating_matrix = sp.csr_matrix((ratings, (users, items)), shape=(num_users, num_items))
    return rating_matrix

rating_matrix = load_rating_matrix_from_mongodb()
num_users, num_items = rating_matrix.shape

train_matrix, test_matrix = split_train_test(rating_matrix, test_ratio=args.test_ratio, shape=(num_users, num_items))
model_cls = model_to_cls[args.model]
model = model_cls()

print('Train start...')
model.fit(train_matrix, save_path=args.save_dir)

print('Train finished...')

prediction = model.predict(train_matrix)
topk = extract_top_k(prediction, args.k)

# Evaluate (skip if test matrix is empty to avoid division by zero)
try:
    scores = evaluate(topk, test_matrix, args.k)
    print(f"Evaluation scores: {scores}")
except ZeroDivisionError:
    print("Skipping evaluation (test set is empty)")

# Model is already saved by model.fit(), but save again to be sure
model.save(args.save_dir)
print(f"Model saved to {args.save_dir}")