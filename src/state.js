import L from 'leaflet';

class State {
  constructor() {
    this._profiles = [];
  }

  _update(waypoints, profiles) {
    let hash = waypoints.map(waypoint => `${waypoint.lat},${waypoint.lng}`);
    if (profiles) {
      this._profiles.splice(0, this._profiles.length, ...profiles);
    }
    window.location.hash = hash.join(';');
  }

  get waypoints() {
    const wptHash = window.location.hash.match(/\d+.\d+/g);
    const wps = [];
    if (wptHash && wptHash.length > 0 && wptHash.length % 2 === 0) {
      for (let i = 1; i < wptHash.length; i += 2) {
        wps.push(L.latLng(wptHash[i - 1], wptHash[i]));
      }
    }
    return wps;
  }

  set waypoints(wps) {
    this._update(wps.map(waypoint => waypoint.latLng), this._profiles);
  }

  get profile() {
    //const match = window.location.hash.match(/[a-z][a-z,]+/);
    //console.log(match)
    //return match ? match[0].split(',') : null;
    return this._profiles;
  }

  set profile(name) {
    const profiles = typeof name === 'string' ? [name] : name;
    this._update(this.waypoints, profiles);
  }
}

const state = new State();
Object.freeze(state);

export default state;
