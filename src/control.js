import L from 'leaflet';

import 'leaflet-routing-machine';

import { saveAs } from 'file-saver';
import { buildGPX, BaseBuilder } from 'gpx-builder';

import state from './state.js';

export default L.Routing.Control.extend({
  options: {
    collapseBtn: function (itinerary) {
      let collapseBtn = L.DomUtil.create('span', itinerary.options.collapseBtnClass);
      collapseBtn.innerHTML = '<span class="fa fa-route"></span>';
      L.DomEvent.on(collapseBtn, 'click', itinerary._toggle, itinerary);
      itinerary._container.insertBefore(collapseBtn, itinerary._container.firstChild);
    }
  },

  initialize: function (options) {
    L.setOptions(this, options);

    fetch(this.options.serviceUrl + '/v1/route/profiles')
      .then(response => response.json())
      .then(data => {
        console.log('profiles.json:', data);
        state.profile = data.map(profile => profile.name);
      });

    L.Routing.Control.prototype.initialize.call(this, options);
  },

  _createAlternative: function (alt, i) {
    const altDiv = L.Routing.Control.prototype._createAlternative.call(this, alt, i);
    const exportBtn = L.DomUtil.create('button', 'leaflet-routing-alt-gpx-export');
    exportBtn.innerHTML = '<span class="fas fa-file-download"></span>'; //'📥';
    exportBtn.setAttribute('type', 'button');
    L.DomEvent.disableClickPropagation(exportBtn);
    L.DomEvent.on(exportBtn, 'click', function (e) {
      const gpxData = new BaseBuilder();
      gpxData.setSegmentPoints(this.coordinates.map(coord => new BaseBuilder.MODELS.Point(coord.lat, coord.lng)));
      const data = buildGPX(gpxData.toObject());
      const blob = new Blob([data], {
        type: 'application/gpx+xml'
      })
      saveAs(blob, 'route.gpx');
    }, alt);
    altDiv.firstChild.appendChild(exportBtn);
    return altDiv;
  },
});
