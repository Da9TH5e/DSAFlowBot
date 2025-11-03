# views.py

import requests
import json
import re
from asgiref.sync import async_to_sync

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from django.contrib import messages
from backend.roadmap_engine import roadmap_generator
from backend.definition_engine import definition_generator
from django.views.decorators.cache import never_cache
from backend.code_evaluator.judge0_executor import submit_code
from main_app.forms import CustomUserCreationForm
from django.contrib.auth import authenticate, login
from backend.filter_videos.fetch_videos_youtube import fetching_videos
from main_app.models import Language, Question, Roadmap, Topic, User, Video

def home(request):
    return render(request, "main_app/home.html")

@never_cache
@login_required(login_url='/login/')
def dashboard(request):
    language = request.GET.get("language")  
    roadmap = []  

    if language:
        roadmap_data = roadmap_generator.generate_roadmap(language)
        roadmap = roadmap_data.get("topics", [])

    return render(request, "main_app/dashboard.html", {
        "roadmap": roadmap,
        "language": language,
    })


def roadmap_view(request):
    language = request.GET.get("language")
    if not language:
        return JsonResponse({"error": "Language not provided"}, status=400)

    roadmap_data = roadmap_generator.generate_roadmap(language)
    
    return JsonResponse({
        "roadmap": roadmap_data
    })


@ensure_csrf_cookie
@login_required
def regenerate_roadmap(request):
    language_name = request.GET.get("language")
    user = request.user

    if not language_name:
        return JsonResponse({"error": "Language not specified"}, status=400)

    language, _ = Language.objects.get_or_create(name=language_name.lower())

    Roadmap.objects.filter(user=user, language=language).delete()

    new_roadmap_data = roadmap_generator.generate_roadmap(language_name)
    roadmap = Roadmap.objects.create(
        user=user,
        language=language,
        topics=new_roadmap_data.get("topics", [])
    )

    return JsonResponse({"message": "Roadmap regenerated successfully", "roadmap": roadmap.topics})


@csrf_protect
@require_POST
def set_language(request):
    try:
        data = json.loads(request.body)
        language = data.get("language")

        if not language:
            return JsonResponse({"error": "Language not provided"}, status=400)

        print("Selected Language:", language)
        return JsonResponse({
            "status": "ok",
            "language": language,
            "redirect": f"/dashboard/?language={language}"
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

@require_POST
@csrf_protect
def get_topic(request):
    try:
        data = json.loads(request.body)
        language = data.get("language")
        topic_name = data.get("topic")

        if not language or not topic_name:
            return JsonResponse({"error": "Missing language or topic"}, status=400)

        topic_obj, _ = Topic.objects.get_or_create(
            language=Language.objects.get_or_create(name=language.lower())[0],
            name=topic_name
        )
        if not topic_obj:
            return JsonResponse({"error": "Topic not found in DB"}, status=404)

        definition_obj = topic_obj.definitions.first()
        if definition_obj:
            summary = definition_obj.definition
        else:
            summary = definition_generator.generate_definition(language, topic_name)

        return JsonResponse({"summary": summary})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def run_fetch(language, topic_name):
    async_to_sync(fetching_videos)(language, topic_name)

    
@require_GET
@csrf_protect
def get_videos(request):
    language = request.GET.get("language")
    topic_name = request.GET.get("topic")

    if not language or not topic_name:
        return JsonResponse({"error": "Missing parameters"})

    run_fetch(language, topic_name)

    return JsonResponse({"status": "processing"})

@require_GET
@csrf_protect
def get_filtered_videos(request):
    language = request.GET.get("language")
    topic_name = request.GET.get("topic")

    if not language or not topic_name:
        return JsonResponse({"status": "error", "error": "Missing parameters"})

    try:
        lang_obj, _ = Language.objects.get_or_create(name=language.lower())
        topic_obj, _ = Topic.objects.get_or_create(language=lang_obj, name=topic_name)

        existing_videos = Video.objects.filter(topic=topic_obj)
        videos_data = [
            {
                "video_id": v.video_id,
                "title": v.title,
                "description": v.description,
                "url": v.url,
            }
            for v in existing_videos
        ]
        
        return JsonResponse({"status": "ok", "videos": videos_data})
        
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})


@csrf_protect
@require_GET
def get_questions(request):
    video_id = request.GET.get("video_id")
    if not video_id:
        return JsonResponse({"status": "error", "message": "video_id missing"}, status=400)

    try:
        question_obj = Question.objects.get(video__video_id=video_id)
        text = question_obj.questions.strip()

        text = re.sub(r"\r\n?", "\n", text)

        q_blocks = re.split(r"--- Question \d+ ---", text)
        q_blocks = [b.strip() for b in q_blocks if b.strip()]

        questions_data = []

        for idx, block in enumerate(q_blocks):
            question_data = parse_question_block(block, idx + 1)
            if question_data:
                questions_data.append(question_data)

        questions_data = questions_data[1:4]

        return JsonResponse({"status": "ok", "questions": questions_data})
    
    except Question.DoesNotExist:
        return JsonResponse({"status": "ok", "questions": []})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

def parse_question_block(block, question_num):
    """Parse individual question block line by line"""
    lines = block.split('\n')
    current_field = None
    current_content = []
    
    question_data = {
        "title": f"Question {question_num}",
        "description": "",
        "input_format": "",
        "output_format": "",
        "example_input": "",
        "example_output": "",
    }
    
    field_mapping = {
        "title": "Title:",
        "description": "Description:",
        "input_format": "Input Format:",
        "output_format": "Output Format:",
        "example_input": "Example Input:",
        "example_output": "Example Output:",
    }
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        field_found = False
        for field_key, field_prefix in field_mapping.items():
            if line.startswith(field_prefix):
                if current_field and current_content:
                    question_data[current_field] = '\n'.join(current_content).strip()
                
                current_field = field_key
                current_content = [line[len(field_prefix):].strip()]
                field_found = True
                break
        
        if not field_found and current_field:
            current_content.append(line)
    
    if current_field and current_content:
        question_data[current_field] = '\n'.join(current_content).strip()
    
    return question_data


def question_page(request):
    return render(request, "main_app/questions.html")

def login_view(request):
    if request.method == "POST":
        identifier = request.POST.get("identifier")  # username or email
        password = request.POST.get("password")

        user = None
        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                user = None

        if user:
            user_auth = authenticate(username=user.username, password=password)
            if user_auth is not None:
                login(request, user_auth)
                return redirect("dashboard")
       
        # If invalid
        messages.error(request, "Invalid username/email or password.")
        return render(request, "main_app/login.html")

    return render(request, "main_app/login.html")


def check_username(request):
    username = request.GET.get("username", "").strip()
    if not username:
        return JsonResponse({"available": False, "message": "No username provided"})

    exists = User.objects.filter(username__iexact=username).exists()
    if exists:
        return JsonResponse({"available": False, "message": "Username already taken"})
    return JsonResponse({"available": True, "message": "Username is available"})


def signup_view(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect("login")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, "main_app/signup.html", {"form": form})

@csrf_protect
@require_POST
def generate_roadmap_view(request):
    try:
        data = json.loads(request.body)
        language = data.get("language")

        if not language:
            return JsonResponse({"error": "No language provided"}, status=400)

        lang_obj = Language.objects.filter(name__iexact=language.lower()).first()
        if lang_obj:
            Roadmap.objects.filter(language=lang_obj).delete()

        result = roadmap_generator.generate_roadmap(language)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_protect
@require_POST
def run_code(request):
    if request.method == "POST":
        data = json.loads(request.body)
        source_code = data.get("source_code")
        language = data.get("language")

        language_map = {
            "python": 71,
            "cpp": 54,
            "java": 62,
            "javascript": 63
        }

        language_id = language_map.get(language)
        result = submit_code(source_code, language_id)
        return JsonResponse(result)
    
    
def get_topic_progress(request, language, topic):
    try:
        topic_obj = Topic.objects.get(name=topic, language__name=language)
        data = {
            "total_videos": topic_obj.total_videos,
            "current_videos": topic_obj.videos.count(),
            "is_fully_processed": topic_obj.is_fully_processed,
        }
        return JsonResponse(data)
    except Topic.DoesNotExist:
        return JsonResponse({"error": "Topic not found"}, status=404)