import L from 'leaflet';

import state from './state.js';

export default L.Class.extend({
  options: {
    serviceUrl: '',
    showInstructions: true,
    dangerClasses: ['B3', 'B4', 'B5'],
  },

  initialize: function (options) {
    L.Util.setOptions(this, options);

    const spinner = L.DomUtil.create('div', 'spinner');
    this.spinner = spinner;
    document.body.appendChild(spinner);
  },

  route: function (waypoints, callback, context, options) {
    const query = {
      waypoints: waypoints.map(waypoint => waypoint.latLng),
      profile_name: null, //state.profile,
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
          const dangerCoordinates = route.segments.reduce((coords, segment) => {
            if (segment.danger_coords) {
              coords.push(...L.GeoJSON.coordsToLatLngs(segment.danger_coords));
            }
            return coords;
          },
            []
          );
          let index = 0;
          return {
            name: route.name,
            summary: { totalTime: route.duration, totalDistance: route.length },
            danger: route.segments.some(segment => this.options.dangerClasses.includes(segment.ts_klass)),
            coordinates: coordinates,
            dangerCoordinates: dangerCoordinates,
            segments: route.segments,
            inputWaypoints: waypoints,
            waypoints: [],
            instructions: this.options.showInstructions ? route.segments.map(segment => {
              const name = segment.name || '';
              const instruction = {
                distance: segment.length,
                time: segment.duration,
                text: `${segment.ts_klass} ${name}`,
                index: index,
              }
              index += segment.coords.length;
              return instruction;
            }) : [],
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
