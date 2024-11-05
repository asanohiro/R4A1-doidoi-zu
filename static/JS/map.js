function initMap() {
    var map = new google.maps.Map(document.getElementById('map'), {
        zoom: 10,
        center: { lat: 35.6895, lng: 139.6917 }  // Tokyo center
    });

    try {
    JSON.parse(items_json);
}
catch (error) {
    console.log('Error parsing JSON:', error, items_json);
}

    try {
        items.forEach(function(item) {
            var fields = item.fields;
            if (fields.latitude && fields.longitude) {
                var latLng = new google.maps.LatLng(parseFloat(fields.latitude), parseFloat(fields.longitude));
                var marker = new google.maps.Marker({
                    position: latLng,
                    map: map,
                    title: fields.description
                });

                var infoWindow = new google.maps.InfoWindow({
                    content: `<img src="${fields.image_url || ''}" alt="Lost Item" style="width:100px;height:100px;"><p>${fields.description}</p><p>${fields.date_time}</p>`
                });

                marker.addListener('click', function() {
                    infoWindow.open(map, marker);
                });
            } else {
                console.error('Latitude or longitude data is missing for item:', fields.description);
            }
        });
    } catch (e) {
        console.error("Error in iterating items:", e);
    }
}

function validateSearch() {
    var itemSelect = document.getElementById('item_name');
    var prefectureSelect = document.getElementById('prefecture');
    if (itemSelect.value !== '' || prefectureSelect.value !== '') {
        return true;
    } else {
        alert("品名または都道府県を選択してください。");
        return false;
    }
}