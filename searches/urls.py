from django.urls import path

from .views import HomePageView, search_results, download_results

urlpatterns = [
    path('search/', HomePageView.as_view(), name='home'),
    path('', HomePageView.as_view(), name='home'),
    path('search_results/', search_results, name='search_results'),
    path('download_results/', download_results, name='download_results'),
]