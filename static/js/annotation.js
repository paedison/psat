function initAnnotation(annotateType) {
  const canvasData = new CanvasData(annotateType)
  const buttonData = new ButtonData(annotateType)

  if (canvasData.exists) {
    const drawingManager = new DrawingManager(canvasData);
    canvasData.$canvas.on("touchstart touchmove", (event) => event.preventDefault()); // 터치 방지

    // 마우스 동작 처리
    drawingManager.tool.onMouseDown = (event) => drawingManager.handleMouseDown(event);
    drawingManager.tool.onMouseDrag = (event) => drawingManager.handleMouseDrag(event);
    drawingManager.tool.onMouseUp = (event) => drawingManager.handleMouseUp(event);

    // 버튼 클릭 이벤트 처리
    buttonData.$drawingBtn.on("click", () => buttonData.handleDrawingBtn(drawingManager, "drawing"));
    buttonData.$lineBtn.on("click", () => buttonData.handleDrawingBtn(drawingManager, "line"));
    buttonData.$highlighterBtn.on(
        "click", () => buttonData.handleDrawingBtn(drawingManager, "highlighter"));
    buttonData.$eraserBtn.on("click", () => buttonData.handleDrawingBtn(drawingManager, "eraser"));
    buttonData.$colorBtn.on("click", (event) => buttonData.handleColorBtn(event, drawingManager));

    buttonData.$undoBtn.on("click", () => drawingManager.undo());
    buttonData.$redoBtn.on("click", () => drawingManager.redo());
    buttonData.$loadBtn.on("click", () => drawingManager.loadDrawing());
    buttonData.$saveBtn.on("click", () => drawingManager.saveDrawing());
    buttonData.$clearBtn.on("click", () => drawingManager.clearAllDrawings());
  }
}


function capitalizeFirstLetter(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}


function getCSRFToken() {
  return $("[name=csrfmiddlewaretoken]").attr("value");
}


function totalInitAnnotation() {
  initAnnotation("normal");
  initAnnotation("wide");
}


$(window).on("load", totalInitAnnotation);
$("body").on("initAnnotation", totalInitAnnotation);


class CanvasData {
  constructor(annotateType) {
    this.annotateType = annotateType;

    // jQuery 객체 정의
    this.$canvas = $(`#${annotateType}Canvas`);
    this.$image = $(`#${annotateType}Image`);

    // 캔버스, 이미지, 필기 처리 주소 정의
    this.canvas = this.$canvas[0]
    this.image = this.$image[0]
    this.annotateUrl = `${this.$canvas.attr("data-annotate-url")}?annotate_type=${annotateType}`

    this.exists = this.$canvas.length && this.$image.length;
    if (this.exists) {
      this.$image.on("load", this.resizeCanvasToImage);
      this.resizeCanvasToImage();
    }
  }

  resizeCanvasToImage() {
    this.canvas.width = this.image.clientWidth;
    this.canvas.height = this.image.clientHeight;
  }
}


class ButtonData {
  constructor(annotateType) {
    // jQuery 객체 정의
    this.annotateType = annotateType
    this.$drawingBtn = $(`#${annotateType}DrawingBtn`);
    this.$lineBtn = $(`#${annotateType}LineBtn`);
    this.$highlighterBtn = $(`#${annotateType}HighlighterBtn`);
    this.$eraserBtn = $(`#${annotateType}EraserBtn`);
    this.$colorBtn = $(`.${annotateType}-color-btn`);
    this.$clearBtn = $(`#${annotateType}ClearBtn`);
    this.$undoBtn = $(`#${annotateType}UndoBtn`);
    this.$redoBtn = $(`#${annotateType}RedoBtn`);
    this.$saveBtn = $(`#${annotateType}SaveBtn`);
    this.$loadBtn = $(`#${annotateType}LoadBtn`);
  }

  getButtonAndStatusJquery(property) {
    let statusId = this.annotateType + capitalizeFirstLetter(property) + 'Status';
    let button = this[`$${property}Btn`];
    let status = $(`#${statusId}`);
    return [button, status]
  }

  toggleDrawingStatus(drawingManager, property) {
    let [button, status] = this.getButtonAndStatusJquery(property);
    drawingManager[`${property}Enabled`] = button.prop("checked");
    status.toggleClass(`${property}-enabled`);
  }

  toggleDrawingBtn(property, isActive) {
    let [button, status] = this.getButtonAndStatusJquery(property);
    if (isActive) {
      button.prop("checked", true).trigger("change");
      status.addClass("enabled");
    } else {
      button.prop("checked", false).trigger("change");
      status.removeClass("enabled");
    }
  }

  activateDrawingPropertyBtn() {
    this.toggleDrawingBtn("drawing", true);
    this.toggleDrawingBtn("eraser", false);
  }

  deactivateDrawingBtn() {
    this.toggleDrawingBtn("drawing", false);
    this.toggleDrawingBtn("line", false);
    this.toggleDrawingBtn("highlighter", false);
    this.toggleDrawingBtn("eraser", false);
  }

  handleDrawingBtn(drawingManager, property) {
    this.toggleDrawingStatus(drawingManager, property);

    if (property === 'eraser') {
      if (drawingManager.eraserEnabled) {
        drawingManager.drawingEnabled = true;
        this.toggleDrawingBtn("drawing", true);
      }
    } else {
      if (drawingManager[`${property}Enabled`]) {
        drawingManager.activateDrawing();
        this.activateDrawingPropertyBtn();
      }

      if (!drawingManager.drawingEnabled) {
        drawingManager.deactivateDrawing();
        this.deactivateDrawingBtn();
      }
    }
    drawingManager.adjustHighlighterSettings();
  }

  handleColorBtn(event, drawingManager) {
    this.$colorBtn.removeClass("active");
    event.currentTarget.classList.add("active");

    const selectedColor = event.currentTarget.dataset["color"];
    let colorcode = DrawingManager.colorMap[selectedColor];

    if (colorcode) {
      drawingManager.currentColor = `rgba(${colorcode}, ${drawingManager.opacity})`; // RGBA 적용
      drawingManager.activateDrawing();
      this.activateDrawingPropertyBtn();
    }
  }
}


class DrawingManager {
  static defaultOpacity = Object.freeze(0.4);
  static defaultStrokeWidth = Object.freeze(2);
  static defaultBlendMode = Object.freeze("normal");

  static highlighterOpacity = Object.freeze(0.3);
  static highlighterBlendMode = Object.freeze("multiply");

  static colorMap = {
    black: "0, 0, 0",
    red: "255, 0, 0",
    blue: "0, 0, 255",
    green: "0, 128, 0",
    yellow: "255, 234, 0",
    orange: "255, 165, 0"
  }

  static angleStep = Math.PI / 100;

  constructor(canvasData) {
    this.canvasData = canvasData;
    this.canvasWidth = canvasData.canvas.width;
    this.highlighterStrokeWidth = this.canvasWidth / 50;

    this.drawingEnabled = false;
    this.lineEnabled = false;
    this.highlighterEnabled = false;
    this.eraserEnabled = false;

    this.opacity = DrawingManager.defaultOpacity;
    this.currentColor = `rgba(0, 0, 0, ${this.opacity})`;
    this.strokeWidth = DrawingManager.defaultStrokeWidth;
    this.blendMode = DrawingManager.defaultBlendMode;

    this.startPoint = null;
    this.previewLine = null;

    this.path = null;
    this.selectedPath = null;
    this.eraserPath = null;

    this.originalAttributes = {};
    this.redoStack = []; // 되돌리기 취소를 위한 저장 공간

    this.paperScope = new paper.PaperScope(); // 개별적인 PaperScope 생성
    this.paperScope.setup(canvasData.canvas); // 해당 캔버스에 Paper.js 설정
    this.tool = new this.paperScope.Tool(); // 개별적인 Tool 생성
  }

  adjustHighlighterSettings() {
    this.opacity = this.highlighterEnabled ? DrawingManager.highlighterOpacity : DrawingManager.defaultOpacity;
    this.strokeWidth = this.highlighterEnabled ? this.highlighterStrokeWidth : DrawingManager.defaultStrokeWidth;
    this.blendMode = this.highlighterEnabled ? DrawingManager.highlighterBlendMode : DrawingManager.defaultBlendMode;
  }

  // 📌 필기 모드 설정
  deactivateDrawing() {
    this.drawingEnabled = false;
    this.lineEnabled = false;
    this.highlighterEnabled = false;
    this.eraserEnabled = false;
  }

  activateDrawing() {
    this.drawingEnabled = true;
    this.eraserEnabled = false;
  }

  getHitResults(event) {
    const point = this.getEventPoint(event)
    return this.paperScope.project.hitTestAll(
        point, {segments: true, stroke: true, tolerance: 5});
  }

  getEventPoint(e) {
    const offset = this.canvasData.$canvas.offset();
    const touch = e.event && e.event.touches ? e.event.touches[0] : e.event || e;
    const x = (touch.pageX || touch.clientX) - offset.left;
    const y = (touch.pageY || touch.clientY) - offset.top;
    return new paper.Point(x, y);
  }

  handleMouseDown(event) {
    const hitResults = this.getHitResults(event);
    const strokeType = this.highlighterEnabled ? 'highlighter' : 'normal'
    console.log(hitResults);

    function isStrokeForSelect(hitResults) {
      return hitResults.length && hitResults[0].type !== 'pixel' && hitResults[0].item.strokeType !== 'eraser'
    }

    if (isStrokeForSelect(hitResults)) return this.selectPath(hitResults[0].item);
    this.deselectPath();

    if (this.eraserEnabled) return this.mouseDownEraserFunction(hitResults, event);
    if (this.lineEnabled) return this.createPreviewLine(event, strokeType);
    if (this.drawingEnabled) return this.createPath(event, strokeType);
  }

  selectPath(path) {
    if (!path) return;

    // 기존 선택된 필기 해제
    this.deselectPath();

    // 새 필기 선택 및 속성 저장
    this.selectedPath = path;
    this.originalAttributes = {
      strokeWidth: this.selectedPath.strokeWidth,
      strokeColor: this.selectedPath.strokeColor,
      opacity: this.selectedPath.opacity,
    };

    // 강조 효과 적용
    if (path.strokeType === 'normal') {
      this.selectedPath.strokeWidth = 4;
      this.selectedPath.strokeColor = 'red';
    } else if (path.strokeType === 'highlighter') {
      this.selectedPath.opacity = 0.8;
    }
  }

  deselectPath() {
    if (this.selectedPath) {
      this.selectedPath.strokeWidth = this.originalAttributes.strokeWidth;
      this.selectedPath.strokeColor = this.originalAttributes.strokeColor;
      this.selectedPath.opacity = this.originalAttributes.opacity;
      this.selectedPath = null;
      this.originalAttributes = {};
    }
  }

  isStrokeForEraser(result) {
    return result.type !== 'pixel' && result.item.strokeType !== 'eraser'
  }

  mouseDownEraserFunction(hitResults, event) {
    if (hitResults.length) {
      hitResults.forEach(result => {
        if (this.isStrokeForEraser(result)) {
          result.item.remove();
          this.paperScope.view.update();
        } else if (result.type === 'pixel') {
          this.createEraserPath(event);
        }
      });
    } else {
      this.createEraserPath(event);
    }
  }

  createEraserPath(event) {
    this.eraserPath = new paper.Path({
      strokeColor: 'black',
      strokeWidth: 20,
      strokeCap: 'round',
      blendMode: 'destination-out',
      strokeType: 'eraser',
    });
    this.eraserPath.add(event.point);
  }

  createPreviewLine(event, strokeType) {
    this.startPoint = event.point;
    this.previewLine = new paper.Path({
      strokeColor: this.currentColor,
      strokeWidth: this.strokeWidth,
      strokeType: strokeType,
    });
    this.previewLine.add(this.startPoint);
    this.previewLine.add(this.startPoint); // 초기에는 같은 점으로 설정
  }

  createPath(event, strokeType) {
    this.path = new this.paperScope.Path({
      strokeColor: this.currentColor,
      strokeWidth: this.strokeWidth,
      blendMode: this.blendMode,
      strokeType: strokeType,
    });
    this.path.add(event.point);
  }

  handleMouseDrag(event) {
    if (this.selectedPath) return this.moveSelectedPath(event);
    if (this.eraserEnabled) return this.mouseDragEraserFunction(event);
    if (this.drawingEnabled && this.path) return this.path.add(event.point);
    if (this.lineEnabled && this.previewLine) return this.adjustPreviewLine(event);
  }

  moveSelectedPath(event) {
    this.selectedPath.position = this.selectedPath.position.add(event.delta); // 필기 이동
  }

  mouseDragEraserFunction(event) {
    const hitResults = this.getHitResults(event);
    if (hitResults.length) {
      hitResults.forEach(result => {
        if (this.isStrokeForEraser(result)) {
          result.item.remove();
          this.paperScope.view.update();
        } else if (this.eraserPath) {
          this.eraserPath.add(event.point);
        }
      });
    }
  }

  adjustPreviewLine(event) {
    let dx = event.point.x - this.startPoint.x;
    let dy = event.point.y - this.startPoint.y;
    let angle = Math.atan2(dy, dx); // 현재 각도 계산
    let snappedAngle = Math.round(angle / DrawingManager.angleStep) * DrawingManager.angleStep;
    let length = Math.sqrt(dx * dx + dy * dy);
    let newX = this.startPoint.x + length * Math.cos(snappedAngle);
    let newY = this.startPoint.y + length * Math.sin(snappedAngle);

    this.previewLine.lastSegment.point = new this.paperScope.Point(newX, newY);
  }

  handleMouseUp() {
    const strokeType = this.highlighterEnabled ? 'highlighter' : 'normal'

    if (this.eraserEnabled) return this.mouseUpEraserFunction();
    if (this.lineEnabled && this.startPoint) return this.createPathFromPreviewLine(strokeType);
    if (this.drawingEnabled && this.path) return this.simplifyPath();
  }

  mouseUpEraserFunction() {
    this.eraserPath = null;
  }

  createPathFromPreviewLine(strokeType) {
    //최종 직선 생성
    const path = new this.paperScope.Path({
      strokeColor: this.currentColor,
      strokeWidth: this.strokeWidth,
      strokeType: strokeType,
    });
    path.add(this.startPoint);
    path.add(this.previewLine.lastSegment.point); // 조정된 끝점 사용

    // 임시 직선 제거
    this.previewLine.remove();
    this.previewLine = null;
    this.startPoint = null; // 시작점 초기화
  }

  simplifyPath() {
    this.path.simplify();
    this.path = null;
  }

  undo() {
    const items = this.paperScope.project.activeLayer.children;

    if (items.length > 0) {
      const lastItem = items[items.length - 1]; // 마지막 요소 가져오기
      this.redoStack.push(lastItem); // 되돌리기 취소를 위해 저장
      lastItem.remove(); // 마지막 요소 제거
      this.paperScope.view.update(); // 화면 업데이트
    } else {
      alert("되돌릴 필기 내용이 없습니다!");
    }
  }

  redo() {
    if (this.redoStack.length > 0) {
      const restoredItem = this.redoStack.pop(); // 저장된 요소 가져오기
      this.paperScope.project.activeLayer.addChild(restoredItem); // 다시 추가
      this.paperScope.view.update(); // 화면 업데이트
    } else {
      alert("되돌리기 취소할 내용이 없습니다!");
    }
  }

  loadDrawing() {
    if (!confirm("저장된 필기 이미지를 불러오시겠습니까?\n현재 필기 내용은 삭제됩니다.")) {
      return;
    }

    fetch(this.canvasData.annotateUrl)
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            this.paperScope.setup(this.canvasData.canvas); // 해당 캔버스에 Paper.js 설정
            this.canvasData.resizeCanvasToImage();

            const raster = new this.paperScope.Raster({
              source: data.image_url,
              position: this.paperScope.view.center
            })
            raster.sendToBack();
            raster.onLoad = () => {
              raster.fitBounds(this.paperScope.view.bounds, true); // 캔버스 크기에 맞게 조정
            }
          } else {
            alert("저장된 필기 데이터가 없습니다.");
          }
        })
        .catch(error => alert("❌ 불러오기 중 오류 발생: " + error));
  }

  saveDrawing() {
    if (!confirm("현재 필기 내용을 저장하시겠습니까?")) {
      return;
    }

    if (!this.canvasData.$canvas) {
      alert("❌ 캔버스를 찾을 수 없습니다!");
      return;
    }

    fetch(this.canvasData.annotateUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCSRFToken() // CSRF 토큰 추가
      },
      body: JSON.stringify({
        annotateType: this.canvasData.annotateType,
        image: this.canvasData.canvas.toDataURL("image/png"),
      })
    })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            alert("✅ 필기 내용이 성공적으로 저장되었습니다!");
          } else {
            alert("❌ 저장 실패: " + data.error);
          }
        })
        .catch(error => alert("❌ 저장 중 오류 발생: " + error));
  }

  clearAllDrawings() {
    if (!confirm("전체 필기 내용을 삭제하시겠습니까?")) {
      return;
    }
    this.paperScope.project.activeLayer.removeChildren();
    this.paperScope.view.update();
  }
}
