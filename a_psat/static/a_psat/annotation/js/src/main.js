import ScopeManager from './ScopeManager.js';

const scopeManager = new ScopeManager();

window.addEventListener('load', totalInitAnnotation);
document.body.addEventListener('initAnnotation', totalInitAnnotation);

function totalInitAnnotation() {
  window.innerWidth < 992 ? initAnnotation('normal') : initAnnotation('wide');
}

function initAnnotation(annotateType) {
  const canvas = document.getElementById(`${annotateType}Canvas`);
  const image = document.getElementById(`${annotateType}Image`);
  
  if (!canvas || !image) return;
  
  scopeManager.create(annotateType, canvas, image);

  const events = ['touchstart', 'touchmove', 'click'];
  events.forEach(eventType => {
    canvas.addEventListener(eventType, e => e.preventDefault(), {passive: false});
  });
}

window.addEventListener('resize', () => {
  if (window.innerWidth < 992) {
    if (!scopeManager.scopes.normal) initAnnotation('normal');
    scopeManager.activate('normal')
  } else {
    if (!scopeManager.scopes.wide) initAnnotation('wide');
    scopeManager.activate('wide')
  }
});
