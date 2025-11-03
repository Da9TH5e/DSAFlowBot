# main_app/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Language, Topic, Roadmap, Definition, User, Video, Question, Transcript

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ['id', 'username', 'email', 'password', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    search_fields = ['username', 'email']
    ordering = ['id']
    list_display_links = ['id', 'username']

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']
    list_display_links = ['id', 'name']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'language', 'definitions_count', 'videos_count', 'total_videos', 'flag']
    list_filter = ['language']
    search_fields = ['name', 'language__name']
    list_display_links = ['id', 'name']
    
    def definitions_count(self, obj):
        return obj.definitions.count()
    definitions_count.short_description = 'Defs'
    
    def videos_count(self, obj):
        return obj.videos.count()
    videos_count.short_description = 'Videos'

    def flag(self, obj):
        return obj.is_fully_processed
    flag.short_description = 'Check'


@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ['id', 'language', 'topics_preview']
    list_filter = ['language']
    search_fields = ['language__name']
    list_display_links = ['id', 'language']

    def topics_preview(self, obj):
        if obj.topics and isinstance(obj.topics, list):
            return ", ".join(obj.topics[:3]) + (" ..." if len(obj.topics) > 3 else "")
        return "No topics"
    topics_preview.short_description = 'Topics'


@admin.register(Definition)
class DefinitionAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'preview']
    list_filter = ['topic__language']
    search_fields = ['topic__name', 'definition']
    list_display_links = ['id']
    
    def preview(self, obj):
        return obj.definition[:100] + '...' if len(obj.definition) > 100 else obj.definition
    preview.short_description = 'Definition'


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'topic', 'video_id', 'has_questions']
    list_filter = ['topic__language']
    search_fields = ['title', 'topic__name', 'video_id']
    list_display_links = ['id', 'title']
    
    def has_questions(self, obj):
        return obj.user_coding_problems.exists()
    has_questions.boolean = True
    has_questions.short_description = 'Questions'



@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ['id', 'video_title', 'created_at', 'updated_at']
    list_filter = ['video__topic__language', 'created_at']
    search_fields = ['video__title', 'video__video_id']
    list_display_links = ['id']
    
    def video_title(self, obj):
        return obj.video.title or obj.video.video_id
    video_title.short_description = 'Video'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'video', 'questions_preview']
    list_filter = ['video__topic__language']
    search_fields = ['video__title']
    list_display_links = ['id', 'video']

    def questions_preview(self, obj):
        return (obj.questions[:80] + '...') if len(obj.questions) > 80 else obj.questions
    questions_preview.short_description = 'Questions'
