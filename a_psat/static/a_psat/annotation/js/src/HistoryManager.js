export default class HistoryManager {
  constructor() {
    this.redoStack = [];
  }

  undo() {
    const items = paper.project.activeLayer.children;
    if (items.length > 0) {
      const lastItem = items[items.length - 1];
      this.redoStack.push(lastItem);
      lastItem.remove();
      paper.view.update();
    } else {
      alert("되돌릴 필기 내용이 없습니다!");
    }
  }

  redo() {
    if (this.redoStack.length > 0) {
      const restoredItem = this.redoStack.pop();
      paper.project.activeLayer.addChild(restoredItem);
      paper.view.update();
    } else {
      alert("되돌리기 취소할 내용이 없습니다!");
    }
  }
}
