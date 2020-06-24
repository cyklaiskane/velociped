import _ from 'lodash';
import L from 'leaflet';
import 'leaflet.vectorgrid'
import 'leaflet-routing-machine';
import 'leaflet-control-geocoder';

import { saveAs } from 'file-saver';
import { buildGPX, BaseBuilder } from 'gpx-builder';

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

import Router from './router.js';
import Line from './line.js';
import Geocoder from './geocoder.js';
import GpxControl from './gpx-control.js';


const apiBaseUrl = process.env.API_BASE_URL;
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

const bg = L.tileLayer('http://localhost:3000/styles/bg/{z}/{x}/{y}.png', {

});

const mvt = L.vectorGrid.protobuf(apiBaseUrl + '/tiles/{z}/{x}/{y}.pbf', {
  renderFactory: L.canvas.tile,
  vectorTileLayerStyles: vtStyles,
});

const tsTiles = L.tileLayer('http://localhost:3000/styles/velo/{z}/{x}/{y}.png', {

});

const wptHash = window.location.hash.match(/\d+.\d+/g);
console.log(wptHash);
let initWaypoints = [];
if (wptHash && wptHash.length > 0 && wptHash.length % 2 === 0) {
  console.log('Fooo!');
  for (let i = 1; i < wptHash.length; i += 2) {
    initWaypoints.push(L.latLng(wptHash[i-1], wptHash[i]));
    console.log(initWaypoints);
  }
} else {
  initWaypoints = [
    L.latLng(55.665193184436035, 13.355383872985841),
    L.latLng(55.66727479751119, 13.340320587158205)
  ];
}

//element.innerHTML = _.join(['Hello', 'webpack'], ' ');
var map = L.map(element, {
  center: [55.665193184436035, 13.355383872985841],
  zoom: 14,
  layers: [bg, mvt],
});


const routing = new L.Routing.control({
  waypoints: initWaypoints,
  router: new Router({serviceUrl: apiBaseUrl}),
  routeLine: function(route, options) {
    return new Line(route, options, tsStyles);
  },
  geocoder: L.Control.Geocoder.latLng(), //null //new Velocoder(), //L.Control.Geocoder.nominatim(),
}).addTo(map);

const baseMaps = {
  bg: bg,
};

const overlayMaps = {
  mvt: mvt,
  ts: tsTiles,
};

L.control.layers(baseMaps, overlayMaps, {
  position: 'bottomleft',
  hideSingleBase: true,
}).addTo(map);

function createButton(label, container) {
    var btn = L.DomUtil.create('button', '', container);
    btn.setAttribute('type', 'button');
    btn.innerHTML = label;
    return btn;
}

map.on('click', function(e) {
    const container = L.DomUtil.create('div'),
        startBtn = createButton('Start from this location', container),
        destBtn = createButton('Go to this location', container);

    L.popup()
      .setContent(container)
      .setLatLng(e.latlng)
      .openOn(map);

    L.DomEvent.on(startBtn, 'click', function() {
      routing.spliceWaypoints(0, 1, e.latlng);
      map.closePopup();
    });

    L.DomEvent.on(destBtn, 'click', function() {
      routing.spliceWaypoints(routing.getWaypoints().length - 1, 1, e.latlng);
      map.closePopup();
    });
});


new GpxControl({position: 'bottomright', routing: routing}).addTo(map);
