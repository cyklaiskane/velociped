import L from 'leaflet';


export default L.Routing.Line.extend({
  initialize: function (route, options, tsStyles) {
    L.Routing.Line.prototype.initialize.call(this, route, options);

    // Skip segment TS-klass colors for alt routes
    if (options.isAlternative) {
      return;
    }
    for (const segment of route.segments) {
      let pl = L.polyline(L.GeoJSON.coordsToLatLngs(segment.coords), tsStyles[segment.ts_klass] || {});
      this.addLayer(pl);
    }
    for (const danger of route.dangerCoordinates) {
      this.addLayer(L.circleMarker(danger, {
        color: 'red',
        opacity: 0.2,
      }));
    }
  },

  _addSegment: function (coords, styles, mouselistener) {
    L.Routing.Line.prototype._addSegment.call(this, coords, styles, mouselistener);
  },
});
