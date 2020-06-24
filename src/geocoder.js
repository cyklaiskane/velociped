import L from 'leaflet';


export default L.Class.extend({
  options: {
    serviceUrl: 'http://localhost:8000/v1/geocoder',
  },

  initialize: function(options) {
    L.Util.setOptions(this, options);
  },

  geocode: function(query, callback, context) {
    fetch(this.options.serviceUrl + `/search/${query}`)
    .then(response => response.json())
    .then(data => {
      const results = [];

      for (const item of data) {
        let loc = L.latLng(item.lat, item.lng);
        results.push({
          name: item.name,
          center: loc,
          bounds: L.latLngBounds(loc, loc),
          properties: item,
        });
      }
      callback.call(context, results);
    })
    .catch(error => {
      console.log(error);
    })
  },

  reverse: function(location, scale, callback, context) {
    fetch(this.options.serviceUrl + `/reverse/${location.lat},${location.lng}`)
    .then(response => response.json())
    .then(data => {
      const results = [];

      let loc = L.latLng(data.lat, data.lng);
      results.push({
        name: data.name,
        center: loc,
        bounds: L.latLngBounds(loc, loc),
        properties: data,
      });
      callback.call(context, results);
    })
    .catch(error => {
      console.log(error);
    })
  }
});
