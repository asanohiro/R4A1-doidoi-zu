import os
from datetime import datetime

import boto3
from django.shortcuts import render
from .forms import UploadImageForm
from django.conf import settings

PROJECT_VERSION_ARN = 'arn:aws:rekognition:ap-northeast-1:637423229169:project/Sotuken1/version/Sotuken1.2024-06-28T10.33.08/1719538390200'

def detect_custom_labels_in_image(image_path):
    client = boto3.client('rekognition',
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                          region_name=settings.AWS_REGION)

    with open(image_path, 'rb') as image_file:
        image_bytes = image_file.read()

    response = client.detect_custom_labels(ProjectVersionArn=PROJECT_VERSION_ARN, Image={'Bytes': image_bytes})

    return response  # Return the full response for debugging purposes


def upload_image(request):
    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            image_path = os.path.join(settings.MEDIA_ROOT, image.name)
            with open(image_path, 'wb+') as f:
                for chunk in image.chunks():
                    f.write(chunk)

            detected_labels = detect_custom_labels_in_image(image_path)
            date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            location = request.POST.get('location', 'Unknown')

            return render(request, 'app/result.html', {
                'labels': detected_labels['CustomLabels'],
                'date_time': date_time,
                'location': location,
                'image_url': settings.MEDIA_URL + image.name
            })
    else:
        form = UploadImageForm()
    return render(request, 'app/upload.html', {'form': form})
