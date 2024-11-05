
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    // 位置情報取得関数
    function getLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                showPosition,
                showError
            );
        } else {
            alert("このブラウザでは位置情報がサポートされていません。");
        }
    }

    function showPosition(position) {
        document.getElementById('latitude').value = position.coords.latitude;
        document.getElementById('longitude').value = position.coords.longitude;
    }

    function showError(error) {
        const messages = {
            1: "位置情報の取得が拒否されました。",
            2: "位置情報が利用できません。",
            3: "位置情報の取得がタイムアウトしました。",
            0: "不明なエラーが発生しました。"
        };
        alert(messages[error.code]);
    }

    // 日時取得
    function getCurrentDateTime() {
        const now = new Date();
        return now.toISOString().slice(0, 19).replace("T", " ");
    }

    // ラベルマッピング辞書
    const labelMapping = {
        'Credit Card': 'クレジットカード',
        'ID Card': '証明書',
        'Electronics': '電子機器',
        'Phone': '携帯電話'
    };

    // 画面幅による条件分岐
    function checkWidth() {
        const windowWidth = window.innerWidth;
        if (windowWidth < 600) {
            // モバイル用処理
            document.body.classList.add('mobile');
        } else if (windowWidth < 1200) {
            // タブレット用処理
            document.body.classList.add('tablet');
        } else {
            // デスクトップ用処理
            document.body.classList.add('desktop');
        }
    }

    window.addEventListener('resize', checkWidth);

    // Blob変換処理
    function base64ToBlob(base64, mimeType = 'image/jpeg') {
        const byteString = atob(base64);
        const arrayBuffer = new ArrayBuffer(byteString.length);
        const intArray = new Uint8Array(arrayBuffer);
        for (let i = 0; i < byteString.length; i++) {
            intArray[i] = byteString.charCodeAt(i);
        }
        return new Blob([intArray], { type: mimeType });
    }

    // 画像ラベル検出およびリサイズ関数
    document.getElementById('image').onchange = async function(event) {
    const imageFile = event.target.files[0];
    if (!imageFile) return;

    // 圧縮前サイズの表示
    const originalFileSize = (imageFile.size / 1024 / 1024).toFixed(2);
    document.getElementById('beforeSize').textContent = `圧縮前サイズ: ${originalFileSize} MB`;

    // 圧縮設定
    const options = {
        maxSizeMB: 1,
        maxWidthOrHeight: 800,
        useWebWorker: true
    };

    try {
        // 画像圧縮処理
        const compressedFile = await imageCompression(imageFile, options);
        const compressedFileSize = (compressedFile.size / 1024 / 1024).toFixed(2);
        document.getElementById('afterSize').textContent = `圧縮後サイズ: ${compressedFileSize} MB`;

        // 圧縮後の画像をプレビュー表示
        const compressedDataUrl = await imageCompression.getDataUrlFromFile(compressedFile);
        document.getElementById('previewImage').src = compressedDataUrl;

        // 圧縮後の画像をBlob形式でラベル検出APIへ送信
        const detectFormData = new FormData();
        detectFormData.append('image', compressedFile, 'compressed_image.jpg');

        const detectResponse = await fetch('/detect_labels_api/', {
            method: 'POST',
            body: detectFormData,
            headers: { 'X-CSRFToken': csrftoken }
        });
        const detectData = await detectResponse.json();

        if (detectData.error) throw new Error(detectData.error);

        // ラベル検出結果を更新
        updateLabels(detectData.labels);
    } catch (error) {
        console.error('画像の処理中にエラーが発生しました:', error);
        alert("画像の処理中にエラーが発生しました。");
    }
};

    // BlobをBase64に変換する関数
    function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

    // ラベルの更新を行う関数
    function updateLabels(detectedLabels) {
    let itemName = '不明';
    detectedLabels.forEach(label => {
        if (labelMapping[label]) {
            if (label === 'Credit Card' || label === 'ID Card') {
                itemName = labelMapping[label];
            }
        }
    });
    document.getElementById('item_name').value = itemName;
    document.getElementById('detected_labels').innerHTML =
        `<p>検出されたラベル:</p>
        <ul>${detectedLabels.map(label => `<li>${label}</li>`).join('')}</ul>`;
}

    document.addEventListener('DOMContentLoaded', function() {
        getLocation();  // ページがロードされたときに位置情報を取得
        document.getElementById('found_time').value = getCurrentDateTime();  // 現在時刻を拾った時間に自動入力
        document.getElementById('image').onchange = detectLabelsAndResize;  // 画像が選択されたらリサイズとラベル検出
        checkWidth();  // 初回ロード時に画面幅をチェック
    });
