class ButtonObjects {
  #toolGroup = null;
  #colorGroup = null;

  constructor(annotateType) {
    this.annotateType = annotateType;

    this.btnContainer = this.getElement('BtnContainer');
    this.drawingGroup = this.getGroup('drawing');
    this.#toolGroup = this.getGroup('tool');
    this.#colorGroup = this.getGroup('color');

    this.drawing = {
      'btn': this.drawingGroup.querySelector('input'),
      'status': this.drawingGroup.querySelector('span'),
    }
    this.style = {
      'pen': this.getStyleButton('pen'),
      'highlighter': this.getStyleButton('highlighter'),
      'eraser': this.getStyleButton('eraser'),
    }
    this.shape = {
      'curve': this.getShapeButton('curve'),
      'line': this.getShapeButton('line'),
    }
    this.color = {
      'black': this.getColorButton( 'black'),
      'red': this.getColorButton( 'red'),
      'blue': this.getColorButton( 'blue'),
      'green': this.getColorButton( 'green'),
      'yellow': this.getColorButton( 'yellow'),
    }
  }

  getElement(suffix) {
    return document.getElementById(`${this.annotateType}${suffix}`);
  }

  getGroup(groupName) {
    return this.btnContainer.querySelector(`[data-annotate-group="${groupName}"]`);
  }

  getStyleButton(buttonName) {
    return this.#toolGroup.querySelector(`[data-annotate-style="${buttonName}"]`);
  }

  getShapeButton(buttonName) {
    return this.#toolGroup.querySelector(`[data-annotate-shape="${buttonName}"]`);
  }

  getColorButton(buttonName) {
    return this.#colorGroup.querySelector(`[data-annotate-color="${buttonName}"]`);
  }
}

export default class UIManager {
  annotateType = null;
  toolManager = null;

  // btnObjects = null;
  drawingBtn = null;
  drawingStatus = null;
  toolBtnGroup = null;
  eraserBtn = null;
  colorBtnGroup = null;

  currentStyleName = null;
  currentShapeName = null;
  currentColorName = null;
  
  constructor(annotateType, toolManager) {
    this.annotateType = annotateType;
    this.toolManager = toolManager;

    // this.btnObjects = new ButtonObjects(annotateType);
    // this.drawingBtn = this.btnObjects.drawing.btn;
    // this.drawingStatus = this.btnObjects.drawing.status;
    // this.toolBtnGroup = this.btnObjects.toolGroup;
    // this.eraserBtn = this.btnObjects.style.eraser;
    // this.colorBtnGroup = this.toolBtnGroup.colorGroup;

    this.drawingBtn = this.getElement('DrawingBtn');
    this.drawingStatus = this.getElement('DrawingStatus');
    this.toolBtnGroup = this.getBtnGroup('tool-btn-group');
    this.eraserBtn = this.toolBtnGroup[0].querySelector(
      `button[data-annotate-style="eraser"]`);
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
    this.drawingStatus.classList.toggle('active');
    if (!this.drawingBtn.checked) this.deactivateToolBtns();
  }
  
  deactivateToolBtns() {
    this.toolBtnGroup.forEach(group => {
      const buttons = group.querySelectorAll('button');
      buttons.forEach(btn => btn.classList.remove('active'));
    });
    this.currentStyleName = this.currentShapeName = null;
    if (this.toolManager.currentTool) this.toolManager.deactivateCurrentTool();
  }
  
  handleToolBtnEvent(button) {
    if (!button) return;
    
    const isEraser = button.dataset.annotateStyle === 'eraser'
    if (isEraser) return this.activateEraserBtn();
    
    const drawingActive = this.drawingBtn.classList.contains('active');
    if (!drawingActive) this.toggleDrawingBtn(true);
    
    const isStyle = button.dataset.annotateStyle !== undefined;
    const isShape = button.dataset.annotateShape !== undefined;
    
    const style = this.currentStyleName;
    const shape = this.currentShapeName;
    const firstClicked = !style && !shape
    const styleOrShapeClicked = (isStyle && style) || (isShape && shape)
    if (firstClicked || styleOrShapeClicked) this.handleClick(button);
  }
  
  activateEraserBtn() {
    this.deactivateToolBtns();
    this.toggleDrawingBtn(true);

    this.currentStyleName = 'eraser';
    this.eraserBtn.classList.add('active');
    this.toolManager.setTool(this.currentStyleName, this.currentShapeName);
  }
  
  toggleDrawingBtn(active) {
    this.drawingBtn.checked = active;
    this.drawingStatus.classList.toggle('active', active);
  }
  
  handleClick(button) {
    const selectedStyle = button.dataset.annotateStyle;
    const selectedShape = button.dataset.annotateShape;
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
    
    const color = button.dataset.annotateColor;
    this.currentColorName = color;
    this.toolManager.setColor(color);
  }
}
