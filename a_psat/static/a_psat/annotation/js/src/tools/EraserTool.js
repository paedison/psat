import Tool from "./Tool.js";

export default class EraserTool extends Tool {
  eraserPath = null;
  constructor(scope, color, style) {
    super(scope, color, style);
  }
  
  isStrokeForEraser(result) {
    return result.type !== 'pixel' && result.item.strokeType !== 'eraser'
  }
  
  handleMouseDown(event) {
    const hitResults = this.getHitResults(event);
    if (!hitResults.length) return this.createEraserPath(event);
    
    hitResults.forEach(result => {
      if (result.type === 'pixel') return this.createEraserPath(event);
      if (this.isStrokeForEraser(result)) return result.item.remove();
    });
  }

  createEraserPath(event) {
    this.eraserPath = new this.scope.Path({
      strokeType: 'eraser',
      strokeColor: this.strokeColor,
      strokeWidth: this.strokeWidth,
      strokeCap: this.strokeCap,
      blendMode: this.blendMode,
    });
    this.eraserPath.add(event.point);
  }
  
  handleMouseDrag(event) {
    const hitResults = this.getHitResults(event);
    if (!hitResults.length) return;

    hitResults.forEach(result => {
      if (this.isStrokeForEraser(result)) return result.item.remove();
      if (this.eraserPath) return this.eraserPath.add(event.point);
    });
  }
  
  handleMouseUp(event) {
    this.pushStateIntoUndoStack();
    this.eraserPath = null;
  }
}
