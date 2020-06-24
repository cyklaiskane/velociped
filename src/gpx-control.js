import L from 'leaflet';


export default L.Control.extend({
  onAdd: function (map) {
    let container = L.DomUtil.create('div', 'leaflet-bar');
    let action = L.DomUtil.create('a', 'gpx-export', container);

    action.title = 'Exportera som GPX';
    action.text = 'GPX';

    console.log(this.options);

    const routingCtl = this.options.routing;

    L.DomEvent.disableClickPropagation(container);
    L.DomEvent.on(action, 'click', function (e) {
      console.log('GPX EXPORT!');
      console.log(routingCtl._selectedRoute.coordinates);
      const gpxData = new BaseBuilder();
      gpxData.setSegmentPoints(routingCtl._selectedRoute.coordinates.map(coord => new BaseBuilder.MODELS.Point(coord.lat, coord.lng)));
      const data = buildGPX(gpxData.toObject());
      console.log(data);
      console.log(this);
      const blob = new Blob([data], {
        type: 'application/gpx+xml'
      })
      saveAs(blob, 'route.gpx');
    });

    return container;
  }
});
