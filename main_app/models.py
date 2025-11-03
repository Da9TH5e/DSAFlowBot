#models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return self.username


class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Topic(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="topics")
    name = models.CharField(max_length=200)
    is_fully_processed = models.BooleanField(default=False)
    total_videos = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('language', 'name')

    def __str__(self):
        return self.name


class Roadmap(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="roadmaps", null=True, blank=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name="roadmaps")
    topics = models.JSONField()

    class Meta:
        unique_together = ('user', 'language')

    def __str__(self):
        user_display = self.user.username if self.user else "Anonymous"
        return f"{user_display}'s Roadmap for {self.language.name}"


class Definition(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="definitions")
    definition = models.TextField()

    def __str__(self):
        return f"Definition for {self.topic.name}"


class Video(models.Model):
    video_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    url = models.URLField()
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="videos")

    def __str__(self):
        return self.title or self.video_id


class Transcript(models.Model):
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name="transcript")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transcript for {self.video.title or self.video.video_id}"


class Question(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="questions", null=True, blank=True)
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name="user_coding_problems", null=True, blank=True)
    questions = models.TextField()

    def __str__(self):
        return f"Questions for {self.user} - {self.video.video_id if self.video else 'No Video'}"