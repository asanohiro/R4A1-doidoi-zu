import os
from datetime import datetime
import boto3
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from .models import LostItem
from django.core.serializers import serialize

PROJECT_VERSION_ARN = 'arn:aws:rekognition:ap-northeast-1:637423229169:project/Sotuken1/version/Sotuken1.2024-06-28T10.33.08/1719538390200'


def detect_labels_api(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            detected_labels = detect_labels_in_image(image)
            labels = [label['Name'] for label in detected_labels]
            return JsonResponse({'labels': labels})
        else:
            return JsonResponse({'error': '画像が選択されていません。'})
    return JsonResponse({'error': '無効なリクエストです。'})

# AWSのデフォルトモデルでラベルを検出
def detect_labels_in_image(image):
    client = boto3.client('rekognition',
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                          region_name=settings.AWS_REGION)
    image_bytes = image.read()

    response = client.detect_labels(Image={'Bytes': image_bytes}, MaxLabels=10, MinConfidence=75)
    return response['Labels']

# 画像アップロード処理
def upload_image(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            # ラベル検出のロジックを実行
            detected_labels = detect_labels_in_image(image)
            labels = [label['Name'] for label in detected_labels]

            # フォームデータの取得
            item_name = request.POST.get('item_name', '不明')
            color = request.POST.get('color', '不明')
            genre = request.POST.get('genre', '不明')
            lost_location = request.POST.get('lost_location', '不明')
            found_time = request.POST.get('found_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

            # データベースに保存
            lost_item = LostItem.objects.create(
                image=image,
                description=item_name,
                location=lost_location,
                date_time=found_time,
                status=color,  # 色をステータスとして保存
            )

            # map_viewにリダイレクト
            return redirect('map_view')

    return render(request, 'app/upload.html')

# マップ表示
def map_view(request):
    items = LostItem.objects.all()
    items_json = serialize('json', items)
    return render(request, 'app/map.html', {'items_json': items_json})


# 全てのアイテムを削除
def delete_all_items(request):
    LostItem.objects.all().delete()
    return redirect('map_view')