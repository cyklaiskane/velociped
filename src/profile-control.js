import L from 'leaflet';

import state from './state.js';

export default L.Control.extend({
  options: {
    baseUrl: '',
  },

  onAdd: function (map) {
    const container = L.DomUtil.create('div', 'leaflet-routing-container leaflet-bar');
    const wrapper = L.DomUtil.create('div', 'profile-selector-container', container);
    const selector = L.DomUtil.create('select', 'profile-selector', wrapper);
    const routingCtl = this.options.routing;

    fetch(this.options.baseUrl + '/v1/route/profiles')
    .then(response => response.json())
    .then(data => {
      for (let profile of data) {
        let opt = L.DomUtil.create('option');
        opt.text = profile.label;
        opt.value = profile.name;
        opt.selected = state.profile === profile.name;
        selector.add(opt);
      }
    });

    L.DomEvent.disableClickPropagation(container);
    L.DomEvent.on(selector, 'input', function (e) {
      state.profile = e.target.value;
      routingCtl.route();
    });

    return container;
  }
});
