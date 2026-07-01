/* === DEBETIES V2 - MAIN JS === */

// ===== PARTICLE CANVAS =====
const canvas = document.getElementById('particle-canvas');
const ctx = canvas.getContext('2d');
let particles = [];
let mouseX = 0, mouseY = 0;

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

class Particle {
  constructor() {
    this.x = Math.random() * canvas.width;
    this.y = Math.random() * canvas.height;
    this.size = Math.random() * 2 + 0.5;
    this.speedX = (Math.random() - 0.5) * 0.5;
    this.speedY = (Math.random() - 0.5) * 0.5;
    this.opacity = Math.random() * 0.5 + 0.1;
  }
  update() {
    this.x += this.speedX;
    this.y += this.speedY;
    if (this.x < 0 || this.x > canvas.width) this.speedX *= -1;
    if (this.y < 0 || this.y > canvas.height) this.speedY *= -1;
    // Mouse interaction
    const dx = mouseX - this.x;
    const dy = mouseY - this.y;
    const dist = Math.sqrt(dx*dx + dy*dy);
    if (dist < 150) {
      this.x -= dx * 0.01;
      this.y -= dy * 0.01;
    }
  }
  draw() {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(99, 102, 241, ${this.opacity})`;
    ctx.fill();
  }
}

function initParticles() {
  particles = [];
  const count = Math.min(80, Math.floor((canvas.width * canvas.height) / 15000));
  for (let i = 0; i < count; i++) particles.push(new Particle());
}
initParticles();

function connectParticles() {
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const dist = Math.sqrt(dx*dx + dy*dy);
      if (dist < 120) {
        ctx.beginPath();
        ctx.strokeStyle = `rgba(99, 102, 241, ${0.1 * (1 - dist/120)})`;
        ctx.lineWidth = 0.5;
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.stroke();
      }
    }
  }
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  particles.forEach(p => { p.update(); p.draw(); });
  connectParticles();
  requestAnimationFrame(animateParticles);
}
animateParticles();

document.addEventListener('mousemove', e => { mouseX = e.clientX; mouseY = e.clientY; });

// ===== NAVBAR SCROLL =====
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  if (window.scrollY > 50) navbar.classList.add('scrolled');
  else navbar.classList.remove('scrolled');
});

// ===== MOBILE MENU =====
const navToggle = document.getElementById('nav-toggle');
const navMenu = document.getElementById('nav-menu');
if (navToggle) {
  navToggle.addEventListener('click', () => {
    navMenu.classList.toggle('active');
    navToggle.classList.toggle('active');
  });
}

// ===== GSAP ANIMATIONS =====
if (typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined') {
  gsap.registerPlugin(ScrollTrigger);

  // Fade up
  document.querySelectorAll('[data-gsap="fade-up"]').forEach(el => {
    const delay = parseFloat(el.dataset.delay) || 0;
    gsap.from(el, {
      y: 40, opacity: 0, duration: 0.8, delay: delay,
      ease: 'power2.out',
      scrollTrigger: { trigger: el, start: 'top 85%', toggleActions: 'play none none none' }
    });
  });

  // Fade right
  document.querySelectorAll('[data-gsap="fade-right"]').forEach(el => {
    const delay = parseFloat(el.dataset.delay) || 0;
    gsap.from(el, {
      x: -40, opacity: 0, duration: 0.8, delay: delay,
      ease: 'power2.out',
      scrollTrigger: { trigger: el, start: 'top 85%' }
    });
  });

  // Fade left
  document.querySelectorAll('[data-gsap="fade-left"]').forEach(el => {
    const delay = parseFloat(el.dataset.delay) || 0;
    gsap.from(el, {
      x: 40, opacity: 0, duration: 0.8, delay: delay,
      ease: 'power2.out',
      scrollTrigger: { trigger: el, start: 'top 85%' }
    });
  });

  // Scale in
  document.querySelectorAll('[data-gsap="scale-in"]').forEach(el => {
    const delay = parseFloat(el.dataset.delay) || 0;
    gsap.from(el, {
      scale: 0.8, opacity: 0, duration: 0.8, delay: delay,
      ease: 'back.out(1.7)',
      scrollTrigger: { trigger: el, start: 'top 85%' }
    });
  });
}

// ===== FLASH AUTO-DISMISS =====
document.querySelectorAll('[data-flash]').forEach(el => {
  setTimeout(() => {
    el.style.animation = 'slideIn 0.4s ease reverse';
    setTimeout(() => el.remove(), 400);
  }, 5000);
});

// ===== INPUT FLOATING LABELS =====
document.querySelectorAll('.input-wrapper input, .input-wrapper select').forEach(input => {
  const update = () => {
    const wrapper = input.closest('.input-wrapper');
    if (input.value || input === document.activeElement) wrapper.classList.add('filled');
    else wrapper.classList.remove('filled');
  };
  input.addEventListener('input', update);
  input.addEventListener('focus', update);
  input.addEventListener('blur', update);
  update();
});
