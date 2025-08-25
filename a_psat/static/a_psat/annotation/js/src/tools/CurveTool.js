import Tool from "./Tool.js";

export default class CurveTool extends Tool {
  constructor(scope, color, style) {
    super(scope, color, style);
  }

  handleMouseDown(event) {
    const selectedHit = this.getSelectedHit(event);
    if (selectedHit) return this.selectPath(selectedHit);
    this.deselectPath();
    return this.createPath(event);
  }
  
  handleMouseDrag(event) {
    if (this.selectedPath) return this.moveSelectedPath(event);

    if (this.path) {
      this.path.add(event.point);
      this.path.smooth();
    }
  }
  
  handleMouseUp(event) {
    this.pushStateIntoUndoStack();
    if (this.path) {
      this.path.simplify();
      this.path = null;
    }
  }

  createPath(event) {
    this.path = new this.scope.Path(this.defaultAttr);
    this.path.add(event.point);
  }

  emphasizePath() {
    this.selectedPath.strokeWidth = 4;
    this.selectedPath.strokeColor = 'red';
  }
}
