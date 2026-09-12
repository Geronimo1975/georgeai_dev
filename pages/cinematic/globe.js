/* Wireframe globe on a canvas: fibonacci point sphere, lat/long rings, orange nodes with arcs.
   Shared by the home hero and the assistant page. Rests off-screen, on hidden tabs, and under reduced motion. */
window.mountGlobe = function (canvas, opts = {}) {
  const rmq = matchMedia('(prefers-reduced-motion: reduce)');
  if (!canvas || rmq.matches) return;
  const speed = opts.speed || .00012;

    const ctx = canvas.getContext('2d');
    const DPR = Math.min(2, devicePixelRatio || 1);
    let W = 0, H = 0, R = 0, cx = 0, cy = 0;
    function size() { const r = canvas.getBoundingClientRect(); W = r.width; H = r.height; canvas.width = W * DPR; canvas.height = H * DPR; ctx.setTransform(DPR, 0, 0, DPR, 0, 0); R = W * .36; cx = W / 2; cy = H / 2; }
    size(); addEventListener('resize', size, { passive: true });
    // points on a sphere (fibonacci), plus lat/long rings
    const PTS = []; const N = 900; for (let i = 0; i < N; i++) { const y = 1 - (i / (N - 1)) * 2, r = Math.sqrt(1 - y * y), th = i * 2.39996; PTS.push([r * Math.cos(th), y, r * Math.sin(th)]); }
    // "land" mask: a few soft blobs so the sphere reads as a planet, not a ball of dots
    const LAND = [[.3, .6, .7, .35], [-.5, .5, .4, .4], [.1, -.4, .8, .3], [-.7, -.2, -.5, .35], [.6, .1, -.6, .3], [-.2, .2, -.9, .25]];
    const isLand = p => LAND.some(([x, y, z, r]) => (p[0] - x) ** 2 + (p[1] - y) ** 2 + (p[2] - z) ** 2 < r * r);
    const NODES = [[.4, .5, .77], [-.6, .3, .74], [.2, -.5, .84], [-.3, -.6, .74], [.8, .1, .59]];
    const tilt = .38; let rot = 0, last = 0, gRaf = null, visible = true;
    function proj(p, a) {
      const x = p[0] * Math.cos(a) - p[2] * Math.sin(a), z = p[0] * Math.sin(a) + p[2] * Math.cos(a), y = p[1];
      const y2 = y * Math.cos(tilt) - z * Math.sin(tilt), z2 = y * Math.sin(tilt) + z * Math.cos(tilt);
      return [cx + x * R, cy - y2 * R, z2];
    }
    function draw(now) {
      const dt = Math.min(64, now - (last || now)); last = now; rot += dt * speed;
      ctx.clearRect(0, 0, W, H);
      // atmosphere
      const g = ctx.createRadialGradient(cx, cy, R * .8, cx, cy, R * 1.25); g.addColorStop(0, 'rgba(25,195,154,0)'); g.addColorStop(.6, 'rgba(25,195,154,.12)'); g.addColorStop(1, 'rgba(25,195,154,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx, cy, R * 1.25, 0, 7); ctx.fill();
      // rings
      ctx.lineWidth = 1;
      for (let k = -2; k <= 2; k++) { const y = k * .33, r = Math.sqrt(1 - y * y); ctx.beginPath(); for (let i = 0; i <= 90; i++) { const a = i / 90 * Math.PI * 2; const q = proj([r * Math.cos(a), y, r * Math.sin(a)], rot); if (q[2] < -.05) { ctx.moveTo(q[0], q[1]); continue; } i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); } ctx.strokeStyle = 'rgba(25,195,154,.38)'; ctx.stroke(); }
      for (let k = 0; k < 6; k++) { const a0 = k / 6 * Math.PI; ctx.beginPath(); for (let i = 0; i <= 90; i++) { const t = i / 90 * Math.PI * 2; const q = proj([Math.cos(a0) * Math.sin(t), Math.cos(t), Math.sin(a0) * Math.sin(t)], rot); if (q[2] < -.05) { ctx.moveTo(q[0], q[1]); continue; } i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]); } ctx.strokeStyle = 'rgba(25,195,154,.3)'; ctx.stroke(); }
      // points
      for (const p of PTS) { const q = proj(p, rot); if (q[2] < 0) continue; const land = isLand(p); const a = (.35 + q[2] * .65) * (land ? 1 : .5); ctx.fillStyle = land ? `rgba(180,255,235,${a})` : `rgba(25,195,154,${a})`; ctx.fillRect(q[0], q[1], land ? 1.8 : 1.2, land ? 1.8 : 1.2); }
      // nodes + arcs to the first node
      const front = NODES.map(n => proj(n, rot)).filter(q => q[2] > .1);
      ctx.lineWidth = 1;
      for (let i = 1; i < front.length; i++) { const a = front[0], b = front[i]; const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2 - 40; ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.quadraticCurveTo(mx, my, b[0], b[1]); ctx.strokeStyle = 'rgba(251,94,49,.45)'; ctx.stroke(); }
      const pulse = (Math.sin(now / 500) + 1) / 2;
      for (const q of front) { ctx.beginPath(); ctx.arc(q[0], q[1], 3 + pulse * 2, 0, 7); ctx.fillStyle = '#fb5e31'; ctx.fill(); ctx.beginPath(); ctx.arc(q[0], q[1], 8 + pulse * 6, 0, 7); ctx.strokeStyle = `rgba(251,94,49,${.5 - pulse * .4})`; ctx.stroke(); }
      gRaf = visible && !document.hidden ? requestAnimationFrame(draw) : null;
    }
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; if (visible && gRaf === null) { last = 0; gRaf = requestAnimationFrame(draw); } }).observe(canvas);
    document.addEventListener('visibilitychange', () => { if (!document.hidden && visible && gRaf === null) { last = 0; gRaf = requestAnimationFrame(draw); } });
    gRaf = requestAnimationFrame(draw);
};
