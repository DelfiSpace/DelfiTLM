let zoomLevel = 3;
let latitude = 52.0116;
let longitude = 4.3571;

// refresh rate in seconds
const refreshRate = 2;

let map = L.map('map',{
    noWrap: true,
    autoPan: false,
    zoomSnap: 0.1,
    maxBounds: [
      [-90.0, -180.0],
      [90.0, 180.0]],
    maxBoundsViscosity: 1.0
    }).setView([0, 0], 0);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	noWrap: true,
	autoPan: false
    }).addTo(map);

// use an icon to show the satellite position
var satellite = L.icon({
    iconUrl: 'static/satellite.webp',
    iconSize:     [116, 87], // size of the icon
    iconAnchor:   [58, 43], // point of the icon which will correspond to marker's location
    popupAnchor:  [0, -21] // point from which the popup should open relative to the iconAnchor
});

// add the solar terminator
let sunlightOverlay = L.terminator({resolution: 5, longitudeRange:360});
sunlightOverlay.addTo(map);

// update the solar terminator periodically
function updateTerminator(t) 
{
    t.setTime();
}
setInterval(function(){updateTerminator(sunlightOverlay)}, refreshRate * 1000);

// limit the zoom value to display the full Earth only once
function setMinimumZoom(map)
{
    let minZoom = 1.0 / 10.0 * Math.ceil(10 * Math.log2(Math.min(map.getSize().x, map.getSize().y) / 256))
    map.setMinZoom(minZoom);
}
setMinimumZoom(map);

let markers = {}

// display the satellites on the map
function findSat() {
    fetch("/location/all/")
    .then(response => response.json())
    .then(data => {
      let satellite_list = data.satellites;

      for (const element of satellite_list){
        let sat = element.satellite;
        let lat = element.latitude.toFixed(2);
        let long = element.longitude.toFixed(2);
        let norad_id = element.norad_id;
        // let sunlit = element.sunlit;
        if (sat != null){
          updateSatMarker(sat, norad_id, lat, long);
        }
      }
    }).catch(e => console.log(e));
}

function updateSatMarker(sat, norad_id, lat, long,) {
    fetch("/next-pass/"+ norad_id + "/")
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
        //markers[sat].bindPopup(sat + " Lat: " + lat + " Long: " + long +"<br>"+ next_pass);
        //markers[sat].bindPopup(sat, {autoPan: false});
    }
    else{
        //let marker = L.marker([lat, long], {icon: satellite}).addTo(map).bindPopup(sat + " Lat: " + lat + " Long: " + long +"<br>"+ next_pass);
        let marker = L.marker([lat, long], {icon: satellite, autoPan: false}).addTo(map).bindPopup(sat).openPopup();
        markers[sat] = marker
    }


    }).catch(e => console.log(e));
}

findSat();

// automatically update the satellite positions
setInterval(findSat, refreshRate * 1000);

// automatically update the minimum zoom if the map is resized
map.on('resize', function ()
    {
        setMinimumZoom(map);
    });

