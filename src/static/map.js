let zoomLevel = 3;
let latitude = 52.0116;
let longitude = 4.3571;
let SATELLITES = {
    "DELFI-PQ": '51074',
}

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

async function findSat() {
    fetch("/location/all/")
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



function updateSatMarker(sat, lat, long,) {


    fetch("/next_pass/"+ SATELLITES[sat]+"/")
    .then(response => response.json())
    .then(data => {
      pass_events = data.passes;

    //   for (let i = 0; i<pass_events.length; i++){
        riseTime = pass_events[0].rise_time;
        peakTime = pass_events[0].peak_time;
        setTime = pass_events[0].set_time;
        next_pass = 'Next pass over Delft (UTC) ' + '<br> Rise Time: ' + riseTime +
                                                         '<br> Peak Time: '+ peakTime +
                                                         '<br> Set Time: ' + setTime;
    //   }

    if (markers.hasOwnProperty(sat)){
        markers[sat].setLatLng([lat, long]);
        markers[sat].bindPopup(sat + " Lat: " + lat + " Long: " + long +"<br>"+ next_pass);
    }
    else{
        let marker = L.marker([lat, long]).addTo(map).bindPopup(sat + " Lat: " + lat + " Long: " + long +"<br>"+ next_pass).openPopup();
        markers[sat] = marker
    }


    }).catch(e => console.log(e));

// updates map view according to Marker's new position
// map.setView([lat, long]);
}

setInterval(findSat, refreshRate * 1000);
