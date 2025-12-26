from app.models.collaborative_model import CollaborativeModel
from app.models.content_based_model import ContentBasedModel
from app.models.hybrid_model import HybridModel
from app.models.personalized_model import PersonalizedRecommendationModel

class RecommendationController:
    def __init__(self, data_dir=None):
        self.collaborative_model = CollaborativeModel(data_dir)
        self.content_based_model = ContentBasedModel(data_dir)
        self.hybrid_model = HybridModel(data_dir)
        self.personalized_model = PersonalizedRecommendationModel(data_dir)
    
    def get_collaborative_recommendations(self, user_id=None, n_recommendations=10):
        return self.collaborative_model.get_recommendations(user_id, n_recommendations)
    
    def get_content_based_recommendations(self, movie_id=None, n_recommendations=10):
        return self.content_based_model.get_recommendations(movie_id, n_recommendations)
    
    def get_hybrid_recommendations(self, user_id=None, movie_id=None, n_recommendations=10):
        return self.hybrid_model.get_recommendations(user_id, movie_id, n_recommendations)
    
    def get_personalized_recommendations(self, user_id, n_recommendations=10):
        """Gợi ý cá nhân hóa theo hành vi và ngữ cảnh."""
        return self.personalized_model.get_personalized_recommendations(user_id, n_recommendations)
    
    def analyze_user_behavior(self, user_id):
        """Phân tích hành vi người dùng."""
        return self.personalized_model.analyze_user_behavior(user_id)
    
    def refresh_models(self):
        """Cập nhật tất cả models với dữ liệu mới."""
        self.collaborative_model.refresh()
        self.personalized_model.refresh()
        return True
