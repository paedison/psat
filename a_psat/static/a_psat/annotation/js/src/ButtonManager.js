export default class ButtonManager {
  #drawingContainer = null;
  #styleContainer = null;
  #shapeContainer = null;
  #colorContainer = null;

  constructor(annotateType) {
    this.annotateType = annotateType;

    this.btnContainer = this.getElement('BtnContainer');
    this.#drawingContainer = this.getContainer('drawing');
    this.#styleContainer = this.getContainer('style');
    this.#shapeContainer = this.getContainer('shape');
    this.#colorContainer = this.getContainer('color');
    
    this.drawingBtn = this.#drawingContainer.querySelector('input')
    this.drawingStatus = this.#drawingContainer.querySelector('.drawing-btn')
    this.drawing = {
      'btn': this.drawingBtn,
      'status': this.drawingStatus,
    }
    
    this.penBtn = this.getStyleButton('pen')
    this.highlighterBtn = this.getStyleButton('highlighter')
    this.eraserBtn = this.getStyleButton('eraser')
    this.styleGroup = {
      'pen': this.penBtn,
      'highlighter': this.highlighterBtn,
      'eraser': this.eraserBtn,
    }
    
    this.curveBtn = this.getShapeButton('curve')
    this.lineBtn = this.getShapeButton('line')
    this.shapeGroup = {
      'curve': this.curveBtn,
      'line': this.lineBtn,
    }
    
    this.blackBtn = this.getColorButton( 'black')
    this.redBtn = this.getColorButton( 'red')
    this.blueBtn = this.getColorButton( 'blue')
    this.greenBtn = this.getColorButton( 'green')
    this.yellowBtn = this.getColorButton( 'yellow')
    this.colorGroup = {
      'black': this.blackBtn,
      'red': this.redBtn,
      'blue': this.blueBtn,
      'green': this.greenBtn,
      'yellow': this.yellowBtn,
    }
  }

  getElement(suffix) {
    return document.getElementById(`${this.annotateType}${suffix}`);
  }

  getContainer(groupName) {
    return this.btnContainer.querySelector(`[data-annotate-container="${groupName}"]`);
  }

  getStyleButton(buttonName) {
    return this.#styleContainer.querySelector(`[data-annotate-style="${buttonName}"]`);
  }

  getShapeButton(buttonName) {
    return this.#shapeContainer.querySelector(`[data-annotate-shape="${buttonName}"]`);
  }

  getColorButton(buttonName) {
    return this.#colorContainer.querySelector(`[data-annotate-color="${buttonName}"]`);
  }
}

