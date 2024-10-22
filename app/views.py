import io
import boto3
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from AWS.settings import env
from .models import LostItem
from django.core.serializers import serialize
from uuid import uuid4
import json
import logging
import requests

logger = logging.getLogger(__name__)

PROJECT_VERSION_ARN = env('PROJECT_VERSION_ARN')

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
    # 最初にファイルデータを全て読み込み、メモリに保存
    image_data = image.read()
    # 読み込んだデータを使ってバイトストリームに変換
    image_bytes = io.BytesIO(image_data)
    # Rekognition APIに送信
    client = boto3.client('rekognition',
                          aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                          aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                          region_name=settings.AWS_REGION)

    # ラベル検出
    response = client.detect_labels(Image={'Bytes': image_bytes.getvalue()}, MaxLabels=10, MinConfidence=75)

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


def get_prefecture_from_location(latitude, longitude):
    api_key = settings.GOOGLE_MAPS_API_KEY
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={latitude},{longitude}&key={api_key}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"API Response: {json.dumps(data, indent=2)}")  # デバッグのためにAPIレスポンス全体を表示

            if data['results']:
                # フィルタリングによる都道府県名の取得
                results = list(filter(lambda component: "administrative_area_level_1" in component['types'],
                                      data['results'][0]['address_components']))

                if results:
                    prefecture = results[0]['long_name']
                    print(f"Found prefecture: {prefecture}")
                    return prefecture
                else:
                    print("administrative_area_level_1 が見つかりませんでした。")
            else:
                print("結果が空でした。")
        else:
            print(f"Error: API request failed with status code {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    return "不明"

# 実際の検出と自動入力の実行
# views.py
s3 = boto3.client('s3',
                  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                  region_name=settings.AWS_S3_REGION_NAME)

bucket_name = settings.AWS_STORAGE_BUCKET_NAME
def upload_image(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if image and latitude and longitude:
            # 画像データをメモリに読み込む
            image_data = image.read()  # ファイルデータをすべて読み込む

            # 都道府県を取得
            prefecture = get_prefecture_from_location(latitude, longitude)

            # ファイル名にUUIDを使用して一意にする
            file_extension = image.name.split('.')[-1]
            file_name = f'{uuid4()}.{file_extension}'

            # S3に画像をアップロード
            s3.upload_fileobj(io.BytesIO(image_data), bucket_name, file_name)
            # 画像のURLを作成 (公開URLを生成)
            image_url = f'https://{bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{file_name}'

            # ラベル検出を実行
            detected_labels = detect_labels_in_image(io.BytesIO(image_data))  # 画像データを再利用
            item_name = detected_labels[0]['Name'] if detected_labels else "不明"

            # LostItemに保存
            lost_item = LostItem.objects.create(
                image_url=image_url,  # S3の画像URLを保存
                latitude=latitude,
                longitude=longitude,
                description=item_name,
                prefecture=prefecture
            )

            # データをテンプレートに渡して表示
            context = {
                'item_name': item_name,
                'latitude': latitude,
                'longitude': longitude,
                'prefecture': prefecture,
                'image_url': image_url  # S3の画像URL
            }
            return render(request, 'app/upload_result.html', context)

    return render(request, 'index.html')

# マップ表示
def map_view(request):
    items = LostItem.objects.all()
    items_json = serialize('json', items)
    context ={
        'items_json': items_json,
        'google_maps_api_key': settings.GOOGLE_MAPS_API_KEY
    }
    return render(request, 'app/map.html', context)


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