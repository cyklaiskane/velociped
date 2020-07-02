import L from 'leaflet';

class State {
  constructor() {}

  _update(waypoints, profile) {
    let hash = waypoints.map(waypoint => `${waypoint.lat},${waypoint.lng}`);
    if (profile) {
      hash.push(profile);
    }
    window.location.hash = hash.join(';');
  }

  get waypoints() {
    const wptHash = window.location.hash.match(/\d+.\d+/g);
    const wps = [];
    if (wptHash && wptHash.length > 0 && wptHash.length % 2 === 0) {
      for (let i = 1; i < wptHash.length; i += 2) {
        wps.push(L.latLng(wptHash[i-1], wptHash[i]));
      }
    }
    return wps;
  }

  set waypoints(wps) {
    this._update(wps.map(waypoint => waypoint.latLng), this.profile);
  }

  get profile() {
    const match = window.location.hash.match(/[a-z]+/);
    return match ? match[0] : null;
  }

  set profile(name) {
    this._update(this.waypoints, name);
  }
}

const state = new State();
Object.freeze(state);

export default state;
