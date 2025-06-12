let canvas, ctx;
let drawing = false;
let drawMode = false;
let textMode = false;
let mode = "pen";  // pen | highlighter | eraser
let currentColor = "#000000";
let eraserSize = 20;
let lastX = 0;
let lastY = 0;

function initAnnotationFunction() {
    const img = document.getElementById('problem-image-wide');
    if (img) {
        canvas = document.getElementById('annotation-canvas-wide');
        ctx = canvas.getContext('2d');

        canvas.width = img.clientWidth;
        canvas.height = img.clientHeight;

        ctx.lineWidth = 2;
        ctx.lineJoin = "round";
        ctx.lineCap = "round";
        ctx.strokeStyle = currentColor;
        ctx.fillStyle = currentColor;

        $('#pen-button').on('click', () => activatePen())
        function activatePen() {
            drawMode = true;
            textMode = false;
            mode = "pen";
            canvas.classList.remove("eraser-cursor");
            canvas.style.cursor = 'crosshair';
        }

        $('#highlighter-button').on('click', () => activateHighlighter())
        function activateHighlighter() {
            drawMode = true;
            textMode = false;
            mode = "highlighter";
            canvas.classList.remove("eraser-cursor");
            canvas.style.cursor = 'crosshair';
        }

        $('#eraser-button').on('click', () => activateEraser())
        function activateEraser() {
            drawMode = true;
            textMode = false;
            mode = "eraser";
            canvas.classList.add("eraser-cursor");
        }

        $('#text-button').on('click', () => enableTextMode())
        function enableTextMode() {
            textMode = true;
            drawMode = false;
            mode = null;
            canvas.classList.remove("eraser-cursor");
            canvas.style.cursor = 'text';
        }

        function changeColor(color) {
            currentColor = color;
            ctx.strokeStyle = color;
            ctx.fillStyle = color;
        }

        function updateBrushStyle() {
            if (mode === "pen") {
                ctx.globalAlpha = 1.0;
                ctx.strokeStyle = currentColor;
                ctx.lineWidth = 2;
            } else if (mode === "highlighter") {
                ctx.globalAlpha = 0.3;
                ctx.strokeStyle = currentColor;
                ctx.lineWidth = 10;
            } else if (mode === "eraser") {
                ctx.globalAlpha = 1.0;
                ctx.lineWidth = eraserSize;
            }
        }

        $('#save-button').on('click', () => saveAnnotation())
        function saveAnnotation() {
            const imageData = canvas.toDataURL("image/png");
            fetch("", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}',
                },
                body: JSON.stringify({image: imageData})
            }).then(response => {
                if (response.ok) {
                    alert("저장 완료!");
                } else {
                    alert("저장 실패");
                }
            });
        }


        function getPosition(event) {
            let x, y;
            if (event.touches) {
                const touch = event.touches[0];
                const rect = canvas.getBoundingClientRect();
                x = touch.clientX - rect.left;
                y = touch.clientY - rect.top;
            } else {
                x = event.offsetX;
                y = event.offsetY;
            }
            return [x, y]
        }

        function drawStart(e) {
            if (!drawMode) return;
            e.preventDefault();
            drawing = true;

            let [x, y] = getPosition(e);
            [lastX, lastY] = [x, y]

            ctx.beginPath();
            ctx.moveTo(x, y);
            updateBrushStyle();
        }

        function drawWorking(e) {
            if (!drawing) return;
            e.preventDefault();

            let [x, y] = getPosition(e);
            if (mode === "eraser") {
                ctx.clearRect(x - eraserSize / 2, y - eraserSize / 2, eraserSize, eraserSize);
            } else {
                ctx.lineTo(x, y);
                ctx.stroke();
            }
        }

        function drawEnd() {
            drawing = false;
            ctx.globalAlpha = 1.0;  // 항상 원상 복귀
        }

        $('#eraser-size').on('input', (e) => {
            eraserSize = parseInt(e.target.value);
            $('#eraser-size-label').text(`${eraserSize}px`);
        })

        $('#annotation-canvas-wide')
            .on('mousedown touchstart', (e) => drawStart(e))
            .on('mousemove touchmove', (e) => drawWorking(e))
            .on('mouseup touchend', () => drawEnd())
    }
}

$(window).on('load', () => initAnnotationFunction());
$('body').on('initAnnotation', () => initAnnotationFunction());
