import ScopeManager from './ScopeManager.js';

const scopeManager = new ScopeManager();

window.addEventListener('load', initAnnotation);
document.body.addEventListener('initAnnotation', initAnnotation);

document.body.addEventListener('htmx:beforeRequest', () => delete scopeManager.scopes[getAnnotateType()]);

window.addEventListener('resize', () => initAnnotation());

function getAnnotateType() {
  return window.innerWidth < 992 ? 'normal' : 'wide';
}

function initAnnotation() {
  const annotateType = getAnnotateType();
  const canvas = document.getElementById(`${annotateType}Canvas`);
  const image = document.getElementById(`${annotateType}Image`);
  if (!canvas || !image) return;
  
  scopeManager.create(annotateType, canvas, image);
  scopeManager.activate(annotateType)
}
