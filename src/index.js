import _ from 'lodash';
import L from 'leaflet';
import 'leaflet.vectorgrid'
import 'leaflet-routing-machine';
import 'leaflet.icon.glyph';
import 'leaflet.locatecontrol';

import '@fortawesome/fontawesome-free/css/all.css'

import 'leaflet/dist/leaflet.css';
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css';
import 'leaflet.locatecontrol/dist/L.Control.Locate.css';

import './style.css';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconRetina from 'leaflet/dist/images/marker-icon-2x.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
  iconRetinaUrl: iconRetina,
  iconUrl: icon,
  shadowUrl: iconShadow,
});

import Control from './control.js';
import Router from './router.js';
import Line from './line.js';
import Geocoder from './geocoder.js';

import tsStyles from './ts-styles.js';
import state from './state.js';


const apiBaseUrl = process.env.API_BASE_URL;
const element = document.createElement('div');
element.id = 'map';
document.body.appendChild(element);

const vtStyles = {
  roads: function (properties, zoom, geometryDimension) {
    const style = tsStyles[properties.ts_klass] || { color: 'grey', opacity: 1, weight: 3 };
    return {
      color: style.color,
      opacity: 0.7,
      weight: 0.4 * style.weight * (Math.tanh(zoom / 3 - 5) + 1),
    };
  }
};

const bounds = L.latLngBounds(
  L.latLng(55.1232, 12.4374),
  L.latLng(56.5354, 14.5959)
);

var map = L.map(element, {
  zoomControl: false,
})
  .setMaxBounds(bounds)
  .fitBounds(bounds);

L.control.zoom({
  position: 'topright'
}).addTo(map);

L.control.locate({
  position: 'topright'
}).addTo(map);

const routing = new Control({
  serviceUrl: apiBaseUrl,
  collapsible: true,
  language: 'sv',
  showAlternatives: true,
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
  position: 'topleft',
  waypoints: state.waypoints,
  router: new Router({ serviceUrl: apiBaseUrl, showInstructions: false }),
  summaryTemplate: function (data) {
    if (data.danger) {
      data.name += '  ⚠️';
    }
    const html = L.Util.template('<h2>{name}</h2><h3>{distance}, {time}</h3>', data);
    return html;
  },
  createGeocoderElement: function (wp, i, nWps, plan) {
    const ge = new L.Routing.GeocoderElement(wp, i, nWps, plan);
    if (plan.addWaypoints && i < nWps - 1) {
      const btnContainer = L.DomUtil.create('div', '', ge.getContainer());
      const addWpBtn = L.DomUtil.create('button', 'leaflet-routing-add-waypoint ' + plan.addButtonClassName, btnContainer);
      L.DomUtil.create('span', 'clear', btnContainer);
      addWpBtn.setAttribute('type', 'button');
      L.DomEvent.addListener(addWpBtn, 'click', function () {
        routing.spliceWaypoints(i + 1, 0, null);
      });
    }
    return ge;
  },
  routeLine: function (route, options) {
    return new Line(route, options, tsStyles);
  },
  geocoder: new Geocoder({ 'serviceUrl': apiBaseUrl }),
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

function initLayers(lyrs, map) {
  const createLayer = layer => {
    const options = layer.options ?? {};
    options.tms = layer.type == 'tms';

    const l = L.tileLayer(layer.url, options);
    const title = L.Util.template(
      '{name} <p>{description}</p>',
      {
        name: layer.name,
        description: layer.description ?? ''
      }
    );

    return [title, l];
  }
  const layers = L.extend({ backgrounds: [], overlays: [] }, lyrs);
  const baseMaps = Object.fromEntries(layers.backgrounds.map(layer => createLayer(layer)));
  const overlayMaps = Object.fromEntries(layers.overlays.map(layer => createLayer(layer)));;
  if (process.env.NODE_ENV === 'development') {
    overlayMaps['Trafiksäkerhetsklassning (vektor)'] = L.vectorGrid.protobuf(apiBaseUrl + '/v1/tiles/ts/{z}/{x}/{y}.pbf', {
      renderFactory: L.canvas.tile,
      vectorTileLayerStyles: vtStyles,
      minZoom: 13,
    });
  }

  baseMaps[Object.keys(baseMaps)[0]].addTo(map);
  return L.control.layers(baseMaps, overlayMaps, {
    position: 'topleft',
    hideSingleBase: false,
    collapsed: true,
  }).addTo(map);
}

fetch('layers.json')
  .then(response => response.json())
  .then(data => {
    console.log('layers.json:', data);
    initLayers(data, map);
  })
  .catch(err => console.log(err));

function createButton(label, container) {
  var btn = L.DomUtil.create('button', '', container);
  btn.setAttribute('type', 'button');
  btn.innerHTML = label;
  return btn;
}

map.on('click', function (e) {
  const container = L.DomUtil.create('div'),
    startBtn = createButton('Start', container),
    destBtn = createButton('Mål', container);

  L.popup()
    .setContent(container)
    .setLatLng(e.latlng)
    .openOn(map);

  L.DomEvent.on(startBtn, 'click', function () {
    routing.spliceWaypoints(0, 1, e.latlng);
    map.closePopup();
  });

  L.DomEvent.on(destBtn, 'click', function () {
    routing.spliceWaypoints(routing.getWaypoints().length - 1, 1, e.latlng);
    map.closePopup();
  });
});

