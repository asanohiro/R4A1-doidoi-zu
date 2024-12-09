import io
import re
from datetime import datetime

import boto3
from PIL import Image
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
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
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

PROJECT_VERSION_ARN = env('PROJECT_VERSION_ARN')

DUMMY_IMAGE_URL = 'https://placehold.jp/200x200.png'

def index(request):
    return render(request, 'index.html')

def map(request):
  return render(request, 'app/map.html')

def return_upload_image(request):
    return render(request, 'app/upload.html')

def warning_page(request):
    return render(request,'warning.html')

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
    'Bag': 'バック',
    'Binoculars': '双眼鏡',
    'Book': '本',
    'Camera': 'カメラ',
    'Contact Lens': 'コンタクトレンズ',
    'Credit Card': 'クレジットカード',
    'Can': '缶',
    'Diaper': 'おむつ',
    'Education': '教科書',
    'Envelope': '封筒',
    'Everyday objects': '日用品',
    'Glasses': '眼鏡',
    'Glove': '手袋',
    'Hat': '帽子',
    'ID Card': '証明書',
    'Jewelry': 'ジュエリー',
    'Key': '鍵',
    'Light': 'ライト',
    'Lighter': 'ライター',
    'Medication': '薬',
    'Money': 'お金',
    'Musical Instrument': '楽器',
    'Page': '書類',
    'Pants': 'パンツ',
    'Perfume': '香水',
    'Raincoat': '合羽',
    'Saucer': '皿',
    'Scarf': 'マフラー',
    'Shoe': '靴',
    'Sock': '靴下',
    'Stick': '杖',
    'Suitcase': 'スーツケース',
    'Telescope': '望遠鏡',
    'Tobacco': 'タバコ',
    'Toy': '人形',
    'Toys and Gaming': 'おもちゃ',
    'Umbrella': '傘',
    'Underwear': '下着',
    'Wallet': '財布',
    'Water Bottle': '水筒',
    'Wristwatch': '腕時計',
    # 他に必要なラベルをここに追加
}
#ラベルのみ
label_words = [
    'Bag', 'Binoculars', 'Book', 'Camera', 'Can',
    'Contact Lens', 'Credit Card', 'Diaper', 'Education', 'Envelope', 'Everyday objects',
    'Glasses', 'Glove', 'Hat', 'ID Card', 'Jewelry', 'Key',
    'Light', 'Lighter', 'Medication', 'Mobile Phone', 'Money','Musical Instrument',
    'Page', 'Pants', 'Perfume', 'Raincoat', 'Saucer', 'Scarf',
    'Shoe', 'Sock', 'Stick', 'Suitcase', 'Telescope', 'Tobacco','Toy','Toys and Gaming',
    'Umbrella', 'Underwear', 'Wallet', 'Water Bottle', 'Wristwatch'
]
#カテゴリ辞書
category_mapping = {
    'Accessories': 'アクセサリー',
    'Clothing': '衣服',
    'Computer Hardware': '機械',
    'Cosmetics': '化粧品',
    'Electrical Device': '電気機器',
    'Electronics': '電子機器',
    'Photography': '写真',
    'Plant': '植物',
    'Tool': '工具'
}
#カテゴリラベルのみ
category_labels = [
        'Accessories', 'Clothing', 'Computer Hardware',
        'Cosmetics', 'Electrical Device', 'Electronics',
        'Photography', 'Plant', 'Tool'
    ]
# 不適切なラベル辞書
INAPPROPRIATE_LABELS = {
    'Face','Animal','Weapon','Food', 'Credit Card'
}
# ダミー画像を用いて登録する単語リスト
dummy_labels = {
    'Credit Card', 'ID Card'
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
        if label['Name'] in label_mapping:
            item_name = label_mapping[label['Name']]
            break

    if item_name is None:
        for label in labels:
            if label['Name'] in category_labels:
                item_name = category_mapping[label['Name']]
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
        comment = request.POST.get('comment')

        if image and latitude and longitude:
            # 画像データをメモリに読み込む
            image_data = image.read()
            image_bytes_for_upload = io.BytesIO(image_data)  # S3アップロード用のファイルオブジェクト
            image_bytes_for_resize = io.BytesIO(image_data)  # リサイズ用のファイルオブジェクト

            # Get the prefecture from location data
            prefecture = get_prefecture_from_location(latitude, longitude)
            prefecture_jp = prefecture_change_japan(prefecture)

            # Generate a unique filename
            file_extension = image.name.split('.')[-1]
            file_name = f'{uuid4()}.{file_extension}'

            # 画像サイズのリサイズ
            resized_image = resize_image(image_bytes_for_resize)
            resized_image_io = io.BytesIO(resized_image)
            image_bytes_for_resize.close()  # リサイズ用ファイルオブジェクトをクローズ

            # 画像ラベル検出
            labels = detect_labels_in_image(resized_image_io)
            label_test = labels

            #ラベル検出が完了した場合の処理
            detected_inappropriate_labels = any(label['Name'] in INAPPROPRIATE_LABELS for label in labels)
            print("Detected inappropriate labels:", detected_inappropriate_labels)

            if detected_inappropriate_labels:
                matched_labels = [label['Name'] for label in labels if label['Name'] in dummy_labels]
                print("Matched labels:", matched_labels)

                if matched_labels:
                    try:
                        response = requests.get(DUMMY_IMAGE_URL)
                        response.raise_for_status()

                        dummy_image = io.BytesIO(response.content)
                        s3.upload_fileobj(dummy_image, bucket_name, file_name)

                        end_label = extract_relevant_labels(labels)

                        image_url = f'https://{bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{file_name}'
                        context = {
                            'item_name': end_label,
                            'latitude': latitude,
                            'longitude': longitude,
                            'prefecture': prefecture_jp,
                            'image_url': image_url,
                            'comment': comment,
                        }
                        print("Rendering upload_dummy.html with context:", context)
                        return render(request, 'app/upload_dummy.html', context)
                    except Exception as e:
                        print("Error during dummy image processing:", str(e))
                else:
                    print("No matched labels found. Redirecting to warning_page.")
                    return redirect('warning_page')

            # 画像をS3にアップロード
            s3.upload_fileobj(image_bytes_for_upload, bucket_name, file_name)
            image_bytes_for_upload.close()  # アップロード用ファイルオブジェクトをクローズ

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
                'comment': comment,
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
        comment = request.POST.get('comment')
        nickname = request.session.get('nickname')

        if nickname == 'null' or nickname is None:
            nickname = 'guest'

        # LostItemに保存
        lost_item = LostItem.objects.create(
            image_url=image_url,
            latitude=latitude,
            longitude=longitude,
            product=item_name,
            prefecture=prefecture,
            comment=comment,
            nickname = nickname
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
      items = items.filter(product__icontains=item_name)
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
        'product': item.product,
        'image_url': item.image_url if item.image_url else None,
        'latitude': float(item.latitude),
        'longitude': float(item.longitude),
        'prefecture': item.prefecture,
        'comment': item.comment
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
    context = {
        'item': item,
        'google_maps_api_key': AWS.settings.env('GOOGLE_MAPS_API_KEY')
    }
    return render(request, 'app/item_detail.html', context)

def item_detail(request, item_id):
  item = get_object_or_404(LostItem, id=item_id)
  user = None  # user 変数を初期化
  user_nickname = request.session.get('nickname')

  if user_nickname:
    user = User.objects.get(nickname=user_nickname)

  return render(request, 'app/item_detail.html', {'item': item, 'user': user})


def login(request):
  if request.method == 'GET':
    return render(request, 'app/login.html')
  elif request.method == 'POST':
    email = request.POST.get('email')
    password = request.POST.get('password')
    try:
      if email and password:
        user = User.objects.get(email=email)
      else:
        return redirect('login')

        # パスワードをチェック
      if password == user.password:
        request.session['nickname'] = user.nickname
        request.session['email'] = user.email
        request.session['password'] = user.password
        return render(request, 'index.html')
      else:
        # パスワードが一致しない場合
        return render(request, 'app/login.html', {'error': 'メールアドレスかパスワードが違います'})
    except User.DoesNotExist:

      return render(request, 'app/login.html', {'error': 'メールアドレスかパスワードが違います'})


def User_register(request):
  if request.method == 'GET':
    return render(request, 'app/User_register.html')

  elif request.method == 'POST':
    nickname = request.POST.get('nickname')
    email = request.POST.get('email')
    password1 = request.POST.get('password1')
    password2 = request.POST.get('password2')

    # メールアドレスの重複チェック
    if User.objects.filter(email=email).exists():
      return render(request, 'app/User_register.html', {'error': 'このメールアドレスはすでに登録されています'})

    # ニックネームの重複チェック
    if User.objects.filter(nickname=nickname).exists():
      return render(request, 'app/User_register.html', {'error': 'このニックネームはすでに使用されています'})

    # ニックネームの検証（英数字を必ず含む）
    if not re.match(r'^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z0-9]+$', nickname):
      return render(request, 'app/User_register.html',
                    {'error': 'ニックネームは英字と数字をそれぞれ1文字以上含む必要があります'})

    # パスワードの検証（8文字以上で英数字を必須）
    if len(password1) < 8 or not re.match(r'^(?=.*[a-zA-Z])(?=.*\d).+$', password1):
      return render(request, 'app/User_register.html',
                    {'error': 'パスワードは8文字以上で、英字と数字を必ず含む必要があります'})

    # パスワードの一致確認
    if password1 != password2:
      return render(request, 'app/User_register.html', {'error': 'パスワードが一致しません'})

    # 確認画面へ遷移
    context = {
      'nickname': nickname,
      'email': email,
      'password': password1,
    }
    return render(request, 'app/User_register_confirm.html', context)


def User_register_confirm(request):
  if request.method == 'POST':
    try:
      nickname = request.POST.get('nickname')
      email = request.POST.get('email')
      password = request.POST.get('password')

      if not nickname or not email or not password:
        return render(request, 'app/User_register_confirm.html', {'error': 'すべての項目を入力してください'})

      user = User.objects.create(
        nickname=nickname,
        email=email,
        password=password
      )
      user.save()
      return render(request, 'app/User_register_complete.html')
    except Exception as e:
      return render(request, 'app/User_register_confirm.html', {'error': f'登録中にエラーが発生しました: {str(e)}'})


def logout(request):
  # セッションから情報を削除
  request.session.flush()  # すべてのセッションデータを削除
  return redirect('index')  # ログインページにリダイレクト


from django.shortcuts import render, get_object_or_404, redirect
from .models import User, ChatRoom, Message


def chat_room_list(request):
  # セッションからログインしているユーザーのnicknameを取得
  user1_nickname = request.session.get('nickname')

  # nicknameに基づいてUserオブジェクトを取得
  user1 = get_object_or_404(User, nickname=user1_nickname)

  # 過去にチャットしたチャットルームを検索（user1がuser2側にいる場合も考慮）
  past_chat_rooms = ChatRoom.objects.filter(user1=user1) | ChatRoom.objects.filter(user2=user1)

  past_users = []

  # 過去にチャットしたユーザーとそのチャットルームIDをリストに追加
  for chatroom in past_chat_rooms:
    # user1以外のユーザー（user2）を取得
    other_user = chatroom.user2 if chatroom.user1 == user1 else chatroom.user1
    past_users.append({
      'nickname': other_user.nickname,
      'chatroom_id': chatroom.id  # チャットルームIDを追加
    })

  # 結果を渡してチャットルーム画面を表示
  return render(request, 'app/past_chatroom_list.html', {
    'past_users': past_users
  })


def chat_room_check(request):
  user1_nickname = request.session.get('nickname')  # ログイン中のユーザー
  user2_nickname = request.GET.get('register')  # アイテム登録者

  user1 = User.objects.filter(nickname=user1_nickname).first()
  user2 = User.objects.filter(nickname=user2_nickname).first()

  # アイテム登録者が'guest'の場合、チャットルーム作成不可
  if user2_nickname == 'guest':
      return JsonResponse({'error': '登録者がゲストユーザーなのでチャットができません。'})

  if user1 == user2:
    return JsonResponse({'error': 'ログインユーザーと登録者が一致しているため、チャットルームは作成できません。'})

  if user1 and user2:
    chat_room = ChatRoom.objects.filter(
      Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
    ).first()

    if chat_room:
      return JsonResponse({'chatRoomId': chat_room.id})
    else:
      return JsonResponse({'chatRoomId': None})

  if user1 is None:
    return JsonResponse({'error': 'ゲストユーザーのため、チャット機能がご利用できません。'})

  return JsonResponse({'error': 'ユーザー情報が不正です。'})


def chat_room_create(request):
  # クエリパラメータからユーザー1とユーザー2を取得
  user1_nickname = request.session.get('nickname')
  user2_nickname = request.GET.get('register')
  item_id = request.POST.get('itemId')

  if user2_nickname == 'guest':
      return HttpResponse("登録者がゲストユーザーのためチャットができません。", status=400)

  if not user1_nickname or not user2_nickname:
    # 必要なパラメータが不足している場合、エラーメッセージを表示
    return HttpResponse("ユーザー情報が不足しています。", status=400)

  # チャットルームが既に存在するか確認
  existing_chat_room = ChatRoom.objects.filter(user1__nickname=user1_nickname, user2__nickname=user2_nickname).first()

  if existing_chat_room:
    # 既存のチャットルームが見つかった場合
    return redirect('chat-room', chat_room_id=existing_chat_room.id,item_id=item_id)
  else:
    # 新しいチャットルームを作成
    user1 = User.objects.get(nickname=user1_nickname)
    user2 = User.objects.get(nickname=user2_nickname)

    new_chat_room = ChatRoom.objects.create(user1=user1, user2=user2)

    # 新しいチャットルームの詳細ページにリダイレクト
    return redirect('chat-room', chat_room_id=new_chat_room.id)


def chat_room(request, chat_room_id):
  # チャットルームを取得
  chatroom = get_object_or_404(ChatRoom, id=chat_room_id)

  # 現在ログインしているユーザーを取得
  user = request.session.get('nickname')
  user1 = get_object_or_404(User, nickname=user)

  # チャットルーム内で他のユーザーをユーザー2として設定
  # (ユーザー1以外のユーザーがユーザー2に設定される想定)
  user2 = chatroom.user1 if chatroom.user2 == user1 else chatroom.user2

  # チャットルームのメッセージを取得
  messages = chatroom.messages.all().order_by('timestamp')

  return render(request, 'app/chatroom.html', {
    'chatroom': chatroom,
    'messages': messages,
    'user1': user1,
    'user2': user2,
  })


def send_message(request, chatroom_id):
  chatroom = get_object_or_404(ChatRoom, id=chatroom_id)
  sender_nickname = request.session.get('nickname')
  sender = User.objects.get(nickname=sender_nickname)

  # POSTリクエストが送信された場合
  if request.method == 'POST':
    text = request.POST.get('text')  # フォームから送信されたテキスト

    if text:
      # メッセージをデータベースに保存
      Message.objects.create(
        chatroom=chatroom,
        sender=sender,
        text=text
      )

      # メッセージ送信後、適切なチャットルームにリダイレクト
      # チャットルーム内のユーザーに基づきリダイレクト先を決定
      recipient_nickname = chatroom.user2.nickname if chatroom.user1 == request.user else chatroom.user1.nickname
      return redirect('chat-room', chat_room_id=chatroom.id)  # チャットルームにリダイレクト

  # GETリクエストの場合（直接ページにアクセスした場合）はフォームを表示
  return render(request, 'app/chatroom.html', {
    'chatroom': chatroom,
    'messages': chatroom.messages.all().order_by('timestamp'),  # チャットメッセージを順番に表示
  })

@receiver(post_save, sender=Message)
def notify_user_on_new_message(sender, instance, created, **kwargs):
    if created:  # 新しいメッセージが作成された場合のみ通知
        # 送信者が user1 なら user2 に通知し、逆も同様
        chatroom = instance.chatroom
        recipient = chatroom.user2 if instance.sender == chatroom.user1 else chatroom.user1

        if recipient.email:  # メールアドレスが登録されている場合のみ通知
            send_mail(
                subject=f"{instance.sender.nickname}からメッセージが届きました",
                message=f"{instance.sender.nickname}から新しいメッセージが届きました。\n内容: {instance.text}",
                from_email="doidoiis.sotuken@gmail.com",  # 送信元メールアドレス
                recipient_list=[recipient.email],
                fail_silently=False,
            )

