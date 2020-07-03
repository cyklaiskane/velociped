import L from 'leaflet';

import infoText from './info.html';
import tsStyles from './ts-styles.js';


export default L.Control.extend({
  initialize: function (options) {
    L.Control.prototype.initialize.call(this, options);

    const text = L.DomUtil.create('div', 'info-text-container');
    if (document.cookie.match(/infoTextClosed=true/)) {
      text.classList.add('info-text-hide');
    }
    text.innerHTML = infoText;

    const classList = text.querySelector('.ts-classes');
    for (const [name, style] of Object.entries(tsStyles)) {
      console.log(style);
      const item = L.DomUtil.create('li', 'ts-class', classList);
      item.innerText = name + ' ' + style.description;
      item.style.color = style.color;
    }

    const button = text.querySelector('button');
    L.DomEvent.on(button, 'click', function (e) {
      document.cookie = 'infoTextClosed=true; Expires=' + (new Date(2037,1,1).toGMTString()) + '; SameSite=Strict';
      text.classList.add('info-text-hide');
    });
    this.infoText = text;
    document.body.appendChild(text);
  },

  onAdd: function (map) {
    const container = L.DomUtil.create('div', 'info-text-control leaflet-bar');
    const button = L.DomUtil.create('a', 'info-button', container);
    const text = this.infoText;

    button.innerHTML = '&#8505;';

    L.DomEvent.disableClickPropagation(container);
    L.DomEvent.on(button, 'click', function (e) {
      text.classList.toggle('info-text-hide');
    });

    return container;
  }
});
