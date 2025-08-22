export default class FileManager {
  constructor(canvasEl, annotateUrl, annotateType) {
    this.canvas = canvasEl;
    this.annotateUrl = annotateUrl;
    this.annotateType = annotateType;
  }

  save(csrfToken) {
    if (!confirm("현재 필기 내용을 저장하시겠습니까?")) return;

    fetch(this.annotateUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken
      },
      body: JSON.stringify({
        annotateType: this.annotateType,
        image: this.canvas.toDataURL("image/png"),
      })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          alert("✅ 필기 내용이 성공적으로 저장되었습니다!");
        } else {
          alert("❌ 저장 실패: " + data.error);
        }
      })
      .catch(err => alert("❌ 저장 중 오류 발생: " + err));
  }

  load() {
    if (!confirm("저장된 필기 이미지를 불러오시겠습니까?\n현재 필기 내용은 삭제됩니다.")) return;

    fetch(this.annotateUrl)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          const raster = new paper.Raster({
            source: data.image_url,
            position: paper.view.center
          });
          raster.sendToBack();
          raster.onLoad = () => {
            raster.fitBounds(paper.view.bounds, true);
          };
        } else {
          alert("저장된 필기 데이터가 없습니다.");
        }
      })
      .catch(err => alert("❌ 불러오기 중 오류 발생: " + err));
  }
}
