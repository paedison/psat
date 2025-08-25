import ButtonManager from "./ButtonManager.js";
import HistoryManager from "./HistoryManager.js";
import ToolManager from './ToolManager.js';
import UIManager from './UIManager.js';
import FileManager from "./FileManager.js";

export default class ScopeManager {
  scopes = {};
  #activeScope = null;
  
  create(annotateType, canvas, image) {
    if (this.scopes[annotateType]) return this.scopes[annotateType];

    const annotateUrl = `${canvas?.getAttribute('data-annotate-url')}?annotate_type=${annotateType}`;
    const scope = new paper.PaperScope();
    
    scope.canvas = canvas;
    scope.image = image;
    scope.annotateUrl = annotateUrl;
    scope.annotateType = annotateType;
    
    scope.setup(canvas);
    this.scopes[annotateType] = scope;
    
    // 매니저 초기화
    scope.btnManager = new ButtonManager(scope);
    scope.historyManager = new HistoryManager(scope);
    scope.toolManager = new ToolManager(scope);
    scope.fileManager = new FileManager(scope);
    scope.uiManager = new UIManager(scope);
    
    scope.uiManager.init();
    
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
  
  get(annotateType) {
    return this.scopes[annotateType] || null;
  }

  list() {
    return Object.keys(this.scopes);
  }

  activate(annotateType) {
    // 현재 활성 스코프 비활성화
    if (this.#activeScope) {
      this.#activeScope.view.element.style.pointerEvents = 'none';
      this.#activeScope.project.activeLayer.selected = false;
    }
    
    // 새 스코프 활성화
    const scope = this.get(annotateType);
    if (scope) {
      this.#activeScope = scope;
      this.#activeScope.activate(); // paper 전역이 이 scope를 바라보도록 함
      this.#activeScope.view.element.style.pointerEvents = 'auto';
    }
  }
}
