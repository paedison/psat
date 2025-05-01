let canvas, ctx;
let drawing = false;
let drawMode = false;
let textMode = false;
let mode = "pen";  // pen | highlighter | eraser
let currentColor = "#000000";
let eraserSize = 20;
let lastX = 0;
let lastY = 0;

window.onload = () => {
    const img = document.getElementById('problem-image-wide');
    canvas = document.getElementById('annotation-canvas-wide');
    ctx = canvas.getContext('2d');

    canvas.width = img.clientWidth;
    canvas.height = img.clientHeight;

    ctx.lineWidth = 2;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";
    ctx.strokeStyle = currentColor;
    ctx.fillStyle = currentColor;

    canvas.addEventListener('mousedown', (e) => {
        const x = e.offsetX;
        const y = e.offsetY;

        if (textMode) {
            const text = prompt("삽입할 텍스트:");
            if (text) {
                ctx.font = "20px sans-serif";
                ctx.globalAlpha = 1.0;
                ctx.fillStyle = currentColor;
                ctx.fillText(text, x, y);
            }
            textMode = false;
            canvas.style.cursor = drawMode ? 'crosshair' : 'default';
            return;
        }

        if (!drawMode) return;
        drawing = true;
        lastX = x;
        lastY = y;

        // 설정
        ctx.beginPath();
        ctx.moveTo(x, y);
        updateBrushStyle();
    });

    canvas.addEventListener('mousemove', (e) => {
        if (!drawing) return;
        const x = e.offsetX;
        const y = e.offsetY;

        if (mode === "eraser") {
            ctx.clearRect(x - eraserSize / 2, y - eraserSize / 2, eraserSize, eraserSize);
        } else {
            ctx.lineTo(x, y);
            ctx.stroke();
        }
    });

    canvas.addEventListener('mouseup', () => {
        drawing = false;
        ctx.globalAlpha = 1.0;  // 항상 원상 복귀
    });

    // 터치 시작
    canvas.addEventListener('touchstart', (e) => {
        if (!drawMode) return;
        e.preventDefault();

        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const y = touch.clientY - rect.top;

        drawing = true;
        lastX = x;
        lastY = y;

        ctx.beginPath();
        ctx.moveTo(x, y);
        updateBrushStyle();
    });

    // 터치 이동
    canvas.addEventListener('touchmove', (e) => {
        if (!drawing) return;
        e.preventDefault();

        const touch = e.touches[0];
        const rect = canvas.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const y = touch.clientY - rect.top;

        if (mode === "eraser") {
            ctx.clearRect(x - eraserSize / 2, y - eraserSize / 2, eraserSize, eraserSize);
        } else {
            ctx.lineTo(x, y);
            ctx.stroke();
        }
    });

    // 터치 끝
    canvas.addEventListener('touchend', () => {
        drawing = false;
        ctx.globalAlpha = 1.0;
    });

    document.getElementById('eraser-size').addEventListener('input', (e) => {
        eraserSize = parseInt(e.target.value);
        document.getElementById('eraser-size-label').innerText = `${eraserSize}px`;
    });
};

// 모드 설정 함수들
function toggleDraw() {
    drawMode = true;
    textMode = false;
    mode = "pen";
    canvas.classList.remove("eraser-cursor");
    canvas.style.cursor = 'crosshair';
}

function activateHighlighter() {
    drawMode = true;
    textMode = false;
    mode = "high" +
        "lighter";
    canvas.classList.remove("eraser-cursor");
    canvas.style.cursor = 'crosshair';
}

function activateEraser() {
    drawMode = true;
    textMode = false;
    mode = "eraser";
    canvas.classList.add("eraser-cursor");
}

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

// 현재 mode에 따라 스타일 반영
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
