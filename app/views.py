import io
from datetime import datetime

import boto3
from PIL import Image
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
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
    'Accessories': 'アクセサリー',
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
# 47都道府県辞書
prefecture_mapping = {
    'Hokkaido': '北海道',
    'Aomori': '青森県',
    'Iwate': '岩手県',
    'Miyagi': '宮城県',
    'Akita': '秋田県',
    'Yamagata': '山形県',
    'Fukushima': '福島県',
    'Ibaraki': '茨城県',
    'Tochigi': '栃木県',
    'Gunma': '群馬県',
    'Saitama': '埼玉県',
    'Chiba': '千葉県',
    'Tokyo': '東京都',
    'Kanagawa': '神奈川県',
    'Niigata': '新潟県',
    'Toyama': '富山県',
    'Ishikawa': '石川県',
    'Fukui': '福井県',
    'Yamanashi': '山梨県',
    'Nagano': '長野県',
    'Gifu': '岐阜県',
    'Shizuoka': '静岡県',
    'Aichi': '愛知県',
    'Mie': '三重県',
    'Shiga': '滋賀県',
    'Kyoto': '京都府',
    'Osaka': '大阪府',
    'Hyogo': '兵庫県',
    'Nara': '奈良県',
    'Wakayama': '和歌山県',
    'Tottori': '鳥取県',
    'Shimane': '島根県',
    'Okayama': '岡山県',
    'Hiroshima': '広島県',
    'Yamaguchi': '山口県',
    'Tokushima': '徳島県',
    'Kagawa': '香川県',
    'Ehime': '愛媛県',
    'Kochi': '高知県',
    'Fukuoka': '福岡県',
    'Saga': '佐賀県',
    'Nagasaki': '長崎県',
    'Kumamoto': '熊本県',
    'Oita': '大分県',
    'Miyazaki': '宮崎県',
    'Kagoshima': '鹿児島県',
    'Okinawa': '沖縄県'
}

# ラベルのマッピングとフォームへの反映
def extract_relevant_labels(labels):
    item_name = None
    for label in labels:
        if label['Name'] == 'Accessories':
            item_name = label_mapping['Accessories']
            break
        elif label['Name'] == 'Animal':
            item_name = label_mapping['Animal']
            break
        elif label['Name'] == 'Bag':
            item_name = label_mapping['Bag']
            break
        elif label['Name'] == 'Binoculars':
            item_name = label_mapping['Binoculars']
            break
        elif label['Name'] == 'Book':
            item_name = label_mapping['Book']
            break
        elif label['Name'] == 'Camera':
            item_name = label_mapping['Camera']
            break
        elif label['Name'] == 'Clothing':
            item_name = label_mapping['Clothing']
            break
        elif label['Name'] == 'Computer Hardware':
            item_name = label_mapping['Computer Hardware']
            break
        elif label['Name'] == 'Contact Lens':
            item_name = label_mapping['Contact Lens']
            break
        elif label['Name'] == 'Cosmetics':
            item_name = label_mapping['Cosmetics']
            break
        elif label['Name'] == 'Credit Card':
            item_name = label_mapping['Credit Card']
            break
        elif label['Name'] == 'Diaper':
            item_name = label_mapping['Diaper']
            break
        elif label['Name'] == 'Electrical Device':
            item_name = label_mapping['Electrical Device']
            break
        elif label['Name'] == 'Electronics':
            item_name = label_mapping['Electronics']
            break
        elif label['Name'] == 'Envelope':
            item_name = label_mapping['Envelope']
            break
        elif label['Name'] == 'Glasses':
            item_name = label_mapping['Glasses']
            break
        elif label['Name'] == 'Glove':
            item_name = label_mapping['Glove']
            break
        elif label['Name'] == 'Hat':
            item_name = label_mapping['Hat']
            break
        elif label['Name'] == 'ID Card':
            item_name = label_mapping['ID Card']
            break
        elif label['Name'] == 'Jewelry':
            item_name = label_mapping['Jewelry']
            break
        elif label['Name'] == 'Key':
            item_name = label_mapping['Key']
            break
        elif label['Name'] == 'Light':
            item_name = label_mapping['Light']
            break
        elif label['Name'] == 'Lighter':
            item_name = label_mapping['Lighter']
            break
        elif label['Name'] == 'Medication':
            item_name = label_mapping['Medication']
            break
        elif label['Name'] == 'Mobile Phone':
            item_name = label_mapping['Mobile Phone']
            break
        elif label['Name'] == 'Money':
            item_name = label_mapping['Money']
            break
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

def prefecture_change_japan(prefecture):
    prefecture_name = None
    if prefecture == 'Hokkaido':
        prefecture_name = prefecture_mapping['Hokkaido']
    elif prefecture == 'Aomori':
        prefecture_name = prefecture_mapping['Aomori']
    elif prefecture == 'Iwate':
        prefecture_name = prefecture_mapping['Iwate']
    elif prefecture == 'Miyagi':
        prefecture_name = prefecture_mapping['Miyagi']
    elif prefecture == 'Akita':
        prefecture_name = prefecture_mapping['Akita']
    elif prefecture == 'Yamagata':
        prefecture_name = prefecture_mapping['Yamagata']
    elif prefecture == 'Fukushima':
        prefecture_name = prefecture_mapping['Fukushima']
    elif prefecture == 'Ibaraki':
        prefecture_name = prefecture_mapping['Ibaraki']
    elif prefecture == 'Tochigi':
        prefecture_name = prefecture_mapping['Tochigi']
    elif prefecture == 'Gunma':
        prefecture_name = prefecture_mapping['Gunma']
    elif prefecture == 'Saitama':
        prefecture_name = prefecture_mapping['Saitama']
    elif prefecture == 'Chiba':
        prefecture_name = prefecture_mapping['Chiba']
    elif prefecture == 'Tokyo':
        prefecture_name = prefecture_mapping['Tokyo']
    elif prefecture == 'Kanagawa':
        prefecture_name = prefecture_mapping['Kanagawa']
    elif prefecture == 'Niigata':
        prefecture_name = prefecture_mapping['Niigata']
    elif prefecture == 'Toyama':
        prefecture_name = prefecture_mapping['Toyama']
    elif prefecture == 'Ishikawa':
        prefecture_name = prefecture_mapping['Ishikawa']
    elif prefecture == 'Fukui':
        prefecture_name = prefecture_mapping['Fukui']
    elif prefecture == 'Yamanashi':
        prefecture_name = prefecture_mapping['Yamanashi']
    elif prefecture == 'Nagano':
        prefecture_name = prefecture_mapping['Nagano']
    elif prefecture == 'Gifu':
        prefecture_name = prefecture_mapping['Gifu']
    elif prefecture == 'Shizuoka':
        prefecture_name = prefecture_mapping['Shizuoka']
    elif prefecture == 'Aichi':
        prefecture_name = prefecture_mapping['Aichi']
    elif prefecture == 'Mie':
        prefecture_name = prefecture_mapping['Mie']
    elif prefecture == 'Shiga':
        prefecture_name = prefecture_mapping['Shiga']
    elif prefecture == 'Kyoto':
        prefecture_name = prefecture_mapping['Kyoto']
    elif prefecture == 'Osaka':
        prefecture_name = prefecture_mapping['Osaka']
    elif prefecture == 'Hyogo':
        prefecture_name = prefecture_mapping['Hyogo']
    elif prefecture == 'Nara':
        prefecture_name = prefecture_mapping['Nara']
    elif prefecture == 'Wakayama':
        prefecture_name = prefecture_mapping['Wakayama']
    elif prefecture == 'Tottori':
        prefecture_name = prefecture_mapping['Tottori']
    elif prefecture == 'Shimane':
        prefecture_name = prefecture_mapping['Shimane']
    elif prefecture == 'Okayama':
        prefecture_name = prefecture_mapping['Okayama']
    elif prefecture == 'Hiroshima':
        prefecture_name = prefecture_mapping['Hiroshima']
    elif prefecture == 'Yamaguchi':
        prefecture_name = prefecture_mapping['Yamaguchi']
    elif prefecture == 'Tokushima':
        prefecture_name = prefecture_mapping['Tokushima']
    elif prefecture == 'Kagawa':
        prefecture_name = prefecture_mapping['Kagawa']
    elif prefecture == 'Ehime':
        prefecture_name = prefecture_mapping['Ehime']
    elif prefecture == 'Kochi':
        prefecture_name = prefecture_mapping['Kochi']
    elif prefecture == 'Fukuoka':
        prefecture_name = prefecture_mapping['Fukuoka']
    elif prefecture == 'Saga':
        prefecture_name = prefecture_mapping['Saga']
    elif prefecture == 'Nagasaki':
        prefecture_name = prefecture_mapping['Nagasaki']
    elif prefecture == 'Kumamoto':
        prefecture_name = prefecture_mapping['Kumamoto']
    elif prefecture == 'Oita':
        prefecture_name = prefecture_mapping['Oita']
    elif prefecture == 'Miyazaki':
        prefecture_name = prefecture_mapping['Miyazaki']
    elif prefecture == 'Kagoshima':
        prefecture_name = prefecture_mapping['Kagoshima']
    elif prefecture == 'Okinawa':
        prefecture_name = prefecture_mapping['Okinawa']

    return prefecture_name


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

            # Get the prefecture from location data
            prefecture = get_prefecture_from_location(latitude, longitude)
            prefecture_jp = prefecture_change_japan(prefecture)


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
                'prefecture': prefecture_jp,
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
  try:
    # クエリパラメータの取得
    item_name = request.GET.get('item_name', '').strip()
    prefecture = request.GET.get('prefecture', '').strip()
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # 日時の比較
    if start_date and end_date:
      start_date_obj = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
      end_date_obj = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
      if end_date_obj < start_date_obj:
        return JsonResponse({'error': '日時が正しくありません'}, status=400)

    # 基本のフィルタリング
    items = LostItem.objects.all()
    if item_name:
      items = items.filter(description__icontains=item_name)
    if prefecture:
      items = items.filter(prefecture__icontains=prefecture)

    # 日時検索のフィルタリング
    if start_date:
      start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
      items = items.filter(date_time__gte=start_date)
    if end_date:
      end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
      items = items.filter(date_time__lte=end_date)

    # 結果のシリアライズ
    items_data = [
      {
        'id': item.id,
        'date_time': item.date_time.strftime('%Y-%m-%d %H:%M:%S'),
        'description': item.description,
        'image_url': item.image_url if item.image_url else None,
        'latitude': float(item.latitude),
        'longitude': float(item.longitude),
        'prefecture': item.prefecture,
      }
      for item in items
    ]

    return JsonResponse(items_data, safe=False)
  except Exception as e:
    # エラーログの出力
    print(f"Error in search_items: {e}")
    return JsonResponse({'error': str(e)}, status=500)

def item_detail(request, item_id):
    item = get_object_or_404(LostItem, id=item_id)
    return render(request, 'item_detail.html', {'item': item})
