import { constants } from '../Constants.js';
import Tool from "./Tool.js";

export default class LineTool extends Tool {
  #startPoint = null;
  #previewLine = null;
  
  constructor(scope, color, style) {
    super(scope, color, style);
  }
  
  handleMouseDown(event) {
    const selectedHit = this.getSelectedHit(event);
    if (selectedHit) return this.selectPath(selectedHit);
    this.deselectPath();
    this.createPreviewLine(event)
  }
  
  handleMouseDrag(event) {
    if (this.selectedPath) this.moveSelectedPath(event);
    if (this.#previewLine) this.adjustPreviewLine(event);
  }

  handleMouseUp(event) {
    if (this.#startPoint) return this.createPathFromPreviewLine();
  }

  createPreviewLine(event) {
    this.#startPoint = event.point;
    this.#previewLine = new this.scope.Path(this.defaultAttr);
    this.#previewLine.add(this.#startPoint);
    this.#previewLine.add(this.#startPoint); // 초기에는 같은 점으로 설정
  }

  createPathFromPreviewLine() {
    const path = new this.scope.Path(this.defaultAttr);
    path.add(this.#startPoint);
    path.add(this.#previewLine.lastSegment.point); // 조정된 끝점 사용

    // 임시 직선 제거
    this.#previewLine.remove();
    this.#previewLine = null;
    this.#startPoint = null; // 시작점 초기화
  }
  
  adjustPreviewLine(event) {
    const startPoint = this.#startPoint;
    const angleStep = constants.angleStep;
    
    const dx = event.point.x - startPoint.x;
    const dy = event.point.y - startPoint.y;
    const angle = Math.atan2(dy, dx);
    const snappedAngle = Math.round(angle / angleStep) * angleStep;
    const length = Math.sqrt(dx * dx + dy * dy);
    
    const newX = startPoint.x + length * Math.cos(snappedAngle);
    const newY = startPoint.y + length * Math.sin(snappedAngle);
    this.#previewLine.lastSegment.point = new this.scope.Point(newX, newY);
  }
}
