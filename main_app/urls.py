#urls.py

from . import views
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("generate_roadmap/", views.generate_roadmap_view, name="generate_roadmap"),  
    path("logout/", LogoutView.as_view(next_page='/'), name="logout"),
    path("check-username/", views.check_username, name="check_username"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("roadmap/", views.roadmap_view, name="roadmap"),
    path("set-language/", views.set_language, name="set_language"),
    path("get_topic/", views.get_topic, name="get_topic"),
    path("get_videos/", views.get_videos, name="get_videos"),
    path("questions/", views.question_page, name="question_page"),
    path("get_questions/", views.get_questions, name="get_questions"),
    path("get_filtered_videos/", views.get_filtered_videos, name="get_filtered_videos"),
    path("run_code/", views.run_code, name="run_code"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)