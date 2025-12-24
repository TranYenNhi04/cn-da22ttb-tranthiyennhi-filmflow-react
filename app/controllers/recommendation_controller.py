from models.collaborative_model import CollaborativeModel
from models.content_based_model import ContentBasedModel
from models.hybrid_model import HybridModel

class RecommendationController:
    def __init__(self, data_dir=None):
        self.collaborative_model = CollaborativeModel(data_dir)
        self.content_based_model = ContentBasedModel(data_dir)
        self.hybrid_model = HybridModel(data_dir)
    
    def get_collaborative_recommendations(self, user_id=None, n_recommendations=10):
        return self.collaborative_model.get_recommendations(user_id, n_recommendations)
    
    def get_content_based_recommendations(self, movie_id=None, n_recommendations=10):
        return self.content_based_model.get_recommendations(movie_id, n_recommendations)
    
    def get_hybrid_recommendations(self, user_id=None, movie_id=None, n_recommendations=10):
        return self.hybrid_model.get_recommendations(user_id, movie_id, n_recommendations)
