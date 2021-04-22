import _ from 'lodash';
import L from 'leaflet';
import 'leaflet.vectorgrid'
import 'leaflet-routing-machine';
import 'leaflet-control-geocoder';
import 'leaflet.icon.glyph';

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
import ProfileControl from './profile-control.js';
import InfoControl from './info-control.js';

import tsStyles from './ts-styles.js';
import state from './state.js';


const apiBaseUrl = process.env.API_BASE_URL;
const element = document.createElement('div');
element.id = 'map';
document.body.appendChild(element);

const vtStyles = {
  roads: function(properties, zoom, geometryDimension) {
    const style = tsStyles[properties.ts_klass] || {color: 'grey', opacity: 1, weight: 3};
    return {
      color: style.color,
      opacity: 0.7,
      weight: 0.4 * style.weight * (Math.tanh(zoom / 3 - 5) + 1),
    };
  }
};

const backgroundTiles = L.tileLayer(typeof backgroundTilesUrl !== 'undefined' ? backgroundTilesUrl : 'http://localhost:3000/styles/bg/{z}/{x}/{y}.png', {});

const tsMvt = L.vectorGrid.protobuf(apiBaseUrl + '/v1/tiles/ts/{z}/{x}/{y}.pbf', {
  renderFactory: L.canvas.tile,
  vectorTileLayerStyles: vtStyles,
});

const bgMvt = L.vectorGrid.protobuf(apiBaseUrl + '/v1/tiles/bg/{z}/{x}/{y}.pbf', {
  renderFactory: L.canvas.tile,
  //vectorTileLayerStyles: vtStyles,
});

const tsTiles = L.tileLayer(typeof tsTilesUrl !== 'undefined' ? tsTilesUrl : 'http://localhost:3000/styles/velo/{z}/{x}/{y}.png', {});

const bounds = L.latLngBounds(
  L.latLng(55.1232, 12.4374),
  L.latLng(56.5354, 14.5959)
);

var map = L.map(element, {
  //center: [55.665193184436035, 13.355383872985841],
  //zoom: 14,
  layers: [backgroundTiles],
})
.setMaxBounds(bounds)
.fitBounds(bounds);


const routing = new L.Routing.control({
  lineOptions: {
    styles: [
      { color: 'black', opacity: 0.7, weight: 10, },
      { color: 'white', opacity: 0.5, weight: 6, },
    ],
  },
  altLineOptions: {
    styles: [
      { color: 'black', opacity: 0.4, weight: 10 },
      { color: 'white', opacity: 0.4, weight: 6 },
    ]
  },
  waypoints: state.waypoints,
  router: new Router({serviceUrl: apiBaseUrl}),
  routeLine: function(route, options) {
    return new Line(route, options, tsStyles);
  },
  geocoder: new Geocoder({ 'serviceUrl': apiBaseUrl }), //L.Control.Geocoder.latLng(), //null //new Velocoder(), //L.Control.Geocoder.nominatim(),
  createMarker: function (i, wp) {
    return L.marker(wp.latLng, {
      icon: L.icon.glyph({
        prefix: '',
        glyph: (i + 1).toString(),
      }),
      draggable: true
    });
  },
}).addTo(map);

const baseMaps = {
  'Bakgrund': backgroundTiles,
  //'MVT bg': bgMvt,
};

const overlayMaps = {
  //'TS MVT': tsMvt,
  'Trafiksäkerhetsklassning': tsTiles,
};

L.control.layers(baseMaps, overlayMaps, {
  position: 'bottomright',
  hideSingleBase: true,
}).addTo(map);

function createButton(label, container) {
    var btn = L.DomUtil.create('button', '', container);
    btn.setAttribute('type', 'button');
    btn.innerHTML = label;
    return btn;
}

map.on('contextmenu', function(e) {
    const container = L.DomUtil.create('div'),
        startBtn = createButton('Start', container),
        destBtn = createButton('Mål', container);

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

new InfoControl({position: 'topleft'}).addTo(map);
new ProfileControl({position: 'topright', baseUrl: apiBaseUrl, routing: routing}).addTo(map);
new GpxControl({position: 'bottomleft', routing: routing}).addTo(map);
