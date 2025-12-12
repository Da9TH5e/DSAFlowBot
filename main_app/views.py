# views.py

import os
import json
import re
from asgiref.sync import async_to_sync
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random
import string
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from django.contrib import messages
from backend.roadmap_engine import roadmap_generator
from backend.definition_engine import definition_generator
from django.views.decorators.cache import never_cache
from backend.code_evaluator.judge0_executor import submit_code
from django.contrib.auth import authenticate, login
from backend.filter_videos.fetch_videos_youtube import fetching_videos
from main_app.models import Language, Question, Roadmap, Topic, Transcript, User, Video, EmailVerification

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


@require_POST
def set_language(request):
    try:
        data = json.loads(request.body)
        language = data.get("language")

        if not language:
            return JsonResponse({"error": "Language not provided"}, status=400)

        return JsonResponse({
            "status": "ok",
            "language": language,
            "redirect": f"/dashboard/?language={language}"
        })

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

@require_POST
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
@login_required
def get_videos(request):
    language = request.GET.get("language")
    topic_name = request.GET.get("topic")

    if not language or not topic_name:
        return JsonResponse({"error": "Missing parameters"})

    run_fetch(language, topic_name)

    return JsonResponse({"status": "processing"})

@require_GET
def get_filtered_videos(request):
    language = request.GET.get("language")
    topic_name = request.GET.get("topic")

    if not language or not topic_name:
        return JsonResponse({"status": "error", "error": "Missing parameters"})

    try:
        lang_obj, _ = Language.objects.get_or_create(name=language.lower())
        topic_obj, _ = Topic.objects.get_or_create(language=lang_obj, name=topic_name)

        existing_videos = Video.objects.filter(topic=topic_obj)
        current_count = existing_videos.count()
        total_videos = topic_obj.total_videos

        fetching = current_count < total_videos or total_videos == 0

        videos_data = [
            {
                "video_id": v.video_id,
                "title": v.title,
                "description": v.description,
                "url": v.url,
            }
            for v in existing_videos
        ]
        
        return JsonResponse({
            "status": "ok",
            "videos": videos_data,
            "fetching": fetching,
            "current": current_count,
            "total": total_videos
        })
        
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})


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
        identifier = request.POST.get("identifier", "").strip()  # username or email
        password = request.POST.get("password", "").strip()

        if not identifier or not password:
            messages.error(request, "Please fill in all fields.")
            return render(request, "main_app/login.html")

        user = None
        if User.objects.filter(username=identifier).exists():
            user = User.objects.get(username=identifier)
        elif User.objects.filter(email=identifier).exists():
            user = User.objects.get(email=identifier)

        if not user:
            messages.error(request, "No account found with that username or email.")
            return render(request, "main_app/login.html")

        if not user.is_active:
            otp_code = ''.join(random.choices(string.digits, k=6))
            verification, _ = EmailVerification.objects.get_or_create(user=user)
            verification.otp = otp_code
            verification.created_at = timezone.now()
            verification.last_sent = timezone.now()
            verification.save()

            send_mail(
                subject="Verify your DSAFlowBot account",
                message=f"Hello {user.username},\n\nYour verification code is: {otp_code}\n\nThis code expires in 10 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            
            messages.warning(request, f"Your account is not verified. A code has been sent to {user.email}.")
            request.session["pending_verification_user"] = user.id
            return render(request, "main_app/login.html", {"verify_email": True, "email": user.email})

        user_auth = authenticate(request, username=user.username, password=password)
        if user_auth:
            login(request, user_auth)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid password. Please try again.")
            return render(request, "main_app/login.html")

    return render(request, "main_app/login.html")


def check_username(request):
    username = request.GET.get("username", "").strip()
    if not username:
        return JsonResponse({"available": False, "message": "No username provided"})

    exists = User.objects.filter(username=username).exists()
    if exists:
        return JsonResponse({"available": False, "message": "Username already taken"})
    return JsonResponse({"available": True, "message": "Username is available"})


def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = (
            request.POST.get("password1")
            or request.POST.get("password")
            or request.POST.get("password2")
        )
        profile_pic_choice = request.POST.get("profile_picture_choice")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("signup")
        
        if username == email:
            messages.error(request, "Username and email cannot be same")
            return redirect("signup")

        user = User.objects.create_user(username=username, email=email, password=password)
        user.is_active = False

        if not password:
            messages.error(request, "Password not provided. Please try again.")
            return redirect("signup")

        if profile_pic_choice:
            filename = os.path.basename(profile_pic_choice)
            user.profile_picture = f"profile_pics/{filename}"

        user.save()

        otp = ''.join(random.choices(string.digits, k=6))
        verification, created = EmailVerification.objects.get_or_create(user=user)
        verification.otp = otp
        verification.created_at = timezone.now()
        verification.last_sent = timezone.now()
        verification.save()

        send_mail(
            subject="Verify your DSAFlowBot account",
            message=f"Hello {username},\n\nYour verification code is: {otp}\n\nThis code expires in 10 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        request.session['pending_user'] = user.id
        messages.info(request, "A verification code has been sent to your email.")
        return redirect("verify_email")

    return render(request, "main_app/signup.html")

def check_email(request):
    email = request.GET.get("email", "").strip()
    if not email:
        return JsonResponse({"available": False, "message": "No email provided"})

    exists = User.objects.filter(email=email).exists()
    if exists:
        return JsonResponse({"available": False, "message": "Email already registered"})
    return JsonResponse({"available": True, "message": "Email is available"})


def verify_email(request):
    user_id = request.session.get("pending_user")
    if not user_id:
        messages.error(request, "No pending verification found. Please sign up again.")
        return redirect("signup")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please sign up again.")
        if "pending_user" in request.session:
            del request.session["pending_user"]
        return redirect("signup")

    try:
        verification = EmailVerification.objects.get(user=user)
    except EmailVerification.DoesNotExist:
        messages.error(request, "Verification code not found. Please sign up again.")
        return redirect("signup")

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        
        # Check if expired
        if verification.is_expired():
            messages.error(request, "Your code has expired. Please sign up again.")
            verification.delete()
            user.delete()
            if "pending_user" in request.session:
                del request.session["pending_user"]
            return redirect("signup")

        # Match code
        if verification.otp.strip() == entered_otp.strip():
            user.is_active = True
            user.save()
            verification.delete()
            if "pending_user" in request.session:
                del request.session["pending_user"]
            messages.success(request, "Email verified successfully! You can now log in.")
            return redirect("login")
        else:
            messages.error(request, "Invalid code. Please try again.")

    return render(request, "main_app/verify.html", {"email": user.email})


def resend_otp(request):
    user_id = request.session.get("pending_user")
    if not user_id:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect("signup")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "User not found. Please sign up again.")
        return redirect("signup")

    verification, _ = EmailVerification.objects.get_or_create(user=user)

    if not verification.can_resend():
        remaining = 120 - int((timezone.now() - verification.last_sent).total_seconds())
        messages.warning(request, f"Please wait {remaining} seconds before requesting a new code.")
        return redirect("verify_email")

    verification.generate_otp()

    send_mail(
        subject="Your new DSAFlowBot verification code",
        message=f"Hello {user.username},\n\nYour new verification code is: {verification.otp}\n\nThis code expires in 10 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

    messages.success(request, "A new verification code has been sent to your email.")
    return redirect("verify_email")

def forgot_password_view(request):
    return render(request, "main_app/forgot_password.html")

@require_POST
def send_reset_otp(request):
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()

        if not email:
            return JsonResponse({"status": "error", "message": "Email is required."}, status=400)

        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({"status": "error", "message": "No account found with this email."}, status=404)
        
        
        otp_code = ''.join(random.choices(string.digits, k=6))
        verification, _ = EmailVerification.objects.get_or_create(user=user)
        verification.otp = otp_code
        verification.created_at = timezone.now()
        verification.last_sent = timezone.now()
        verification.save()
        send_mail(
            subject="Verify your DSAFlowBot account",
            message=f"Hello {user.username},\n\nYour verification code is: {otp_code}\n\nThis code expires in 10 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return JsonResponse({"status": "ok", "message": f"OTP sent successfully to {email}."})

    except Exception as e:
        messages.error(request, f"Error sending reset OTP: {e}")
        return JsonResponse({"status": "error", "message": "Failed to send OTP."}, status=500)

@require_POST
def verify_reset_otp(request):
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()
        otp = data.get("otp", "").strip()
        new_password = data.get("new_password", "").strip()
        confirm_password = data.get("confirm_password", "").strip()

        if not email or not otp:
            return JsonResponse({"status": "error", "message": "Email and OTP are required."}, status=400)

        user = User.objects.filter(email=email).first()
        if not user:
            return JsonResponse({"status": "error", "message": "Invalid email."}, status=404)

        try:
            verification = EmailVerification.objects.get(user=user)
        except EmailVerification.DoesNotExist:
            return JsonResponse({"status": "error", "message": "No OTP found. Please request a new one."}, status=404)

        if verification.is_expired():
            verification.delete()
            return JsonResponse({"status": "error", "message": "OTP expired. Please request a new one."}, status=400)

        if verification.otp != otp:
            return JsonResponse({"status": "error", "message": "Invalid OTP. Please try again."}, status=400)

        if not new_password and not confirm_password:
            return JsonResponse({"status": "ok", "message": "OTP verified successfully!"})

        if new_password != confirm_password:
            return JsonResponse({"status": "error", "message": "Passwords do not match."}, status=400)

        user.set_password(new_password)
        user.save()
        verification.delete()

        return JsonResponse({"status": "ok", "message": "Password reset successfully! You can now log in."})

    except Exception as e:
        messages.error(f"Error verifying OTP: {e}")
        return JsonResponse({"status": "error", "message": "An error occurred while verifying OTP."}, status=500)

@require_POST
def verify_login_email(request):
    try:
        data = json.loads(request.body)
        email = data.get("email", "").strip()
        otp = data.get("otp", "").strip()

        if not email or not otp:
            return JsonResponse({"status": "error", "message": "Both email and OTP are required."}, status=400)

        pending_user_id = request.session.get("pending_verification_user")
        if pending_user_id:
            pending_user = User.objects.filter(id=pending_user_id).first()
            if not pending_user or pending_user.email != email:
                return JsonResponse({"status": "error", "message": "Unauthorized verification attempt."}, status=403)
            user = pending_user
        else:
            user = User.objects.filter(email=email).first()

        if not user:
            return JsonResponse({"status": "error", "message": "Invalid email."}, status=404)
        
        else:
            user.is_active = True
            user.save()
            return JsonResponse({"status": "ok", "message": "Email verified successfully."})

    except Exception as e:
        messages.error(f"Error verifying login OTP: {e}")
        return JsonResponse({"status": "error", "message": "Server error during email verification."}, status=500)

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
