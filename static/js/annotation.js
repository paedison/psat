function initAnnotation(annotateType) {
  const $canvas = $(`#${annotateType}Canvas`);
  const $image = $(`#${annotateType}Image`);

  if ($canvas.length && $image.length) {
    const canvas = $canvas[0]
    const image = $image[0]

    function resizeCanvasToImage() {
      canvas.width = image.clientWidth;
      canvas.height = image.clientHeight;
    }

    $image.on("load", resizeCanvasToImage);
    resizeCanvasToImage();

    const annotateUrl = $canvas.attr("data-annotate-url")
    const paperScope = new paper.PaperScope(); // 개별적인 PaperScope 생성
    paperScope.setup(canvas); // 해당 캔버스에 Paper.js 설정

    let path = null;
    let drawingEnabled = false;
    let opacity = 0.4;
    let currentColor = `rgba(0, 0, 0, ${opacity})`; // 검은색, 투명도 80%
    let eraserEnabled = false; // 지우개 모드 변수 추가

    const colorMap = {
      black: "0, 0, 0",
      red: "255, 0, 0",
      blue: "0, 0, 255",
      green: "0, 128, 0"
    }

    const tool = new paperScope.Tool(); // 개별적인 Tool 생성

    function getHitResultFromEvent(event) {
      return paperScope.project.hitTest(event.point, {
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
        paperScope.view.update();
      }
    }

    function saveAnnotation() {
      if (!confirm("현재 필기 내용을 저장하시겠습니까?")) {
        return;
      }

      if (!$canvas) {
        alert("❌ 캔버스를 찾을 수 없습니다!");
        return;
      }

      const imageData = canvas.toDataURL("image/png"); // 캔버스를 PNG 이미지로 변환

      fetch(annotateUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken() // CSRF 토큰 추가
        },
        body: JSON.stringify({
          annotateType: annotateType,
          image: imageData
        })
      })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              alert("✅ 필기 이미지가 성공적으로 저장되었습니다!");
            } else {
              alert("❌ 저장 실패: " + data.error);
            }
          })
          .catch(error => alert("❌ 저장 중 오류 발생: " + error));
    }

    function loadAnnotation() {
      if (!confirm("저장된 필기 이미지를 불러오시겠습니까?\n현재 필기 내용은 삭제됩니다.")) {
        return;
      }

      fetch(`${annotateUrl}?annotate_type=${annotateType}`)
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              const imageUrl = data.image_url;

              paperScope.setup(canvas); // 해당 캔버스에 Paper.js 설정
              resizeCanvasToImage();

              const raster = new paperScope.Raster({
                source: imageUrl,
                position: paperScope.view.center
              })

              raster.onLoad = function () {
                raster.fitBounds(paperScope.view.bounds, true); // 캔버스 크기에 맞게 조정
              }
            } else {
              alert("❌ 불러오기 실패: " + data.error);
            }
          })
          .catch(error => alert("❌ 불러오기 중 오류 발생: " + error));

    }

    function getCSRFToken() {
      return $("[name=csrfmiddlewaretoken]").attr("value");
    }

    // 마우스 클릭 시 삭제 여부 확인
    tool.onMouseDown = function (event) {
      if (eraserEnabled) {
        processErase(event);
      } else if (drawingEnabled) {
        path = new paperScope.Path({
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

    // 버튼 클릭 이벤트 처리
    $(`#${annotateType}DrawingBtn`).on("click", function () {
      drawingEnabled = !drawingEnabled;
      $(this).text(drawingEnabled ? "🛑 필기 중지" : "✍️ 필기 시작");
      // $(this).toggleClass('active', drawingEnabled);
    });

    $(`#${annotateType}EraserBtn`).on('click', function () {
      eraserEnabled = !eraserEnabled;
      $(this).text(eraserEnabled ? "🧹 삭제 모드" : "📝 필기 모드");
    });

    $(`.${annotateType}-annotate-color`).on("click", function () {
      const selectedColor = $(this).data("color");
      let colorcode = colorMap[selectedColor]
      if (colorcode) {
        currentColor = `rgba(${colorcode}, ${opacity})`; // RGBA 적용
      }
      // $('.colorBtn').removeClass('active');
      // $(this).addClass('active');
    });

    $(`#${annotateType}ClearBtn`).on("click", function () {
      paperScope.project.activeLayer.removeChildren();
      paperScope.view.update();
    });

    $(`#${annotateType}SaveBtn`).on("click", function () {
      saveAnnotation();
    });

    $(`#${annotateType}LoadBtn`).on("click", function () {
      loadAnnotation();
    });

    // 터치 방지
    $canvas.on("touchstart touchmove", function (e) {
      e.preventDefault();
    });
  }
}

$(window)
    .on("load", () => {
      initAnnotation("normal");
      initAnnotation("wide");
    })
$("body")
    .on("initAnnotation", () => {
      initAnnotation("normal");
      initAnnotation("wide");
    })
