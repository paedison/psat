export default class ButtonManager {
  #drawingContainer = null;
  #styleContainer = null;
  #shapeContainer = null;
  #colorContainer = null;
  #actionContainer = null;

  constructor(scope) {
    this.scope = scope
    this.annotateType = scope.annotateType;

    this.btnContainer = this.getElement('BtnContainer');
    this.#drawingContainer = this.getContainer('drawing');
    this.#styleContainer = this.getContainer('style');
    this.#shapeContainer = this.getContainer('shape');
    this.#colorContainer = this.getContainer('color');
    this.#actionContainer = this.getContainer('action');
    
    this.drawingBtn = this.#drawingContainer.querySelector('input')
    this.drawingStatus = this.#drawingContainer.querySelector('.drawing-btn')
    this.drawing = {
      'btn': this.drawingBtn,
      'status': this.drawingStatus,
    }
    
    this.penBtn = this.getButton('style', 'pen')
    this.highlighterBtn = this.getButton('style', 'highlighter')
    this.eraserBtn = this.getButton('style', 'eraser')
    this.styleGroup = {
      'pen': this.penBtn,
      'highlighter': this.highlighterBtn,
      'eraser': this.eraserBtn,
    }
    
    this.curveBtn = this.getButton('shape', 'curve')
    this.lineBtn = this.getButton('shape', 'line')
    this.shapeGroup = {
      'curve': this.curveBtn,
      'line': this.lineBtn,
    }
    
    this.blackBtn = this.getButton('color',  'black')
    this.redBtn = this.getButton('color',  'red')
    this.blueBtn = this.getButton('color',  'blue')
    this.greenBtn = this.getButton('color',  'green')
    this.yellowBtn = this.getButton('color',  'yellow')
    this.colorGroup = {
      'black': this.blackBtn,
      'red': this.redBtn,
      'blue': this.blueBtn,
      'green': this.greenBtn,
      'yellow': this.yellowBtn,
    }
    
    this.undoBtn = this.getButton('action', 'undo')
    this.redoBtn = this.getButton('action', 'redo')
    this.loadBtn = this.getButton('action', 'load')
    this.saveBtn = this.getButton('action', 'save')
    this.clearBtn = this.getButton('action', 'clear')
    this.actionGroup = {
      'undo': this.undoBtn,
      'redo': this.redoBtn,
      'load': this.loadBtn,
      'save': this.saveBtn,
      'clear': this.clearBtn,
    }
  }

  getElement(suffix) {
    return document.getElementById(`${this.annotateType}${suffix}`);
  }

  getContainer(groupName) {
    return this.btnContainer.querySelector(`[data-annotate-container="${groupName}"]`);
  }
  
  getButton(type, buttonName) {
    const buttonMap = {
      style: {container: this.#styleContainer, attribute: 'data-annotate-style'},
      shape: {container: this.#shapeContainer, attribute: 'data-annotate-shape'},
      color: {container: this.#colorContainer, attribute: 'data-annotate-color'},
      action: {container: this.#actionContainer, attribute: 'data-annotate-action'},
    }
    const {container, attribute} = buttonMap[type];
    
    return container?.querySelector(`[${attribute}="${buttonName}"]`);
  }
}

