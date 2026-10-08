import assert from 'node:assert/strict';
import { makeProjection, facadesOf, visibleFacades, rectFromSide, polylineLength, snapToFacades, ringAreaM2, bearingDeg } from '../prototype/js/geo.js';

// Maison test à Eaubonne : 10 m est-ouest x 6 m nord-sud
const lat0 = 48.99, lon0 = 2.28;
const P = makeProjection(lat0, lon0);
const ring = [[0,0],[10,0],[10,6],[0,6],[0,0]].map(P.toLonLat); // sens trigonométrique
const f = facadesOf(ring);
assert.equal(f.length, 4);
const byFacing = Object.fromEntries(f.map(x => [x.facing, x.length]));
assert.ok(Math.abs(byFacing.sud - 10) < 0.05, 'façade sud 10 m');
assert.ok(Math.abs(byFacing.est - 6) < 0.05, 'façade est 6 m');
assert.ok(Math.abs(byFacing.nord - 10) < 0.05);
assert.ok(Math.abs(byFacing.ouest - 6) < 0.05);
// Même résultat avec l'anneau dans l'autre sens
const f2 = facadesOf([...ring].reverse());
assert.deepEqual(f2.map(x=>x.facing).sort(), ['est','nord','ouest','sud']);
// Points intermédiaires colinéaires fusionnés
const ring3 = [[0,0],[5,0],[10,0],[10,6],[0,6],[0,0]].map(P.toLonLat);
assert.equal(facadesOf(ring3).length, 4);
// Surface
assert.ok(Math.abs(ringAreaM2(ring) - 60) < 0.5);
// Photo prise à 15 m au sud, regard vers le nord : la façade sud est visible
const cam = P.toLonLat([5,-15]);
const vis = visibleFacades(f, cam, bearingDeg(cam, P.toLonLat([5,3])));
assert.equal(vis[0].facing, 'sud');
assert.ok(!vis.some(v => v.facing === 'nord'), 'façade nord cachée');
// Rectangle 4 m contre la façade sud, profondeur 3 m
const r = rectFromSide(P.toLonLat([2,0]), P.toLonLat([6,0]), 3, -1);
assert.ok(Math.abs(r.width - 4) < 0.01);
const c = r.ring.map(P.toXY);
assert.ok(c[2][1] < -2.9, 'posé côté sud (hors maison)');
assert.ok(Math.abs(polylineLength([P.toLonLat([0,0]), P.toLonLat([3,4])]) - 5) < 0.01);
// Aimantation
const s = snapToFacades(P.toLonLat([4,-1]), f, 2);
assert.equal(s.facade.facing, 'sud');
console.log('geo : tous les tests passent');
