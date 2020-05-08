import _ from 'lodash';
import L from 'leaflet';
import 'leaflet-routing-machine';
import './style.css';
import 'leaflet/dist/leaflet.css';
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: iconRetina,
  iconUrl: icon,
  shadowUrl: iconShadow,
});


const apiUri = process.env.APP_API_URI;
const element = document.createElement('div');
element.id = 'map';
document.body.appendChild(element);

//element.innerHTML = _.join(['Hello', 'webpack'], ' ');
var map = L.map(element).setView(/*[56, 13]*/ [55.665193184436035, 13.355383872985841], 14);

console.log(L);

const Velorouter = L.Class.extend({
  route: function(waypoints, callback, context, options) {
    console.log(waypoints);

    let query = {
      waypoints: waypoints.map(waypoint => waypoint.latLng),
    }
    fetch(apiUri + '/api/route', {
      method: 'POST',
      body: JSON.stringify(query),
    })
    .then(response => response.json())
    .then(data => {
      //console.log(data);
      //const coordinates = data.features.map(feature => L.GeoJSON.coordsToLatLngs(feature.geometry.coordinates)).flat()
      const result = data.map(route => {
        const coordinates = route.segments.map(segment => L.GeoJSON.coordsToLatLngs(segment.coords)).flat();
        //L.polyline(coordinates, {color: 'green'}).addTo(map);
        return {
          name: 'Foo',
          summary: {totalTime: 1337, totalDistance: 42},
          coordinates: coordinates,
          inputWaypoints: waypoints,
          waypoints: [],
          instructions: [],
        }
      });

      //console.log(result);
      callback.call(context, null, result);
    })
    .catch(error => {
      callback.call(context, error, null);
    });
  }
});

var routing = new L.Routing.control({
  waypoints: [
    L.latLng(55.665193184436035, 13.355383872985841),
    L.latLng(55.66727479751119, 13.340320587158205)
  ],
  router: new Velorouter({foo: 'bar'}),
}).addTo(map);

var dark = L.tileLayer('https://api.maptiler.com/maps/darkmatter/{z}/{x}/{y}.png?key=jrAoRNrX6nfYt6nZNnnW', {
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

/*
var route = null;

map.on('click', async (ev) => {
  console.log(ev);
  if (route)
    map.removeLayer(route);
  let query = {
    start: {lat: 55.65760706736028, lng: 13.357245326042177},
    end: ev.latlng,
  }
  const response = await fetch(apiUri + '/api/route', {
    method: 'POST',
    body: JSON.stringify(query),
  });
  const data = await response.json();
  console.log(data);
  route = L.geoJSON(data).addTo(map);

});
*/
