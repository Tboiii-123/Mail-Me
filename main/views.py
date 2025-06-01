import os
import zipfile
from django.conf import settings
from django.shortcuts import render, redirect
from datetime import datetime
from django.http import HttpResponse, Http404
from io import BytesIO
import shutil


def build_file_tree(base_path):
            tree = {}
            for entry in os.listdir(base_path):
                full_path = os.path.join(base_path, entry)
                if os.path.isdir(full_path):
                    tree[entry] = build_file_tree(full_path)  # Nested dict for folder
                else:
                    tree[entry] = None  # File

            return tree

def index(request):
    upload_folder = os.path.join(settings.BASE_DIR, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    message_file = os.path.join(upload_folder, 'message.txt')
    message = ''


    # Save message if POST request
    if request.method == 'POST':
        # Get message from form
        message = request.POST.get('message', '')

        # Save the message into a temp file
        with open(message_file, 'w', encoding='utf-8') as f:
            f.write(message)

        # Handle file uploads
        uploaded_files = request.FILES.getlist('files')
        for uploaded_file in uploaded_files:
            file_path = os.path.join(upload_folder, uploaded_file.name)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'wb+') as dest:
                for chunk in uploaded_file.chunks():
                    dest.write(chunk)

        # Handle folder uploads
        uploaded_folders = request.FILES.getlist('folder')
        if uploaded_folders:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            folder_root = os.path.join(upload_folder, f"folder_upload_{timestamp}")
            os.makedirs(folder_root, exist_ok=True)

            for uploaded_file in uploaded_folders:
                relative_path = uploaded_file.name.replace('\\', '/')
                file_path = os.path.join(folder_root, relative_path)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'wb+') as dest:
                    for chunk in uploaded_file.chunks():
                        dest.write(chunk)

    # Read the latest saved message if exists
    if os.path.exists(message_file):
        with open(message_file, 'r', encoding='utf-8') as f:
            message = f.read()

    # if 'delete_message' in request.POST:
    #     if os.path.exists(message_file):
    #             os.remove(message_file)
                


    # File tree display
    files_tree = build_file_tree(upload_folder)
    return render(request, 'index.html', {
        'files_tree': files_tree,
        'message': message
    })

    



def delete_file(request):
    if request.method == 'POST':
        filename = request.POST.get('filename')
        upload_folder = os.path.join(settings.BASE_DIR, 'uploads')  # same as in index()
        file_path = os.path.join(upload_folder, filename)

        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except PermissionError as e:
            return HttpResponse(f"Permission denied: {e}", status=403)

        return redirect('index')
    



def download_folder(request, folder_name):
    folder_path = os.path.join(settings.BASE_DIR, 'uploads', folder_name)

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        raise Http404("Folder does not exist")

    # Create ZIP in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zip_file.write(file_path, arcname)

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{folder_name}.zip"'
    return response
