// Position et direction de prise de vue : capteurs du téléphone (photo prise dans l'outil)
// ou métadonnées EXIF (photo choisie dans la galerie).
/* global exifr */

// ---------- Capteurs, pour une photo prise depuis la page ----------

let lastFix = null;      // { lat, lon, accuracy }
let lastHeading = null;  // degrés depuis le nord, sens horaire
let watching = false;

function onOrientation(e) {
  if (typeof e.webkitCompassHeading === 'number') lastHeading = e.webkitCompassHeading; // iOS
  else if (e.absolute && typeof e.alpha === 'number') lastHeading = (360 - e.alpha) % 360; // Android
}

// À appeler dans le geste de l'utilisateur (clic) : iOS refuse sinon la demande d'autorisation.
export async function startSensors() {
  if (watching) return;
  watching = true;
  try {
    if (typeof DeviceOrientationEvent !== 'undefined' && typeof DeviceOrientationEvent.requestPermission === 'function') {
      const r = await DeviceOrientationEvent.requestPermission();
      if (r === 'granted') window.addEventListener('deviceorientation', onOrientation, true);
    } else {
      window.addEventListener('deviceorientationabsolute', onOrientation, true);
      window.addEventListener('deviceorientation', onOrientation, true);
    }
  } catch (e) { /* refus : on se passera de la boussole */ }
  if ('geolocation' in navigator) {
    navigator.geolocation.watchPosition(
      (p) => { lastFix = { lat: p.coords.latitude, lon: p.coords.longitude, accuracy: p.coords.accuracy }; },
      () => {},
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 },
    );
  }
}

export function sensorSnapshot() {
  return { fix: lastFix, heading: lastHeading };
}

// ---------- EXIF, pour une photo de la galerie ----------

export async function readExifView(file) {
  if (typeof exifr === 'undefined') return null;
  try {
    const data = await exifr.parse(file, { tiff: true, gps: true });
    if (!data || typeof data.latitude !== 'number') return null;
    return {
      lat: data.latitude,
      lon: data.longitude,
      heading: typeof data.GPSImgDirection === 'number' ? data.GPSImgDirection : null,
      accuracy: data.GPSHPositioningError || null,
    };
  } catch (e) {
    return null;
  }
}
