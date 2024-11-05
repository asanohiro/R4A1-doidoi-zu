import io
import boto3
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.conf import settings
from django.urls import reverse
import AWS.settings
from AWS.settings import env
from .models import LostItem
from django.core.serializers import serialize
from uuid import uuid4
import json
import logging
import requests
from PIL import Image
import base64

logger = logging.getLogger(__name__)

PROJECT_VERSION_ARN = env('PROJECT_VERSION_ARN')

# views.py
s3 = boto3.client('s3',
                  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                  region_name=settings.AWS_S3_REGION_NAME
                  )

bucket_name = settings.AWS_STORAGE_BUCKET_NAME

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
# 不適切なラベルリストを定義（定数として扱う）
INAPPROPRIATE_LABELS = {
    'Face',
    'Food',
    'Finger',
    'Body Part'
    'Person Description'
}

def index(request):
    return render(request, 'index.html')


def return_upload_image(request):
    return render(request, 'app/upload.html')


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

def resize_image_api(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES.get('image')

        resized_image = resize_image(image_file)

        encoded_image = base64.b64encode(resized_image).decode('utf-8')
        return JsonResponse({'resized_image': encoded_image})
    return JsonResponse({'error': '画像が見つかりませんでした。'}, status=400)

# AWSのデフォルトモデルでラベルを検出
def detect_labels_in_image(image_data):
    # Rekognition API に送信
    client = boto3.client(
        'rekognition',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

    # ラベル検出
    response = client.detect_labels(
        Image={'Bytes': image_data},
        MaxLabels=5,
        MinConfidence=85
    )
    return response['Labels']


# ラベルのマッピングとフォームへの反映
def extract_relevant_labels(labels):
    # 対応するフォームフィールドの値を保存する辞書
    item_name = "不明"

    for label in labels:
        if label['Name'] == 'Credit Card':
            item_name = label_mapping['Credit Card']
            break  # 「クレジットカード」を見つけたら以降の処理をしない

        elif label['Name'] == 'ID Card':
            item_name = label_mapping['ID Card']

        # 他のラベルの処理
        elif label['Name'] == 'Electronics':
            item_name = label_mapping['Electronics']

        elif label['Name'] == 'Wristwatch':
            item_name = label_mapping['Wristwatch']

        elif label['Name'] == 'Mobile Phone':
            item_name = label_mapping['Mobile Phone']

        elif label['Name'] == 'Hat':
            item_name = label_mapping['Hat']

        elif label['Name'] == 'Scarf':
            item_name = label_mapping['Scarf']

        elif label['Name'] == 'Glove':
            item_name = label_mapping['Glove']

        elif label['Name'] == 'Key':
            item_name = label_mapping['Key']

        elif label['Name'] == 'Water Bottle':
            item_name = label_mapping['Water Bottle']

        elif label['Name'] == 'Shoe':
            item_name = label_mapping['Shoe']

        elif label['Name'] == 'Sock':
            item_name = label_mapping['Sock']

        elif label['Name'] == 'Underwear':
            item_name = label_mapping['Underwear']

        elif label['Name'] == 'Pants':
            item_name = label_mapping['Pants']

        elif label['Name'] == 'Jewelry':
            item_name = label_mapping['Jewelry']

        elif label['Name'] == 'Book':
            item_name = label_mapping['Book']

        elif label['Name'] == 'Suitcase':
            item_name = label_mapping['Suitcase']

        elif label['Name'] == 'Tobacco':
            item_name = label_mapping['Tobacco']

        elif label['Name'] == 'Lighter':
            item_name = label_mapping['Lighter']

        elif label['Name'] == 'Accessories':
            item_name = label_mapping['Accessories']

        elif label['Name'] == 'Camera':
            item_name = label_mapping['Camera']

        elif label['Name'] == 'Diaper':
            item_name = label_mapping['Diaper']

        elif label['Name'] == 'Contact Lens':
            item_name = label_mapping['Contact Lens']

        elif label['Name'] == 'Binoculars':
            item_name = label_mapping['Binoculars']

        elif label['Name'] == 'Light':
            item_name = label_mapping['Light']

        elif label['Name'] == 'Electrical Device':
            item_name = label_mapping['Electrical Device']

        elif label['Name'] == 'Plant':
            item_name = label_mapping['Plant']

        elif label['Name'] == 'Saucer':
            item_name = label_mapping['Saucer']

        elif label['Name'] == 'Tool':
            item_name = label_mapping['Tool']

        elif label['Name'] == 'Book':
            item_name = label_mapping['Book']

        elif label['Name'] == 'Suitcase':
            item_name = label_mapping['Suitcase']

        elif label['Name'] == 'Tobacco':
            item_name = label_mapping['Tobacco']

        elif label['Name'] == 'Underwear':
            item_name = label_mapping['Underwear']

        elif label['Name'] == 'Pants':
            item_name = label_mapping['Pants']

        elif label['Name'] == 'Jewelry':
            item_name = label_mapping['Jewelry']

        elif label['Name'] == 'Accessories':
            item_name = label_mapping['Accessories']

        elif label['Name'] == 'Camera':
            item_name = label_mapping['Camera']

        elif label['Name'] == 'Diaper':
            item_name = label_mapping['Diaper']

        elif label['Name'] == 'Body Part':
            item_name = label_mapping['Body Part']

        elif label['Name'] == 'Perfume':
            item_name = label_mapping['Perfume']

        elif label['Name'] == 'Photography':
            item_name = label_mapping['Photography']

        elif label['Name'] == 'Stick':
            item_name = label_mapping['Stick']

        elif label['Name'] == 'Medication':
            item_name = label_mapping['Medication']

        elif label['Name'] == 'Clothing':
            item_name = label_mapping['Clothing']

    return item_name


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
    img.save(img_byte_arr, format='JPEG', quality=10)  # Adjust quality as needed
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr


def upload_image(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if image and latitude and longitude:
            # 画像データをメモリに読み込む
            image_data = image.read()
            image_bytes_for_upload = io.BytesIO(image_data)  # S3アップロード用のファイルオブジェクト
            image_bytes_for_resize = io.BytesIO(image_data)  # リサイズ用のファイルオブジェクト

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
            image_bytes_for_resize.close()  # リサイズ用ファイルオブジェクトをクローズ

            # 画像ラベル検出
            labels = detect_labels_in_image(resized_image)

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


def upload_result(request):
    # セッションから context を取得
    context = request.session.pop('upload_context', {})  # デフォルトは空の辞書
    return render(request, 'app/upload_result.html', context)


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

def warning_page(request):
    return render(request, 'warning.html', {'message': '不適切な画像は登録できません。'})


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