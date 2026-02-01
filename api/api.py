import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

from recommend.recommender import RecommenderWrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

wrapper = RecommenderWrapper()

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/api/recommend", methods=['POST'])
def recommend():
    """Get recommendations using specified model"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'MISSING_DATA',
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        if 'context' not in data:
            return jsonify({
                'error': 'MISSING_CONTEXT',
                'message': 'Context (movie IDs) is required'
            }), 400
        
        if not data['context'] or len(data['context']) == 0:
            return jsonify({
                'error': 'EMPTY_CONTEXT',
                'message': 'Context cannot be empty'
            }), 400
        
        if 'model' not in data:
            return jsonify({
                'error': 'MISSING_MODEL',
                'message': 'Model name is required'
            }), 400
        
        user_context = data['context']
        model = data['model']
        
        # Validate model name
        valid_models = ['EASE', 'ItemKNN', 'NeuralMF', 'DeepFM']  # Added placeholder for neural models
        if model not in valid_models:
            return jsonify({
                'error': 'INVALID_MODEL',
                'message': f'Model must be one of {valid_models}',
                'available_models': valid_models
            }), 400
        
        # Validate context format
        try:
            user_context = [int(item) for item in user_context]
        except (ValueError, TypeError):
            return jsonify({
                'error': 'INVALID_CONTEXT',
                'message': 'Context must be an array of integers (movie IDs)'
            }), 400
        
        # Get recommendations
        try:
            wrapper.set_model(model)
            result = wrapper.recommend(user_context)
            
            if not result:
                return jsonify({
                    'error': 'NO_RECOMMENDATIONS',
                    'message': 'No recommendations found',
                    'result': []
                }), 200
            
            logger.info(f"Generated {len(result)} recommendations using {model}")
            
            return jsonify({
                'result': result,
                'model': model,
                'count': len(result)
            }), 200
            
        except KeyError as e:
            logger.error(f"Model {model} not found: {str(e)}")
            return jsonify({
                'error': 'MODEL_NOT_FOUND',
                'message': f'Model {model} is not available',
                'available_models': valid_models
            }), 404
        except FileNotFoundError as e:
            logger.error(f"Checkpoint not found for model {model}: {str(e)}")
            return jsonify({
                'error': 'MODEL_CHECKPOINT_MISSING',
                'message': f'Model {model} checkpoint file not found. The model needs to be trained first.',
                'available_models': valid_models
            }), 503
        except Exception as e:
            logger.error(f"Recommendation error: {str(e)}")
            return jsonify({
                'error': 'RECOMMENDATION_ERROR',
                'message': 'Failed to generate recommendations',
                'details': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'error': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred'
        }), 500

@app.route("/api/models", methods=['GET'])
def get_models():
    """Get list of available recommendation models"""
    return jsonify({
        'models': [
            {'name': 'EASE', 'type': 'non-neural', 'description': 'Embarrassingly Shallow Autoencoders'},
            {'name': 'ItemKNN', 'type': 'non-neural', 'description': 'Item-based Collaborative Filtering'},
            {'name': 'NeuralMF', 'type': 'neural', 'description': 'Neural Matrix Factorization (Coming Soon)'},
            {'name': 'DeepFM', 'type': 'neural', 'description': 'Deep Factorization Machine (Coming Soon)'}
        ]
    }), 200

@app.route("/api/health", methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'recommendation-api'
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'NOT_FOUND',
        'message': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'INTERNAL_ERROR',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    import os
    port = int(os.getenv('PORT', 8000))
    app.run(host="0.0.0.0", port=port, debug=False)