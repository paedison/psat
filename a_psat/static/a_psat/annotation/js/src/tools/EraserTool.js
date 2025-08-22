import Tool from "./Tool.js";

export default class EraserTool extends Tool {
  eraserPath = null;
  constructor(scope, color, style) {
    super(scope, color, style);
  }
  
  handleMouseDown(event) {
    const hitResults = this.getHitResults(event);
    if (!hitResults.length) return this.createEraserPath(event);
    
    hitResults.forEach(result => {
      if (result.type === 'pixel') return this.createEraserPath(event);
      result.item.remove();
      this.scope.view.update();
    });
  }

  createEraserPath(event) {
    this.eraserPath = new this.scope.Path({
      strokeColor: this.color,
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
      if (result.type === 'stroke') return  result.item.remove();
      if (this.eraserPath) return this.eraserPath.add(event.point);
    });
  }
  
  handleMouseUp(event) {
    this.eraserPath = null;
  }
}
