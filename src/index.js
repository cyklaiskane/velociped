import _ from 'lodash';
import L from 'leaflet';
import 'leaflet.vectorgrid'
import 'leaflet-routing-machine';
import 'leaflet-control-geocoder';

import {buildGPX, BaseBuilder} from 'gpx-builder';

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

const tsStyles = {
  C1: {color: '#5e96a8', opacity: 1, weight: 5},
  C2: {color: '#C49949', opacity: 1, weight: 5},
  C3: {color: '#5e96a8', opacity: 1, weight: 5},
  B1: {color: '#61b9bd', opacity: 1, weight: 4},
  B2: {color: '#b5dfe1', opacity: 1, weight: 4},
  B3: {color: '#ff8b9e', opacity: 1, weight: 4},
  B4: {color: '#a7616d', opacity: 1, weight: 4},
  B5: {color: '#808080', opacity: 1, weight: 4},
  G1: {color: '#c4b79f', opacity: 1, weight: 4},
  G2: {color: '#c4b79f', opacity: 1, weight: 4},
}

const vtStyles = {
  roads: function(properties, zoom, geometryDimension) {
    let style = tsStyles[properties.ts_klass] || {color: 'grey', opacity: 1, weight: 3};
    //style.weight = style.weight * zoom / 18;
    //console.log(style.weight * zoom / 18);
    return {
      color: style.color,
      opacity: 0.7,
      weight: 0.4 * style.weight * (Math.tanh(zoom / 3 - 5) + 1),
    };
  }
};

const darkmatter = L.tileLayer('https://api.maptiler.com/maps/darkmatter/{z}/{x}/{y}.png?key=jrAoRNrX6nfYt6nZNnnW', {
  attribution: '© OpenStreetMap contributors'
})

const mvt = L.vectorGrid.protobuf('http://localhost:8000/tiles/{z}/{x}/{y}.pbf', {
  renderFactory: L.canvas.tile,
  vectorTileLayerStyles: vtStyles,
});

const tsTiles = L.tileLayer('http://localhost:3000/styles/velo/{z}/{x}/{y}.png', {

});

//element.innerHTML = _.join(['Hello', 'webpack'], ' ');
var map = L.map(element, {
  center: [55.665193184436035, 13.355383872985841],
  zoom: 14,
  layers: [darkmatter, mvt],
});

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
        const gpxData = new BaseBuilder();
        gpxData.setSegmentPoints(coordinates.map(coord => new BaseBuilder.MODELS.Point(coord.lat, coord.lng)));
        //console.log(buildGPX(gpxData.toObject()));
        //L.polyline(coordinates, {color: 'green'}).addTo(map);
        return {
          name: route.name,
          summary: {totalTime: route.duration, totalDistance: route.length},
          coordinates: coordinates,
          segments: route.segments,
          inputWaypoints: waypoints,
          waypoints: [],
          instructions: route.segments.map(segment => {
            const name = segment.name || '';
            return {
              distance: segment.length,
              time: segment.duration,
              text: `${segment.ts_klass} ${name}`,
            }
          }),
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



const Veloline = L.Routing.Line.extend({
  initialize: function(route, options) {
    options.styles = [
      {
        color: 'black', opacity: 0.7, weight: 10,
      },
      {
        color: 'white', opacity: 0.5, weight: 6,
      }
    ];
    L.Routing.Line.prototype.initialize.call(this, route, options);

    for (const segment of route.segments) {
      //console.log(segment, styles[segment.ts_klass]);
      let pl = L.polyline(L.GeoJSON.coordsToLatLngs(segment.coords), tsStyles[segment.ts_klass] || {});
      this.addLayer(pl);
    }
  },

  _addSegment: function(coords, styles, mouselistener) {
    //console.log(styles);
    L.Routing.Line.prototype._addSegment.call(this, coords, styles, mouselistener);
  },
});

const Velocoder = L.Class.extend({
  options: {
    serviceUrl: 'http://localhost:8000/api/geocoder',
  },

  initialize: function(options) {
    L.Util.setOptions(this, options);
  },

  geocode: function(query, callback, context) {
    fetch(this.options.serviceUrl + `/search/${query}`)
    .then(response => response.json())
    .then(data => {
      console.log(data);
      const results = [];

      for (const item of data) {
        let loc = L.latLng(item.lat, item.lng);
        results.push({
          name: item.name,
          center: loc,
          bounds: L.latLngBounds(loc, loc),
          properties: item,
        });
      }
      console.log(results);
      callback.call(context, results);
    })
    .catch(error => {
      console.log(error);
    })
  },

  reverse: function(location, scale, callback, context) {
    fetch(this.options.serviceUrl + `/reverse/${location.lat},${location.lng}`)
    .then(response => response.json())
    .then(data => {
      console.log(data);
      const results = [];

      let loc = L.latLng(data.lat, data.lng);
      results.push({
        name: data.name,
        center: loc,
        bounds: L.latLngBounds(loc, loc),
        properties: data,
      });
      console.log(results);
      callback.call(context, results);
    })
    .catch(error => {
      console.log(error);
    })
  }
});

const routing = new L.Routing.control({
  waypoints: [
    L.latLng(55.665193184436035, 13.355383872985841),
    L.latLng(55.66727479751119, 13.340320587158205)
  ],
  router: new Velorouter({foo: 'bar'}),
  routeLine: function(route, options) {
    //console.log(options);
    //console.log(route.segments);
    return new Veloline(route, options);
  },
  geocoder: new Velocoder(), //L.Control.Geocoder.nominatim(),
}).addTo(map);

const baseMaps = {
  dark: darkmatter,
};

const overlayMaps = {
  mvt: mvt,
  ts: tsTiles,
};

L.control.layers(baseMaps, overlayMaps, {
  position: 'topleft',
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
