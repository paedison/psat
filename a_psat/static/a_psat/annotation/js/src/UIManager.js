export default class UIManager {
  annotateType = null;
  toolManager = null;
  
  drawingBtn = null;
  drawingStatus = null;
  eraserBtn = null;
  colorBtns = null;

  toolBtnGroup = document.querySelectorAll('.tool-btn-group');
  toolBtns = document.querySelectorAll('.tool-btn');

  currentStyleName = null;
  currentShapeName = null;

  constructor(annotateType, toolManager) {
    this.annotateType = annotateType;
    this.toolManager = toolManager;

    this.drawingBtn = this.getElement('DrawingBtn');
    this.drawingStatus = this.getElement('DrawingStatus');
    this.eraserBtn = this.getElement('EraserBtn');
    this.colorBtns = document.querySelectorAll(`.${this.annotateType}-color-btn`);
  }
  
  getElement(suffix) {
    return document.getElementById(`${this.annotateType}${suffix}`);
  }
  
  init() {
    this.drawingBtn.addEventListener('click', () => this.toggleDrawingStatus());
    
    this.toolBtnGroup.forEach(group => {
      group.addEventListener('click', e => {
        const button = e.target.closest('button');
        this.handleToolButtonGroupEvent(button);
      });
    });
    
    this.eraserBtn.addEventListener('click', () => this.toggleEraserBtn());
    
    this.colorBtns.forEach(btn => {
      btn.addEventListener('click', e => {
        this.colorBtns.forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const color = e.currentTarget.dataset.color;
        this.toolManager.setColor(color);
      });
    });
    
    // const btnName = ['Undo', 'Redo', 'Clear', 'Save', 'Load']
    // btnName.forEach(name => {
    //   document.getElementById(`${this.annotateType}${name}Btn`)?.addEventListener(
    //     'click', () => this.toolManager[name.toLowerCase()]());
    // });
    
    document.getElementById(`${this.annotateType}UndoBtn`)?.addEventListener('click', () => this.toolManager.undo());
    document.getElementById(`${this.annotateType}RedoBtn`)?.addEventListener('click', () => this.toolManager.redo());
    document.getElementById(`${this.annotateType}ClearBtn`)?.addEventListener('click', () => this.toolManager.clear());
    document.getElementById(`${this.annotateType}SaveBtn`)?.addEventListener('click', () => this.toolManager.save());
    document.getElementById(`${this.annotateType}LoadBtn`)?.addEventListener('click', () => this.toolManager.load());
  }
  
  toggleDrawingStatus() {
    if (this.drawingBtn.checked) {
      this.drawingStatus.classList.add('active');
    } else {
      this.drawingStatus.classList.remove('active');
      this.currentStyleName = this.currentShapeName = null;
      this.toolBtns.forEach(btn => btn.classList.remove('active'));
      if (this.toolManager.currentTool) this.toolManager.deactivateCurrentTool();
    }
  }
  
  handleToolButtonGroupEvent(button) {
    if (!button) return;
    
    const drawingIsActive = this.drawingBtn.classList.contains('active');
    if (!drawingIsActive) this.toggleDrawingBtn(true);
    
    const isStyle = button.dataset.annotationStyle !== undefined;
    const isShape = button.dataset.annotationShape !== undefined;
    
    if ((isStyle && this.currentStyleName) || (isShape && this.currentShapeName)) this.handleClick(button);
    
    if (!this.currentStyleName && !this.currentShapeName) this.handleClick(button);
  }
  
  toggleDrawingBtn(active) {
    this.drawingBtn.checked = active;
    this.drawingStatus.classList.toggle('active', active);
    
    const changeEvent = new Event('change', {bubbles: true});
    this.drawingBtn.dispatchEvent(changeEvent);
    this.drawingStatus.dispatchEvent(changeEvent);
  }
  
  handleClick(button) {
    const style = button.dataset.annotationStyle;
    const shape = button.dataset.annotationShape;
    const curveBtn = this.getElement('CurveBtn');
    console.log(this.currentStyleName, this.currentShapeName)
    if (style) {
      if (!this.currentStyleName && !this.currentShapeName) {
        this.setActive(curveBtn);
        this.currentShapeName = 'curve';
      }
      if (this.currentStyleName && !this.currentShapeName) {
        this.setActive(curveBtn);
        this.currentShapeName = 'curve';
      }
      this.setActive(button);
      this.currentStyleName = style;
    }
    
    if (shape) {
      if (!this.currentShapeName && !this.currentStyleName) {
        const penBtn = this.getElement('PenBtn');
        this.setActive(penBtn);
        this.currentStyleName = 'pen';
      }
      this.setActive(button);
      this.currentShapeName = shape;
    }
    
    this.toolManager.setTool(this.currentStyleName, this.currentShapeName);
  }
  
  setActive(button) {
    const group = button.parentElement;
    const buttons = group.querySelectorAll('button');
    
    buttons.forEach(btn => {
      btn.classList.toggle('active', btn === button);
    });
  }
  
  toggleEraserBtn() {
    const eraseIsActive = this.eraserBtn.classList.contains('active');
    this.toolBtns.forEach(btn => btn.classList.remove('active'));
    
    if (eraseIsActive) {
      this.currentStyleName = this.currentShapeName = null;
      this.eraserBtn.classList.remove('active');
    } else {
      this.currentStyleName = 'eraser';
      this.currentShapeName = null;
      this.eraserBtn.classList.add('active');
      this.toolManager.setTool(this.currentStyleName, this.currentShapeName);
    }
  }
}
