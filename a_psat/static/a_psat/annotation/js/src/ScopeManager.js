import ToolManager from './ToolManager.js';
import UIManager from './UIManager.js';

export default class ScopeManager {
  scopes = {};
  #activeScope = null;
  
  create(name, canvas, image) {
    if (this.scopes[name]) return this.scopes[name];

    const annotateUrl = canvas?.getAttribute('data-annotate-url');
    const scope = new paper.PaperScope();
    
    scope.name = name;
    scope.canvas = canvas;
    scope.image = image;
    scope.annotateUrl = annotateUrl;
    
    scope.setup(canvas);
    this.scopes[name] = scope;
    
    // 매니저 초기화
    // const historyManager = new HistoryManager();
    // const fileManager = new FileManager(canvas, annotateUrl, annotateType);
    this.toolManager = new ToolManager(scope);
    this.uiManager = new UIManager(name, this.toolManager);
    
    this.uiManager.init();
    
    this.resizeCanvasToImage(scope, image);

    return scope;
  }

  resizeCanvasToImage(scope, image) {
    const canvas = scope.view.element;
    const width = image.clientWidth;
    const height = image.clientHeight;
    
    const resizeCanvas = () => {
      canvas.width = width;
      canvas.height = height;
      canvas.style.width = width + 'px';
      canvas.style.height = height + 'px';
      
      scope.view.viewSize = new scope.Size(canvas.width, canvas.height);
      scope.view.update();
    }
    resizeCanvas();
  }
  
  get(name) {
    return this.scopes[name] || null;
  }

  list() {
    return Object.keys(this.scopes);
  }

  activate(name) {
    // 현재 활성 스코프 비활성화
    if (this.#activeScope) {
      this.#activeScope.view.element.style.pointerEvents = 'none';
      this.#activeScope.project.activeLayer.selected = false;
    }
    
    // 새 스코프 활성화
    const scope = this.get(name);
    if (scope) {
      this.#activeScope = scope;
      this.#activeScope.activate(); // paper 전역이 이 scope를 바라보도록 함
      this.#activeScope.view.element.style.pointerEvents = 'auto';
    }
  }
}
