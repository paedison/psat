export default class Tool {
  constructor(scope, color, style) {
    this.scope = scope;
    
    const {strokeWidth, strokeCap, blendMode, emphasizeStrokeColor, emphasizeStrokeWidth} = style
    this.strokeColor = color;
    this.strokeWidth = strokeWidth;
    this.strokeCap = strokeCap;
    this.blendMode = blendMode;
    this.emphasizeStrokeWidth = emphasizeStrokeWidth;
    this.emphasizeStrokeColor = emphasizeStrokeColor;
    
    this.defaultAttr = {
      strokeColor: color,
      strokeWidth: strokeWidth,
      strokeCap: strokeCap,
      blendMode: blendMode,
    }
    
    this.canvas = scope.view.element;
    this.path = null;
    this.selectedPath = null;
    this.originalAttr = {};
    
    this.tool = new scope.Tool();
    
    this.initEvents();
  }
  
  deactivate() {
    this.deselectPath();
    this.tool.remove();
  }

  initEvents() {
    this.tool.onMouseUp = (event) => this.handleMouseUp(event);
    this.tool.onMouseDrag = (event) => this.handleMouseDrag(event);
    this.tool.onMouseDown = (event) => this.handleMouseDown(event);
  }

  handleMouseDown(event) {
    throw new Error('execute() must be implemented by subclass');
  }
  
  handleMouseDrag(event) {
    throw new Error('execute() must be implemented by subclass');
  }
  
  handleMouseUp(event) {
    throw new Error('execute() must be implemented by subclass');
  }
  
  getSelectedHit(event) {
    const hitResults = this.getHitResults(event);
    const isSelected = hitResults.length && hitResults[0].type === 'stroke';
    if (isSelected) return hitResults[0].item;
  }
  
  getHitResults(e) {
    const rect = this.canvas.getBoundingClientRect();
    const touch = e.event && e.event.touches ? e.event.touches[0] : e.event || e;
    
    const x = (touch.pageX || touch.clientX) - rect.left;
    const y = (touch.pageY || touch.clientY) - rect.top;

    const point = new paper.Point(x, y);
    return this.scope.project.hitTestAll(point, {segments: true, stroke: true, tolerance: 5});
  }

  selectPath(path) {
    if (!path) return;

    // 기존 선택된 필기 해제
    this.deselectPath();

    // 새 필기 선택 및 속성 저장
    this.selectedPath = path;
    this.originalAttr = {
      strokeWidth: this.selectedPath.strokeWidth,
      strokeColor: this.selectedPath.strokeColor,
      opacity: this.selectedPath.opacity,
    };

    // 강조 효과 적용
    this.selectedPath.strokeWidth = this.emphasizeStrokeWidth;
    this.selectedPath.strokeColor = this.emphasizeStrokeColor;
  }

  deselectPath() {
    if (this.selectedPath) {
      this.selectedPath.strokeWidth = this.originalAttr.strokeWidth;
      this.selectedPath.strokeColor = this.originalAttr.strokeColor;
      this.selectedPath.opacity = this.originalAttr.opacity;
      this.selectedPath = null;
      this.originalAttr = {};
    }
  }
  
  moveSelectedPath(event) {
    this.selectedPath.position = this.selectedPath.position.add(event.delta); // 필기 이동
  }

  updateColor(newColor) {
    this.strokeColor = newColor;
    this.defaultAttr.strokeColor = newColor;
  }
  
  pushStateIntoUndoStack() {
    if (this.path) this.scope.historyManager.pushState(this.path);
  }
}
