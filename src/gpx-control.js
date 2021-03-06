import L from 'leaflet';

import { saveAs } from 'file-saver';
import { buildGPX, BaseBuilder } from 'gpx-builder';


export default L.Control.extend({
  onAdd: function (map) {
    const container = L.DomUtil.create('div', 'leaflet-bar');
    const action = L.DomUtil.create('a', 'gpx-export', container);

    action.title = 'Exportera som GPX';
    action.text = 'GPX';

    const routingCtl = this.options.routing;

    L.DomEvent.disableClickPropagation(container);
    L.DomEvent.on(action, 'click', function (e) {
      const gpxData = new BaseBuilder();
      gpxData.setSegmentPoints(routingCtl._selectedRoute.coordinates.map(coord => new BaseBuilder.MODELS.Point(coord.lat, coord.lng)));
      const data = buildGPX(gpxData.toObject());
      const blob = new Blob([data], {
        type: 'application/gpx+xml'
      })
      saveAs(blob, 'route.gpx');
    });

    return container;
  }
});
