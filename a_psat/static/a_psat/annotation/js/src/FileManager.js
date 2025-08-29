export default class FileManager {
  constructor(scope) {
    this.scope = scope;
    this.canvas = scope.canvas;
    this.annotateUrl = scope.annotateUrl;
    this.annotateType = scope.annotateType;
  }

  saveAnnotation() {
    if (!confirm('현재 필기 내용을 저장하시겠습니까?')) return;
    if (!this.canvas) return alert('❌ 캔버스를 찾을 수 없습니다!');
    
    const csrfToken = document.querySelector(`input[name='csrfmiddlewaretoken']`)?.value;
    console.log(csrfToken)
    fetch(this.annotateUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({image: this.canvas.toDataURL('image/png')})
    })
      .then(res => res.json())
      .then(data => {
        if (!data.success) return alert("❌ 저장 실패: " + data.error);
        alert("✅ 필기 내용이 저장되었습니다!");
      })
      .catch(err => alert("❌ 저장 중 오류 발생: " + err));
  }

  loadAnnotation() {
    if (!this.canvas) return alert('❌ 캔버스를 찾을 수 없습니다!');
    if (!confirm("저장된 필기 이미지를 불러오시겠습니까?\n현재 필기 내용은 삭제됩니다.")) return;

    fetch(this.annotateUrl)
      .then(res => res.json())
      .then(data => {
        if (!data.success) return alert("저장된 필기 데이터가 없습니다.");
        
        const {image_url: source} = data;
        const raster = new this.scope.Raster({source: source, position: this.scope.view.center})
        raster.sendToBack();
        raster.on('load', () => raster.fitBounds(this.scope.view.bounds, true))
      })
      .catch(err => alert("❌ 불러오기 중 오류 발생: " + err));
  }
}
