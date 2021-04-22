import L from 'leaflet';

import state from './state.js';

export default L.Class.extend({
  options: {
    serviceUrl: '',
    showInstructions: true,
  },

  initialize: function(options) {
      L.Util.setOptions(this, options);

      const spinner = L.DomUtil.create('div', 'spinner');
      this.spinner = spinner;
      document.body.appendChild(spinner);
  },

  route: function(waypoints, callback, context, options) {
    const query = {
      waypoints: waypoints.map(waypoint => waypoint.latLng),
      profile_name: state.profile,
    }
    const spinner = this.spinner;

    state.waypoints = waypoints;
    spinner.style.visibility = 'visible';
    spinner.style.opacity = 1;

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
    })
    .finally(() => {
      spinner.style.visibility = 'hidden';
      spinner.style.opacity = 0;
    });
  },
});
