import os
from datetime import datetime
import boto3
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from .models import LostItem
from django.core.serializers import serialize
import logging
import requests

logger = logging.getLogger(__name__)

PROJECT_VERSION_ARN = 'arn:aws:rekognition:ap-northeast-1:637423229169:project/Sotuken1/version/Sotuken1.2024-06-28T10.33.08/1719538390200'


def detect_labels_api(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            # ラベルを検出
            detected_labels = detect_labels_in_image(image)

            # 検出されたラベルを使って必要なデータを抽出
            form_data = extract_relevant_labels(detected_labels)

            # ラベルとともにJSONレスポンスを返す
            labels = [label['Name'] for label in detected_labels]
            return JsonResponse({'labels': labels, 'form_data': form_data})  # form_dataを追加して返す
    return JsonResponse({'error': '無効なリクエストです。'})

# AWSのデフォルトモデルでラベルを検出
# AWSからのラベルを検出する関数
def detect_labels_in_image(image):
    client = boto3.client('rekognition',
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                          region_name=settings.AWS_REGION)

    image_bytes = image.read()
    response = client.detect_labels(Image={'Bytes': image_bytes}, MaxLabels=10, MinConfidence=75)
    return response['Labels']


# ラベルマッピング辞書
label_mapping = {
    'ID Card': '証明書',
    'Credit Card': 'クレジットカード'
    # 他に必要なラベルをここに追加
}

# ラベルのマッピングとフォームへの反映
def extract_relevant_labels(labels):
    # 対応するフォームフィールドの値を保存する辞書
    form_data = {
        'item_name': '',
        'genre': '',
        'color': ''
    }

    for label in labels:
        print(f"Detected label: {label['Name']}")

        if label['Name'] == 'Credit Card':
            form_data['item_name'] = label_mapping['Credit Card']
            break  # 「クレジットカード」を見つけたら以降の処理をしない

        elif label['Name'] == 'ID Card':
            form_data['item_name'] = label_mapping['ID Card']

        # 他のラベルの処理
        elif label['Name'] == 'Electronics':
            form_data['genre'] = '電子機器'

    # 'item_name' が空の場合はデフォルト値を設定
    if not form_data['item_name']:
        form_data['item_name'] = '不明'

    print(f"Final form_data: {form_data}")
    return form_data


# Geocoding APIを使用して都道府県を取得する関数
def get_prefecture_from_location(latitude, longitude):
    api_key = 'AIzaSyBTheiF0rr8chsdrv8vFMXVruV4JMLDhqY&callback=initMap'  # Google Maps APIキー
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            for component in data['results'][0]['address_components']:
                if 'administrative_area_level_1' in component['types']:
                    return component['long_name']  # 都道府県名を返す

# 実際の検出と自動入力の実行
# views.py

def upload_image(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        latitude = request.POST.get('latitude')  # 緯度
        longitude = request.POST.get('longitude')  # 経度

        if image and latitude and longitude:
            # 都道府県を取得
            prefecture = get_prefecture_from_location(latitude, longitude)

            # AWS Rekognitionでラベル検出
            detected_labels = detect_labels_in_image(image)
            form_data = extract_relevant_labels(detected_labels)

            # LostItemに保存
            lost_item = LostItem.objects.create(
                image=image,
                location=f"{latitude}, {longitude}",
                description=form_data['item_name'],  # ここで品名を使用
                prefecture=prefecture  # 都道府県を保存
            )

            # データをテンプレートに渡して表示
            context = {
                'item_name': form_data['item_name'],
                'genre': form_data['genre'],
                'latitude': latitude,
                'longitude': longitude,
                'prefecture': prefecture,
                'image_url': lost_item.image.url  # 画像のURLをテンプレートに渡す
            }
            return render(request, 'app/upload_result.html', context)

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


def search_items(request):
    item_name = request.GET.get('item_name', '')
    prefecture = request.GET.get('prefecture', '')

    # 条件に基づいてLostItemをフィルタリング
    items = LostItem.objects.all()

    if item_name:
        items = items.filter(description__icontains=item_name)

    if prefecture:
        items = items.filter(location__icontains=prefecture)

    # 検索結果をJSON形式で返す
    items_json = serialize('json', items)
    return render(request, 'app/map.html', {'items_json': items_json})