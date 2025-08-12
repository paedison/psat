/** @type {import('../types/phaser')} */

import {settings} from '../constants.js';

function getCardConstants(index, card) {
  const {
    ATLAS_KEY, getFrameKey,
    WIDTH, HEIGHT, MARGIN,
  } = settings.card;
  const x_margin = settings.window.MARGIN_X + settings.button.WIDTH + MARGIN;
  
  return {
    atlasKey: ATLAS_KEY, frameKey: getFrameKey(card), getFrameKey: getFrameKey,
    cardWidth: WIDTH, cardHeight: HEIGHT,
    x: x_margin + (index % 4) * (WIDTH + MARGIN),
    y: settings.window.MARGIN_Y + Math.floor(index / 4) * (HEIGHT + MARGIN),
  };
}

export class CardSprite extends Phaser.GameObjects.Image {
  constructor(scene, index, card) {
    const {
      atlasKey, frameKey, getFrameKey,
      cardWidth, cardHeight, x, y,
    } = getCardConstants(index, card);
    
    super(scene, x, y, atlasKey, frameKey);
    
    this.index = index;
    this.cardData = card;
    this.atlasKey = atlasKey;
    this.getFrameKey = getFrameKey;
    this.cardWidth = cardWidth;
    this.cardHeight = cardHeight;
    
    const {
      BORDER_WIDTH, BORDER_COLOR_DEFAULT, BORDER_COLOR_SELECTED,
    } = settings.card;
    
    this.borderWidth = BORDER_WIDTH;
    this.borderColor = BORDER_COLOR_DEFAULT;
    this.borderColorDefault = BORDER_COLOR_DEFAULT;
    this.borderColorSelected = BORDER_COLOR_SELECTED;
    this.selected = false;
    
    scene.add.existing(this);
  }
  
  setup() {
    this.setOrigin(0, 0)
      .setInteractive()
      .setPosition(this.x + this.borderWidth / 2, this.y + this.borderWidth / 2)
      .setDisplaySize(this.cardWidth - this.borderWidth,
        this.cardHeight - this.borderWidth);
    this.input.cursor = 'pointer';
    this.border = this.drawBorder(this.borderColor);
    return this;
  }
  
  toggleSelect() {
    this.selected = !this.selected;
    this.selected
      ? this.updateBorder(this.borderColorSelected)
      : this.updateBorder(this.borderColorDefault);
  }
  
  checkBorder() {
    this.selected
      ? this.drawBorder(this.borderColorSelected)
      : this.drawBorder(this.borderColorDefault);
  }
  
  drawBorder(color) {
    if (this.border) this.border.destroy(); // Clean up old border
    const border = this.scene.add.graphics();
    border.lineStyle(this.borderWidth, color);
    border.strokeRect(this.x, this.y, this.cardWidth, this.cardHeight);
    return border;
  }
  
  updateBorder(finalColor) {
    const duration = 100;
    const ease = 'Poser2';
    if (finalColor !== this.borderColor) {
      this.scene.tweens.add({
        targets: this.border, alpha: 0, duration: duration, ease: ease,
        onComplete: () => {
          this.border.clear();
          this.border = this.drawBorder(finalColor).setAlpha(0);
          this.borderColor = finalColor;
          this.scene.tweens.add({
            targets: this.border, alpha: 1, duration: duration, ease: ease,
          });
        },
      });
    }
  }
  
  deselect() {
    this.selected = false;
    this.updateBorder(this.borderColorDefault);
  }
  
  replaceCard(newCard) {
    const frameKey = this.getFrameKey(newCard);
    this.deselect();
    settings.fadeOutAnimation(
      this.scene, this, (cs) => cs.setTexture(this.atlasKey, frameKey));
    this.cardData = newCard;
    this.setInteractive();
  }
  
  removeCard() {
    this.deselect();
    settings.fadeOutAnimation(
      this.scene, this, (cs) => cs.setTexture('__WHITE'));
    this.disableInteractive();
  }
}

function getThumbnailConstants(index, card) {
  const {
    ATLAS_KEY, getFrameKey,
    WIDTH, HEIGHT, MARGIN,
  } = settings.thumbnail;
  
  return {
    atlasKey: ATLAS_KEY, frameKey: getFrameKey(card), getFrameKey: getFrameKey,
    cardWidth: WIDTH, cardHeight: HEIGHT,
    x: settings.window.MARGIN_X + index * (WIDTH + MARGIN),
    y: settings.window.HEIGHT - settings.window.MARGIN_Y - HEIGHT - 2 *
      settings.card.BORDER_WIDTH,
  };
}

export class CardThumbnailSprite extends Phaser.GameObjects.Image {
  constructor(scene, index, card) {
    const {
      atlasKey, frameKey, getFrameKey,
      cardWidth, cardHeight, x, y,
    } = getThumbnailConstants(index, card);
    
    super(scene, x, y, atlasKey, frameKey);
    
    this.index = index;
    this.cardData = card;
    this.atlasKey = atlasKey;
    this.getFrameKey = getFrameKey;
    this.cardWidth = cardWidth;
    this.cardHeight = cardHeight;
    
    const {BORDER_COLOR, BORDER_WIDTH} = settings.thumbnail;
    
    this.borderColor = BORDER_COLOR;
    this.borderWidth = BORDER_WIDTH;
    this.selected = false;
    
    scene.add.existing(this);
  }
  
  setup() {
    this.setOrigin(0, 0)
      .setPosition(this.x + this.borderWidth / 2, this.y + this.borderWidth / 2)
      .setDisplaySize(this.cardWidth - this.borderWidth,
        this.cardHeight - this.borderWidth);
    this.border = this.drawBorder(this.borderColor);
    return this;
  }
  
  drawBorder(color) {
    if (this.border) this.border.destroy(); // Clean up old border
    const border = this.scene.add.graphics();
    border.lineStyle(this.borderWidth, color);
    border.strokeRect(this.x, this.y, this.cardWidth, this.cardHeight);
    return border;
  }
  
  replaceCard(newCard) {
    const frameKey = this.getFrameKey(newCard);
    settings.fadeOutAnimation(
      this.scene, this, (cs) => cs.setTexture(this.atlasKey, frameKey));
    this.cardData = newCard;
  }
}

export class TextButton extends Phaser.GameObjects.Container {
  constructor(scene, y, options = {}) {
    const {x = settings.window.MARGIN_X} = options;
    super(scene, x, y);
    
    this.options = options;
    this.#draw();
    this.#hooverEffect();
    this.#add();
    
    scene.add.existing(this);
  }
  
  #draw() {
    const {
      WIDTH, HEIGHT, TEXT_COLOR, BACKGROUND_RESTART,
    } = settings.button;
    
    const {
      text = '',
      width = WIDTH,
      height = HEIGHT,
      backgroundColor = BACKGROUND_RESTART,
      alpha = 0.8,
      textColor = TEXT_COLOR,
      fontFamily = settings.window.FONT_FAMILY,
      fontStyle = 'bold',
      fontSize = '20px',
      radius = 8,
    } = this.options;
    
    this.bg = this.scene.add.graphics()
      .fillStyle(backgroundColor)
      .setAlpha(alpha)
      .fillRoundedRect(0, 0, width, height, radius)
      .setInteractive(
        new Phaser.Geom.Rectangle(0, 0, width, height), // 히트 영역 정의
        Phaser.Geom.Rectangle.Contains,                 // 포인터가 영역 안에 있는지 판단하는 함수
      );
    
    // 텍스트
    this.label = this.scene.add.text(width / 2, height / 2, text, {
      fontFamily: fontFamily,
      fontSize: fontSize,
      fontStyle: fontStyle,
      color: textColor,
    }).setOrigin(0.5);
  }
  
  #hooverEffect() {
    const {alpha = 0.8} = this.options;
    this.bg.input.cursor = 'pointer'; // 커서 손가락으로
    this.bg.on('pointerover', () => this.#alphaEffect(1));
    this.bg.on('pointerout', () => this.#alphaEffect(alpha));
    
    this.bg.on('pointerup', () => {
      this.bg.disableInteractive();
      this.scene.tweens.add({
        targets: this.bg, alpha: 0.5, duration: 100, yoyo: true,
        onComplete: () => this.bg.setInteractive(),
      });
      this.execute();
    });
  }
  
  #add() {
    this.add(this.bg);
    this.add(this.label);
    this.scene.add.existing(this);
  }
  
  #alphaEffect(alpha) {
    this.scene.tweens.add(
      {targets: this.bg, alpha: alpha, duration: 100, ease: 'Power2'});
  }
  
  execute() {
    throw new Error('execute() must be implemented by subclass');
  }
}

export class TextBox extends Phaser.GameObjects.Container {
  constructor(scene, y, options = {}) {
    const {x = settings.window.MARGIN_X} = options;
    super(scene, x, y);
    
    this.options = options;
    this.#draw();
    this.#add();
    
    scene.add.existing(this);
  }
  
  #draw() {
    const {WIDTH, HEIGHT, TEXT_COLOR} = settings.textbox;
    
    const {
      text = '',
      width = WIDTH,
      height = HEIGHT,
      backgroundColor = settings.window.BACKGROUND,
      alpha = 0,
      textColor = TEXT_COLOR,
      fontFamily = settings.window.FONT_FAMILY,
      fontSize = '18px',
      radius = 8,
    } = this.options;
    
    this.bg = this.scene.add.graphics()
      .fillStyle(backgroundColor)
      .setAlpha(alpha)
      .fillRoundedRect(0, 0, width, height, radius);
    
    this.label = this.scene.add.text(width / 2, height / 2, text, {
      fontFamily: fontFamily,
      fontSize: fontSize,
      fontStyle: 'bold',
      color: textColor,
    }).setOrigin(0.5);
  }
  
  #add() {
    this.add(this.bg);
    this.add(this.label);
    this.scene.add.existing(this);
  }
}

export class InformationBox extends Phaser.GameObjects.Container {
  constructor(scene, y, options = {}) {
    const {x = settings.window.MARGIN_X} = options;
    super(scene, x, y);
    
    this.options = options;
    this.#draw();
    this.#add();
    
    scene.add.existing(this);
  }
  
  #draw() {
    const {
      WIDTH, HEIGHT,
      BORDER_WIDTH, BACKGROUND_COLOR,
      TEXT_COLOR_LABEL, TEXT_COLOR_DATA,
    } = settings.textbox;
    
    const {
      labelText = '',
      dataText = '',
      width = WIDTH,
      height = HEIGHT,
      lineWidth = BORDER_WIDTH,
      backgroundColor = BACKGROUND_COLOR,
      alpha = 1,
      textColorLabel = TEXT_COLOR_LABEL,
      textColorData = TEXT_COLOR_DATA,
      fontFamily = settings.window.FONT_FAMILY,
      fontStyle = 'bold',
      fontSize = '18px',
    } = this.options;
    
    this.labelBox = this.scene.add.graphics()
      .lineStyle(lineWidth, backgroundColor)
      .fillStyle(backgroundColor)
      .setAlpha(alpha)
      .fillRect(0, 0, width / 2, height)
      .strokeRect(0, 0, width / 2, height);
    
    this.dataBox = this.scene.add.graphics()
      .lineStyle(lineWidth, backgroundColor)
      .setAlpha(alpha)
      .strokeRect(width / 2, 0, width / 2, height);
    
    this.label = this.scene.add.text(width / 4, height / 2, labelText, {
      fontFamily: fontFamily,
      fontSize: fontSize,
      fontStyle: fontStyle,
      color: textColorLabel,
    }).setOrigin(0.5);
    
    this.data = this.scene.add.text(width * 3 / 4, height / 2, dataText, {
      fontFamily: fontFamily,
      fontSize: fontSize,
      fontStyle: 'normal',
      color: textColorData,
    }).setOrigin(0.5);
  }
  
  #add() {
    this.add(this.labelBox);
    this.add(this.dataBox);
    this.add(this.label);
    this.add(this.data);
    this.scene.add.existing(this);
  }
}
