import MainScene from './scenes/mainScene.js';
import GameOverScene from './scenes/gameOverScene.js';
import { settings } from './constants.js';

const config = {
  type: Phaser.AUTO,
  title: 'Boardgame SET',
  description: '',
  parent: 'game-container',
  width: settings.window.WIDTH,
  height: settings.window.HEIGHT,
  backgroundColor: settings.window.BACKGROUND,
  pixelArt: false,
  scene: [
    MainScene,
    GameOverScene,
  ],
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
  },
};

new Phaser.Game(config);
