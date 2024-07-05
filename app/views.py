# app/views.py
import os
import boto3
from django.shortcuts import render
from .forms import UploadImageForm
from django.conf import settings

PROJECT_VERSION_ARN = "arn:aws:rekognition:ap-northeast-1:637423229169:project/Sotuken1/version/Sotuken1.2024-06-28T10.33.08/1719538390200"


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
            response = detect_custom_labels_in_image(image_path)

            # Check for sensitive labels and confidence
            sensitive_labels = ["credit", "Identification"]
            high_confidence = any(label['Name'] in sensitive_labels and label['Confidence'] > 90 for label in
                                  response.get('CustomLabels', []))

            image_url = os.path.join(settings.MEDIA_URL, image.name)

            return render(request, 'app/result.html', {
                'high_confidence': high_confidence,
                'image_url': image_url
            })
    else:
        form = UploadImageForm()
    return render(request, 'app/upload.html', {'form': form})
