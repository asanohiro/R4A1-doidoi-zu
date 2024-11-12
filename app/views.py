import io
import boto3
from PIL import Image
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
import AWS.settings
from AWS.settings import env
from .models import LostItem
from django.core.serializers import serialize
from uuid import uuid4
import json
import logging
import requests

logger = logging.getLogger(__name__)

PROJECT_VERSION_ARN = env('PROJECT_VERSION_ARN')

def index(request):
    return render(request, 'index.html')

def map(request):
  return render(request, 'app/map.html')


def return_upload_image(request):
    return render(request, 'app/upload.html')

def warning_page(request):
    render(request,'warning.html')


def resize_image(image, max_size=(400, 400)):
    # Open the image
    img = Image.open(image)

    # Convert the image to RGB mode if it's in P mode (or any other mode incompatible with JPEG)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 画像のリサイズ（アスペクト比を維持）
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Convert the resized image to a byte array
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=50)  # Adjust quality as needed
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr


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
    'Accessories': '付属品',
    'Animal': '動物',
    'Bag': 'バック',
    'Binoculars': '双眼鏡',
    'Book': '本',
    'Camera': 'カメラ',
    'Clothing': '衣服',
    'Computer Hardware': '機械',
    'Contact Lens': 'コンタクトレンズ',
    'Cosmetics': '化粧品',
    'Credit Card': 'クレジットカード',
    'Diaper': 'おむつ',
    'Electrical Device': '電気機器',
    'Electronics': '電子機器',
    'Envelope': '封筒',
    'Glasses': '眼鏡',
    'Glove': '手袋',
    'Hat': '帽子',
    'ID Card': '証明書',
    'Jewelry': 'ジュエリー',
    'Key': '鍵',
    'Light': 'ライト',
    'Lighter': 'ライター',
    'Medication': '薬',
    'Mobile Phone': '携帯電話',
    'Money': 'お金',
    'Page': '書類',
    'Pants': 'パンツ',
    'Perfume': '香水',
    'Photography': '写真',
    'Plant': '植物',
    'Raincoat': '合羽',
    'Saucer': '皿',
    'Scarf': 'マフラー',
    'Shoe': '靴',
    'Sock': '靴下',
    'Stick': '杖',
    'Suitcase': 'スーツケース',
    'Tobacco': 'タバコ',
    'Tool': '工具',
    'Toy': '人形',
    'Umbrella': '傘',
    'Underwear': '下着',
    'Wallet': '財布',
    'Water Bottle': '水筒',
    'Wristwatch': '腕時計',
    # 他に必要なラベルをここに追加
}
# 不適切なラベル辞書
INAPPROPRIATE_LABELS = {
    'Face'
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
            image_data = image.read()
            image_bytes_for_upload = io.BytesIO(image_data)  # S3アップロード用のファイルオブジェクト
            image_bytes_for_resize = io.BytesIO(image_data)# リサイズ用のファイルオブジェクト

            print(image_bytes_for_upload)
            print(image_bytes_for_resize)

            # Get the prefecture from location data
            prefecture = get_prefecture_from_location(latitude, longitude)

            # Generate a unique filename
            file_extension = image.name.split('.')[-1]
            file_name = f'{uuid4()}.{file_extension}'

            # 画像をS3にアップロード
            s3.upload_fileobj(image_bytes_for_upload, bucket_name, file_name)
            image_bytes_for_upload.close()  # アップロード用ファイルオブジェクトをクローズ

            # 画像サイズのリサイズ
            resized_image = resize_image(image_bytes_for_resize)
            resized_image_io = io.BytesIO(resized_image)
            image_bytes_for_resize.close()  # リサイズ用ファイルオブジェクトをクローズ

            # 画像ラベル検出
            labels = detect_labels_in_image(resized_image_io)

            # ラベル検出が完了した場合の処理
            detected_inappropriate_labels = any(label['Name'] in INAPPROPRIATE_LABELS for label in labels)
            if detected_inappropriate_labels:
                return redirect('warning_page')

            end_label = extract_relevant_labels(labels)

            # S3 URL を生成
            image_url = f'https://{bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{file_name}'

            # データをテンプレートに渡す
            context = {
                'item_name': end_label,
                'latitude': latitude,
                'longitude': longitude,
                'prefecture': prefecture,
                'image_url': image_url,
                'detected_labels': labels
            }

            return render(request, 'app/upload_result.html', context)

    return render(request, 'app/upload.html')


def upload_image_result(request):
    if request.method == 'POST':
        item_name = request.POST.get('item_name')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        prefecture = request.POST.get('prefecture')
        image_url = request.POST.get('image_url')

        # LostItemに保存
        lost_item = LostItem.objects.create(
            image_url=image_url,
            latitude=latitude,
            longitude=longitude,
            description=item_name,
            prefecture=prefecture
        )
        lost_item.save()

        return render(request, 'app/upload_completion.html')


def map_view(request):
    if request.method == 'GET':
        google_maps_api_key = AWS.settings.env('GOOGLE_MAPS_API_KEY')
        items = LostItem.objects.all()
        items_json = serialize('json', items)
        context = {
            'items_json': items_json,
            'google_maps_api_key': google_maps_api_key
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

def search_lost_items(request):
    search_term = request.GET.get('search', '')
    search_condition = request.GET.get('search-condition', '')

    # 検索条件に基づいてフィルタリング
    if search_condition == '場所':
        items = LostItem.objects.filter(location__icontains=search_term)
    elif search_condition == '時間':
        items = LostItem.objects.filter(date_time__icontains=search_term)
    elif search_condition == '特徴':
        items = LostItem.objects.filter(description__icontains=search_term)
    else:
        items = LostItem.objects.all()


    # 結果をJSONで返す
    results = []
    for item in items:
        results.append({
            'id': item.id,
            'description': item.description,
            'location': item.location,  # 緯度経度の文字列
            'date_time': item.date_time.strftime('%Y-%m-%d %H:%M:%S'),
            'image_url': item.image.url if item.image else '',
            'latitude': item.latitude,  # 緯度
            'longitude': item.longitude  # 経度
        })

    return JsonResponse(results, safe=False)