import ButtonManager from "./ButtonManager.js";

export default class UIManager {
  constructor(annotateType, toolManager) {
    this.annotateType = annotateType;
    this.toolManager = toolManager;
    
    this.btnManager = new ButtonManager(annotateType);
    this.drawingBtn = this.btnManager.drawingBtn;
    this.drawingStatus = this.btnManager.drawing.status;
    this.styleBtnGroup = this.btnManager.styleGroup;
    this.shapeBtnGroup = this.btnManager.shapeGroup;
    this.eraserBtn = this.btnManager.styleGroup.eraser;
    this.colorBtnGroup = this.btnManager.colorGroup;
    
    this.previousStyleName = null;
    this.previousShapeName = null;
    this.previousColorName = null;
    
    this.currentStyleName = null;
    this.currentShapeName = null;
    this.currentColorName = null;
  }
  
  init() {
    // 필기 버튼
    this.drawingBtn.addEventListener('click', () => {
      this.drawingStatus.classList.toggle('active');
      if (!this.drawingBtn.checked) this.deactivateToolBtns();
    });
    
    // 툴 버튼(펜, 형광펜, 지우개, 곡선, 직선, 색상)
    const buttonGroups = {
      'Style': this.styleBtnGroup,
      'Shape': this.shapeBtnGroup,
      'Color': this.colorBtnGroup,
    };
    Object.entries(buttonGroups).forEach(([key, group]) => {
      Object.entries(group).forEach(([buttonName, btn]) => {
        btn.addEventListener('click', () => this.handleToolBtnEvent(key, buttonName, btn));
      });
    });

    // const btnName = ['Undo', 'Redo', 'Clear', 'Save', 'Load']
    // btnName.forEach(name => {
    //   document.getElementById(`${this.annotateType}${name}Btn`)?.addEventListener(
    //     'click', () => this.toolManager[name.toLowerCase()]());
    // });
    
    document.getElementById(`${this.annotateType}UndoBtn`)
      ?.addEventListener('click', () => this.toolManager.undo());
    document.getElementById(`${this.annotateType}RedoBtn`)
      ?.addEventListener('click', () => this.toolManager.redo());
    document.getElementById(`${this.annotateType}ClearBtn`)
      ?.addEventListener('click', () => this.toolManager.clear());
    document.getElementById(`${this.annotateType}SaveBtn`)
      ?.addEventListener('click', () => this.toolManager.save());
    document.getElementById(`${this.annotateType}LoadBtn`)
      ?.addEventListener('click', () => this.toolManager.load());
  }
  
  // 필기 상태에서 필기 버튼을 클릭하는 경우 -> 필기 버튼 및 필기 상태가 비활성화됨
  // 최초 로딩 후 툴 버튼을 클릭하는 경우 -> 필기 버튼은 자동으로 활성화됨
  deactivateToolBtns() {
    [this.styleBtnGroup, this.shapeBtnGroup, this.colorBtnGroup].forEach(group => {
      Object.values(group).forEach(btn => btn.classList.remove('active'));
    });
    this.currentStyleName = this.currentShapeName = this.currentColorName = null;
    if (this.toolManager.currentTool) this.toolManager.deactivateCurrentTool();
  }
  
  // 이벤트 설정: 지우개 버튼을 제외한 툴 버튼을 클릭하는 경우
  handleToolBtnEvent(type, buttonName, button) {
    if (!button || !type || !buttonName) return;
    
    const validTypes = new Set(['Style', 'Shape', 'Color']);
    if (!validTypes.has(type)) return console.warn(`Invalid type: ${type}`);
    
    // 기존 상태값에 현재 상태값을 입력
    this[`previous${type}Name`] = this[`current${type}Name`];
    
    // 필기 버튼이 비활성화되어 있으면 자동 활성화
    if (!this.drawingBtn.classList.contains('active')) {
      this.drawingBtn.checked = true;
      this.drawingStatus.classList.toggle('active', true);
    }
    
    // 지우개 버튼을 클릭할 경우 activateEraserBtn()으로 분기
    if (type === 'Style' && buttonName === 'eraser') return this.activateEraserBtn();
    
    // 지우개 버튼이 활성화된 상태에서 다른 버튼을 클릭하면 전체 툴 버튼을 비활성화함
    if (this.eraserBtn?.classList.contains('active')) this.deactivateToolBtns();
    
    // 현재 상태값을 입력받은 버튼 이름으로 변경
    this[`current${type}Name`] = buttonName;
    
    // 현재값이 null이 아닌 경우에만 현재값 그대로 다시 설정
    // 현재값이 null이면 이전값을, 이전값도 null이면 기본값으로 설정
    this.currentStyleName = this.currentStyleName || this.previousStyleName || 'pen'
    this.currentShapeName = this.currentShapeName || this.previousShapeName || 'curve'
    this.currentColorName = this.currentColorName || this.previousColorName || 'black'
    
    // 각각의 툴 버튼마다 그룹별로 버튼 활성화 및 비활성화 재설정
    // 각 그룹별로 현재 클릭한 버튼만 활성화되고 나머지는 비활성화됨
    // 지우개 버튼에는 적용되지 않으며 대신에 activateEraserBtn()가 적용됨
    const activeMap = {
      styleBtnGroup: this.currentStyleName,
      shapeBtnGroup: this.currentShapeName,
      colorBtnGroup: this.currentColorName
    };
    Object.entries(activeMap).forEach(([groupName, buttonName]) => {
      Object.entries(this[groupName]).forEach(([name, btn]) => {
        btn.classList.toggle('active', name === buttonName);
      });
    });
    
    this.initTool();
  }
  
  // 이벤트 설정: 지우개 버튼을 클릭하는 경우
  activateEraserBtn() {
    this.previousStyleName = this.currentStyleName;
    this.previousShapeName = this.currentShapeName;
    this.previousColorName = this.currentColorName;
    
    this.deactivateToolBtns();
    
    this.currentStyleName = 'eraser';
    this.currentShapeName = this.previousShapeName;
    this.currentColorName = this.previousColorName || 'black';
    this.eraserBtn.classList.add('active');
    this.initTool();
  }
  
  initTool() {
    this.toolManager.setTool(this.currentStyleName, this.currentShapeName);
    this.toolManager.setColor(this.currentColorName);
  }
  
  consoleTest() {
    console.log('---- test start ----')
    console.log('previousStyleName: ' + this.previousStyleName)
    console.log('previousShapeName: ' + this.previousShapeName)
    console.log('previousColorName: ' + this.previousColorName)
    console.log('currentStyleName: ' + this.currentStyleName)
    console.log('currentShapeName: ' + this.currentShapeName)
    console.log('currentColorName: ' + this.currentColorName)
  }
}
