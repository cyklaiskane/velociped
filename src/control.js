import L from 'leaflet';

import 'leaflet-routing-machine';

import { saveAs } from 'file-saver';
import { buildGPX, BaseBuilder } from 'gpx-builder';

export default L.Routing.Control.extend({
  initialize: function (options) {
    console.log(options);
    L.Routing.Control.prototype.initialize.call(this, options);
  },

  _createAlternative: function (alt, i) {
    console.log(i, alt);
    const altDiv = L.Routing.Control.prototype._createAlternative.call(this, alt, i);
    const exportBtn = L.DomUtil.create('button', 'leaflet-routing-alt-gpx-export');
    exportBtn.innerText = '📥';
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
