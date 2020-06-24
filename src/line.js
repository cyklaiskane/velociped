export default L.Routing.Line.extend({
  initialize: function(route, options, tsStyles) {
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
      let pl = L.polyline(L.GeoJSON.coordsToLatLngs(segment.coords), tsStyles[segment.ts_klass] || {});
      this.addLayer(pl);
    }
  },

  _addSegment: function(coords, styles, mouselistener) {
    L.Routing.Line.prototype._addSegment.call(this, coords, styles, mouselistener);
  },
});
