import CurveTool from './tools/CurveTool.js';
import LineTool from './tools/LineTool.js';
import EraserTool from './tools/EraserTool.js';
import {colorToRgba} from './utils/ColorPalette.js';
import {constants} from './Constants.js';

export default class ToolManager {
  constructor(scope) {
    this.scope = scope;
    this.btnManager = scope.btnManager;
    this.historyManager = scope.historyManager;
    this.currentTool = null;
    this.currentColor = null;
  }
  
  deactivateCurrentTool() {
    if (this.currentTool?.tool) this.currentTool.deactivate();
    this.currentTool = null;
  }
  
  setTool(styleName, shapeName, colorName) {
    const style = constants.writingStyle[styleName];
    
    this.currentColor = colorToRgba(colorName, style.alpha);
    if (this.currentTool) this.currentTool.updateColor(this.currentColor);
    
    if (styleName === 'highlighter') style['strokeWidth'] = style['emphasizeStrokeWidth'] = this.scope.canvas.width / 100;
    
    if (styleName === 'eraser') this.currentTool = new EraserTool(this.scope, this.currentColor, style);
    else {
      if (shapeName === 'curve') this.currentTool = new CurveTool(this.scope, this.currentColor, style);
      if (shapeName === 'line') this.currentTool = new LineTool(this.scope, this.currentColor, style);
    }
    this.currentTool.tool.activate();
  }
}
