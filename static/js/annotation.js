function initAnnotationFunction() {
  const $canvas = $('#annotation-canvas-wide');
  const $image = $('#problem-image-wide');

  if ($canvas || $image) {
    function resizeCanvasToImage() {
      $canvas[0].width = $image[0].clientWidth;
      $canvas[0].height = $image[0].clientHeight;
    }

    $image.on('load', resizeCanvasToImage);
    resizeCanvasToImage();

    paper.setup($canvas[0]);

    let path = null;
    let drawingEnabled = false;
    let opacity = 0.4;
    let currentColor = `rgba(0, 0, 0, ${opacity})`; // 검은색, 투명도 80%
    let eraserEnabled = false; // 지우개 모드 변수 추가

    const colorMap = {
      black: '0, 0, 0',
      red: '255, 0, 0',
      blue: '0, 0, 255',
      green: '0, 128, 0'
    }

    const tool = new paper.Tool();

    function getHitResultFromEvent(event) {
      return paper.project.hitTest(event.point, {
        segments: false,
        stroke: true,
        fill: false,
        tolerance: 5
      });
    }

    function processErase(event) {
      const hitResult = getHitResultFromEvent(event);
      if (hitResult && hitResult.item) {
        hitResult.item.remove();
        paper.view.update();
      }
    }

    // 마우스 클릭 시 삭제 여부 확인
    tool.onMouseDown = function (event) {
      if (eraserEnabled) {
        processErase(event);
      } else if (drawingEnabled) {
        path = new paper.Path({
          strokeColor: currentColor,
          strokeWidth: 2
        });
        path.add(event.point);
      }
    };

    tool.onMouseDrag = function (event) {
      if (eraserEnabled) {
        processErase(event);
      } else if (drawingEnabled && path) {
        path.add(event.point);
      }
    };

    tool.onMouseUp = function () {
      if (path) {
        path.simplify();
        path = null;
      }
    };

    // 필기 토글 버튼
    $('#toggle-drawing-button').on('click', function () {
      drawingEnabled = !drawingEnabled;
      $(this).text(drawingEnabled ? '🛑 필기 중지' : '✍️ 필기 시작');
      // $(this).toggleClass('active', drawingEnabled);
    });

    // 지우개 버튼 이벤트 처리
    $('#eraser-button').on('click', function () {
      eraserEnabled = !eraserEnabled;
      $(this).text(eraserEnabled ? '🧹 삭제 모드' : '📝 필기 모드');
    });

    // 색상 선택 버튼
    $('.annotate-color').on('click', function () {
      const selectedColor = $(this).data('color');
      let colorcode = colorMap[selectedColor]
      if (colorcode) {
        currentColor = `rgba(${colorcode}, ${opacity})`; // RGBA 적용
      }
      // $('.colorBtn').removeClass('active');
      // $(this).addClass('active');
    });

    // 지우기 버튼
    $('#clear-button').on('click', function () {
      paper.project.activeLayer.removeChildren();
      paper.view.update();
    });

    // 터치 방지
    $canvas.on('touchstart touchmove', function (e) {
      e.preventDefault();
    });
  }
}

$(window).on('load', () => initAnnotationFunction());
$('body').on('initAnnotation', () => initAnnotationFunction());
