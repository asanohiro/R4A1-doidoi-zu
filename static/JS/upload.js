let compressedFileGlobal;

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
                navigator.geolocation.getCurrentPosition(showPosition, showError);
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

        function  previewImage(event) {
            const fileInput = event.target;
            const previewArea = document.getElementById('preview-area');

            if (fileInput.files && fileInput.files[0]) {
                const file = fileInput.files[0]
                const reader = new FileReader();

                reader.onload = function (e) {
                    previewArea.innerHTML = `<img src="${e.target.result}" alt="プレビュー画像" style="width: 200px; height: auto">`;
                };
                reader.readAsDataURL(file);
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            getLocation();
            document.getElementById('found_time').value = getCurrentDateTime();
        });