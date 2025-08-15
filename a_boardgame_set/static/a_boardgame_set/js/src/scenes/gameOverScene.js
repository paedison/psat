import {settings} from '../constants.js';
import {ResetGameButton} from './buttons.js';

export default class GameOverScene extends Phaser.Scene {
  constructor() {
    super({key: 'GameOverScene'});
  }
  
  create(data) {
    // 상수 설정
    const
      width = this.game.config.width + 0,
      height = this.game.config.height + 0,
      
      {
        WIDTH: buttonWidth, HEIGHT: buttonHeight,
        FILL_RESTART, FONT_FAMILY,
      } = settings.button,
      
      {score} = data,
      
      titleStyle = {
        fontSize: '32px',
        fontFamily: FONT_FAMILY,
        fontStyle: 'bold',
        color: '#000000',
      },
      scoreStyle = {...titleStyle};
    
    scoreStyle.fontSize = '24px';
    scoreStyle.fontStyle = 'normal';
    
    // 그래픽 그리기
    const
      overlay = this.add.rectangle(
        0, 0, width, height, 0x000000, 0.5),
      bg = this.add.graphics()
        .fillStyle(this.game.config.backgroundColor.color)
        .fillRoundedRect(
          -width * 3 / 8, -height / 8,
          width * 3 / 4, height / 4, 10),
      titleText = this.add
        .text(0, -height / 16, '게임이 종료됐습니다.', titleStyle)
        .setOrigin(0.5),
      scoreText = this.add
        .text(0, 0, `점수: ${score}`, scoreStyle).setOrigin(0.5),
      
      x = width * 3 / 8 - buttonWidth / 2 - 25,
      y = height / 8 - buttonHeight / 2 - 25,
      resetButton = new ResetGameButton(this, x, y, {
        text: '새로 시작(R)',
        fillColor: FILL_RESTART,
      });
    
    this.add.container(width / 2, height / 2, [
      overlay, bg, titleText, scoreText, resetButton
    ]);
  }
}
