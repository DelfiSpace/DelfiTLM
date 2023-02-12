let zoomLevel = 3;
let latitude = 52.0116;
let longitude = 4.3571;

// refresh rate in seconds
const refreshRate = 2;

let map = L.map('map').setView([latitude, longitude], zoomLevel);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

let sunlightOverlay = L.terminator();
sunlightOverlay.addTo(map);

setInterval(function(){updateTerminator(sunlightOverlay)}, refreshRate * 1000);

function updateTerminator(t) {
  t.setTime();
}

let markers = {}

function findSat(noradID) {
    fetch("/location/" + noradID + "/")
    .then(response => response.json())
    .then(data => {
    satellite_list = data.satellites;

    for (let i = 0; i<satellite_list.length; i++){
        sat = satellite_list[i].satellite
        lat = satellite_list[i].latitude.toFixed(2);
        long = satellite_list[i].longitude.toFixed(2);
        sunlit = satellite_list[i].sunlit;

        updateSatMarker(sat, lat, long);
        }
    }).catch(e => console.log(e));
}


function updateSatMarker(sat, lat, long) {

    if (markers.hasOwnProperty(sat)){
        markers[sat].setLatLng([lat, long]);
        markers[sat].bindPopup(sat + " Lat: " + lat + " Long: " + long);
    }
    else{
        let marker = L.marker([lat, long]).addTo(map).bindPopup(sat + " Lat: " + lat + " Long: " + long).openPopup();
        markers[sat] = marker
    }

// updates map view according to Marker's new position
// map.setView([lat, long]);
}

setInterval(findSat("all"), refreshRate * 1000);
