export default class UIManager {
  annotateType = null;
  toolManager = null;
  
  drawingBtn = null;
  drawingStatus = null;
  toolBtnGroup = null;
  eraserBtn = null;
  colorBtnGroup = null;
  
  currentStyleName = null;
  currentShapeName = null;
  
  constructor(annotateType, toolManager) {
    this.annotateType = annotateType;
    this.toolManager = toolManager;
    
    this.drawingBtn = this.getElement('DrawingBtn');
    this.drawingStatus = this.getElement('DrawingStatus');
    this.toolBtnGroup = this.getBtnGroup('tool-btn-group');
    this.eraserBtn = this.toolBtnGroup[0].querySelector(
      `button[data-annotation-style="eraser"]`);
    this.colorBtnGroup = this.getBtnGroup('color-btn-group');
  }
  
  getElement(suffix) {
    return document.getElementById(`${this.annotateType}${suffix}`);
  }
  
  getBtnGroup(suffix) {
    return document.querySelectorAll(`.${this.annotateType}-${suffix}`);
  }
  
  init() {
    this.drawingBtn.addEventListener(
      'click', () => this.handleDrawingBtnEvent());
    
    this.toolBtnGroup.forEach(group => {
      group.addEventListener('click', e => {
        const button = e.target.closest('button');
        this.handleToolBtnEvent(button);
      });
    });
    
    this.colorBtnGroup.forEach(group => {
      group.addEventListener('click', e => {
        const button = e.target.closest('button');
        this.handleColorBtnEvent(button);
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
  
  handleDrawingBtnEvent() {
    const drawingActive = this.drawingBtn.checked;
    if (drawingActive) return this.drawingStatus.classList.add('active');
    
    this.currentStyleName = this.currentShapeName = null;
    this.drawingStatus.classList.remove('active');
    this.deactivateToolBtns();
    
    if (this.toolManager.currentTool) this.toolManager.deactivateCurrentTool();
  }
  
  deactivateToolBtns() {
    this.toolBtnGroup.forEach(group => {
      const buttons = group.querySelectorAll('button');
      buttons.forEach(btn => btn.classList.remove('active'));
    });
  }
  
  handleToolBtnEvent(button) {
    if (!button) return;
    
    const isEraser = button.dataset.annotationStyle === 'eraser'
    if (isEraser) return this.toggleEraserBtn();
    
    const drawingIsActive = this.drawingBtn.classList.contains('active');
    if (!drawingIsActive) this.toggleDrawingBtn(true);
    
    const isStyle = button.dataset.annotationStyle !== undefined;
    const isShape = button.dataset.annotationShape !== undefined;
    
    const style = this.currentStyleName;
    const shape = this.currentShapeName;
    const firstClicked = !style && !shape
    const styleOrShapeClicked = (isStyle && style) || (isShape && shape)
    if (firstClicked || styleOrShapeClicked) this.handleClick(button);
  }
  
  toggleEraserBtn() {
    this.deactivateToolBtns();
    
    const eraseIsActive = this.eraserBtn.classList.contains('active');
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
  
  toggleDrawingBtn(active) {
    this.drawingBtn.checked = active;
    this.drawingStatus.classList.toggle('active', active);
    
    const changeEvent = new Event('change', {bubbles: true});
    this.drawingBtn.dispatchEvent(changeEvent);
    this.drawingStatus.dispatchEvent(changeEvent);
  }
  
  handleClick(button) {
    const selectedStyle = button.dataset.annotationStyle;
    const selectedShape = button.dataset.annotationShape;
    const style = this.currentStyleName;
    const shape = this.currentShapeName;
    const penBtn = this.getElement('PenBtn');
    const curveBtn = this.getElement('CurveBtn');
    
    if (selectedStyle) {
      if (!shape) {
        this.setActive(curveBtn);
        this.currentShapeName = 'curve';
      }
      this.setActive(button);
      this.currentStyleName = selectedStyle;
    }
    
    if (selectedShape) {
      if (!style) {
        this.setActive(penBtn);
        this.currentStyleName = 'pen';
      }
      this.setActive(button);
      this.currentShapeName = selectedShape;
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
  
  handleColorBtnEvent(button) {
    if (!button) return;
    this.setActive(button);
    
    const color = button.dataset.annotationColor;
    this.toolManager.setColor(color);
  }
}
