import CurveTool from './tools/CurveTool.js';
import LineTool from './tools/LineTool.js';
import EraserTool from './tools/EraserTool.js';
import {COLORS} from './utils/ColorPalette.js';
import {constants} from './Constants.js';

export default class ToolManager {
  scope = null;
  currentTool = null;
  currentColor = `rgba(0, 0, 0, 0.4)`;
  
  constructor(scope) {
    this.scope = scope;
  }
  
  deactivateCurrentTool() {
    if (this.currentTool?.tool) this.currentTool.deactivate();
    this.currentTool = null;
  }
  
  setTool(styleName, shapeName) {
    const style = constants.writingStyle[styleName];
    
    if (styleName === 'highlighter') style['strokeWidth'] = this.scope.canvas.width / 100;
    
    if (styleName === 'eraser') this.currentTool = new EraserTool(this.scope, this.currentColor, style);
    if (shapeName === 'curve') this.currentTool = new CurveTool(this.scope, this.currentColor, style);
    if (shapeName === 'line') this.currentTool = new LineTool(this.scope, this.currentColor, style);
    
    this.currentTool.tool.activate();
  }
  
  setColor(colorName) {
    const rgb = COLORS[colorName] || COLORS.black;
    this.currentColor = `rgba(${rgb}, 0.4)`;
    if (this.currentTool?.updateColor) {
      this.currentTool.updateColor(this.currentColor);
    }
  }
}