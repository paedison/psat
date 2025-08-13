import {settings} from '../constants.js';
import {TextButton} from './interface.js';

class ResetGameButton extends TextButton {
  execute() {
    const cameras = this.scene.cameras;
    const scene = this.scene.scene;
    
    cameras.main.fadeOut(250, 255, 255, 255);
    cameras.main.once('camerafadeoutcomplete', () => {
      const mainScene = scene.get('MainScene');
      mainScene.restart();
      scene.resume('MainScene');
      scene.stop();
    });
  }
}

export default class GameOverScene extends Phaser.Scene {
  constructor() {
    super({key: 'GameOverScene'});
  }
  
  create(data) {
    const width = settings.window.WIDTH;
    const height = settings.window.HEIGHT;
    
    const {score} = data;
    
    this.add.rectangle(width / 2, height / 2, width, height, 0x000000, 0.5);
    
    const container = this.add.container(width / 2, height / 2);
    const bg = this.add.graphics().
      fillStyle(settings.window.BACKGROUND).
      fillRoundedRect(-width * 3 / 8, -height / 8, width * 3 / 4, height / 4, 10);
    
    // 텍스트 표시
    const titleText = this.add.text(0, -height / 16, '게임이 종료됐습니다.', {
      fontSize: '32px',
      fontFamily: 'Noto Sans KR',
      fontStyle: 'bold',
      color: '#000000',
    }).setOrigin(0.5);
    
    const scoreText = this.add.text(0, 0, `점수: ${score}`, {
      fontSize: '24px',
      fontFamily: 'Noto Sans KR',
      color: '#000000',
    }).setOrigin(0.5);
    
    const x = width * 3 / 8 - settings.button.WIDTH - 25;
    const y = height / 8 - settings.button.HEIGHT - 25;
    const resetButton = new ResetGameButton(this, y, {x: x, text: '새로 시작(R)'});
    
    container.add([bg, titleText, scoreText, resetButton]);
  }
}
