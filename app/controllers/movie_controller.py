# app/controllers/movie_controller.py
import pandas as pd
from models.movie_model import MovieModel
import os

class MovieController:
    def __init__(self, data_dir=None):
        # Nếu data_dir được truyền vào, MovieModel sẽ dùng nó
        self.movie_model = MovieModel(data_dir=data_dir)
    
    def search_movies(self, query):
        return self.movie_model.search_movies(query)
    
    def get_movie_by_id(self, movie_id):
        return self.movie_model.get_movie_by_id(movie_id)
    
    def add_review(self, movie_id, rating, review, username="Anonymous"):
        return self.movie_model.add_review(movie_id, rating, review, username)
    
    def add_interaction(self, movie_id, user_id="Anonymous", action="like"):
        return self.movie_model.add_interaction(movie_id, user_id, action)

    def add_user(self, user_id, metadata=None):
        return self.movie_model.add_user(user_id, metadata)

    def add_item(self, movie_id, title=None, metadata=None):
        return self.movie_model.add_item(movie_id, title, metadata)

    def record_view(self, movie_id, user_id="Anonymous"):
        return self.movie_model.record_view(movie_id, user_id)

    def record_click(self, movie_id, user_id="Anonymous"):
        return self.movie_model.record_click(movie_id, user_id)

    def record_rating(self, movie_id, user_id="Anonymous", rating=5):
        return self.movie_model.record_rating(movie_id, user_id, rating)
    
    def get_movie_reviews(self, movie_id):
        return self.movie_model.get_movie_reviews(movie_id)

    def add_comment(self, movie_id, user_id, comment_text):
        return self.movie_model.add_comment(movie_id, user_id, comment_text)

    def get_movie_comments(self, movie_id, limit=50, offset=0):
        return self.movie_model.get_movie_comments(movie_id, limit=limit, offset=offset)

    def autocomplete(self, query, n=10):
        return self.movie_model.autocomplete(query, n=n)
