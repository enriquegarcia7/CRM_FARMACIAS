from django.urls import path
from .seasonal_views import predict_seasonal_demand, get_seasonal_predictions_year, get_available_categories

urlpatterns = [
    # ... tus otras URLs
    path('predict-seasonal/', predict_seasonal_demand, name='predict-seasonal'),
    path('seasonal-predictions/', get_seasonal_predictions_year, name='seasonal-predictions-year'),
    path('seasonal/predict/', predict_seasonal_demand, name='predict_seasonal'),
    path('seasonal/year/', get_seasonal_predictions_year, name='seasonal_year'),
    path('seasonal/categories/', get_available_categories, name='seasonal_categories'),
]