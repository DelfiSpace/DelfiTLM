let zoomLevel = 3;
let latitude = 52.0116;
let longitude = 4.3571;
let SATELLITES = {
    "DELFI-PQ": '51074',
    "DELFI-N3XT": '39428',

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

function findSat() {
    fetch("/location/all/")
    .then(response => response.json())
    .then(data => {
      let satellite_list = data.satellites;
      console.log(satellite_list);

      for (const element of satellite_list){
        console.log(element);
        let sat = element.satellite
        let lat = element.latitude.toFixed(2);
        let long = element.longitude.toFixed(2);
        // let sunlit = element.sunlit;
        if (sat != null){
          updateSatMarker(sat, lat, long);
        }
      }
    }).catch(e => console.log(e));
}



function updateSatMarker(sat, lat, long,) {


    fetch("/next-pass/"+ SATELLITES[sat]+"/")
    .then(response => response.json())
    .then(data => {
      let pass_events = data.passes;

    //   for (let i = 0; i<pass_events.length; i++){
        let riseTime = pass_events[0].rise_time;
        let  peakTime = pass_events[0].peak_time;
        let setTime = pass_events[0].set_time;
        let next_pass = 'Next pass over Delft (UTC) ' + '<br> Rise Time: ' + riseTime +
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
