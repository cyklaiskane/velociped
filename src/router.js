import L from 'leaflet';


export default L.Class.extend({
  options: {
      serviceUrl: '',
  },

  initialize: function(options) {
      L.setOptions(this, options);
  },

  route: function(waypoints, callback, context, options) {
    let query = {
      waypoints: waypoints.map(waypoint => waypoint.latLng),
    }
    const hash = waypoints.map(waypoint => `${waypoint.latLng.lat},${waypoint.latLng.lng}`).join(';');
    window.location.hash = hash;

    fetch(this.options.serviceUrl + '/v1/route', {
      method: 'POST',
      body: JSON.stringify(query),
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        throw data.error;
      }
      const result = data.map(route => {
        const coordinates = route.segments.map(segment => L.GeoJSON.coordsToLatLngs(segment.coords)).flat();
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

      callback.call(context, null, result);
    })
    .catch(error => {
      console.log(error);
      callback.call(context, error, null);
    });
  },
});
