export default class HistoryManager {
  constructor(scope) {
    this.scope = scope;
    this.btnManager = scope.btnManager;
    this.undoStack = [];
    this.redoStack = [];
  }
  
  updateBtns() {
    this.btnManager.undoBtn.disabled = this.undoStack.length === 0;
    this.btnManager.redoBtn.disabled = this.redoStack.length === 0;
  }
  
  pushState(item) {
    this.undoStack.push(item);
    this.redoStack = [];
    this.updateBtns();
  }

  undoAnnotation() {
    if (this.undoStack.length === 0) return alert("되돌릴 필기 내용이 없습니다!");
    
    const lastPath = this.undoStack.pop();
    this.redoStack.push(lastPath);
    this.updateBtns();
    lastPath?.remove();
  }

  redoAnnotation() {
    if (this.redoStack.length === 0) return alert("되돌리기 취소할 내용이 없습니다!");

    const restoredPath = this.redoStack.pop();
    this.undoStack.push(restoredPath);
    this.updateBtns();
    if (restoredPath) this.scope.project.activeLayer.addChild(restoredPath);
  }
  
  clear() {
    this.undoStack = [];
    this.redoStack = [];
  }
}
