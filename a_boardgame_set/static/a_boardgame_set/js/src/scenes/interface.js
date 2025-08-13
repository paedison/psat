/** @type {import('../types/phaser')} */

import {settings} from '../constants.js';

export class InformationBox extends Phaser.GameObjects.Container {
  constructor(scene, x, options = {}) {
    const y = 0;
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
      fontSize = '14px',
    } = this.options;
    
    this.labelBox = this.scene.add.graphics()
      .lineStyle(lineWidth, backgroundColor)
      .fillStyle(backgroundColor)
      .setAlpha(alpha)
      .fillRect(0, 0, width * 5 / 8, height)
      .strokeRect(0, 0, width * 5 / 8, height);
    
    this.dataBox = this.scene.add.graphics()
      .lineStyle(lineWidth, backgroundColor)
      .setAlpha(alpha)
      .strokeRect(width * 5 / 8, 0, width * 3 / 8, height);
    
    this.label = this.scene.add.text(width * 5 / 16, height / 2, labelText, {
      fontFamily: fontFamily,
      fontSize: fontSize,
      fontStyle: fontStyle,
      color: textColorLabel,
    }).setOrigin(0.5);
    
    this.data = this.scene.add.text(width * 13 / 16, height / 2, dataText, {
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

export class CardSprite extends Phaser.GameObjects.Image {
  atlasKey = settings.card.ATLAS_KEY;
  getFrameKey = settings.card.getFrameKey;
  
  cardWidth = settings.card.WIDTH;
  cardHeight = settings.card.HEIGHT;
  
  borderWidth = settings.card.BORDER_WIDTH;
  borderColor = settings.card.BORDER_COLOR_DEFAULT;
  borderColorDefault = settings.card.BORDER_COLOR_DEFAULT;
  borderColorSelected = settings.card.BORDER_COLOR_SELECTED;
  
  constructor(scene, index, card) {
    const {
      ATLAS_KEY, getFrameKey, WIDTH, HEIGHT, PADDING_X, PADDING_Y
    } = settings.card;
    const x = (index % 4) * (WIDTH + PADDING_X) - settings.textbox.BORDER_WIDTH
    const y = Math.floor(index / 4) * (HEIGHT + PADDING_Y)
    
    super(scene, x, y, ATLAS_KEY, getFrameKey(card));
    
    this.index = index;
    this.cardData = card;
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
    const {POSITION_X, POSITION_Y} = settings.card;
    border.lineStyle(this.borderWidth, color);
    border.strokeRect(POSITION_X + this.x, POSITION_Y + this.y, this.cardWidth, this.cardHeight);
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

export class CardThumbnailSprite extends Phaser.GameObjects.Image {
  atlasKey = settings.thumbnail.ATLAS_KEY;
  getFrameKey = settings.thumbnail.getFrameKey;
  
  cardWidth = settings.thumbnail.WIDTH;
  cardHeight = settings.thumbnail.HEIGHT;
  borderWidth = settings.thumbnail.BORDER_WIDTH;
  borderColor = settings.thumbnail.BORDER_COLOR;
  
  constructor(scene, index, card) {
    const {
      ATLAS_KEY, getFrameKey, WIDTH, MARGIN,
    } = settings.thumbnail;
    const x = index * (WIDTH + MARGIN);
    const y = settings.thumbnailText.HEIGHT + settings.thumbnailText.MARGIN;
    
    super(scene, x, y, ATLAS_KEY, getFrameKey(card));
    
    this.index = index;
    this.cardData = card;
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
    const {POSITION_X, POSITION_Y} = settings.thumbnailText;
    const border = this.scene.add.graphics();
    border.lineStyle(this.borderWidth, color);
    border.strokeRect(POSITION_X + this.x, POSITION_Y + this.y, this.cardWidth, this.cardHeight);
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
  buttonWidth = settings.button.WIDTH;
  buttonHeight = settings.button.HEIGHT;
  textColor = settings.button.TEXT_COLOR;
  alphaFill = 0.8;
  radius = 8;
  
  constructor(scene, x, y, options = {}) {
    super(scene, x, y);
    this.options = options;
    this.#draw();
  }
  
  #draw() {
    const {text, fillColor, textColor = this.textColor} = this.options;
    const width = this.buttonWidth;
    const height = this.buttonHeight;
    
    this.bg = this.scene.add.graphics()
      .fillStyle(fillColor)
      .setAlpha(this.alphaFill)
      .fillRoundedRect(-width / 2, -height / 2, width, height, this.radius);
    
    this.shadow = this.scene.add.graphics()
      .fillStyle(0x000000, 0.1)
      .fillRoundedRect(-width / 2 + 3, -height / 2 + 3, width, height, this.radius);
    
    this.label = this.scene.add.text(0, 0, text, {
      fontFamily: settings.window.FONT_FAMILY,
      fontSize: '18px',
      fontStyle: 'bold',
      color: textColor,
    }).setOrigin(0.5);
    
    this.add([this.shadow, this.bg, this.label]);
    this.#setInteractive();
  }
  
  #setInteractive() {
    const width = this.buttonWidth;
    const height = this.buttonHeight;
    
    this.setSize(width, height)
      .setInteractive(
        new Phaser.Geom.Rectangle(0, 0, width, height), // 히트 영역 정의
        Phaser.Geom.Rectangle.Contains,                 // 포인터가 영역 안에 있는지 판단하는 함수
      );
    this.input.cursor = 'pointer'; // 커서 손가락으로
    this.on('pointerover', () => this.#alphaEffect(1));
    this.on('pointerout', () => this.#alphaEffect(this.alphaFill));
    
    this.on('pointerup', () => {
      this.disableInteractive();
      this.scene.tweens.add({
        targets: this, duration: 100, yoyo: true,
        alpha: 0.5, scaleX: 0.95, scaleY: 0.95,
        onComplete: () => this.setInteractive(),
      });
      this.execute();
    });
    
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
    const {x = 0} = options;
    super(scene, x, y);
    
    this.options = options;
    this.#draw();
    this.#add();
    
    scene.add.existing(this);
  }
  
  #draw() {
    const {WIDTH, HEIGHT} = settings.button;
    
    const {
      text = '',
      width = WIDTH,
      height = HEIGHT,
      backgroundColor = settings.window.BACKGROUND,
      alpha = 0,
      textColor = '#000000',
      fontFamily = settings.window.FONT_FAMILY,
      fontSize = '18px',
      radius = 8,
    } = this.options;
    
    this.bg = this.scene.add.graphics()
      .fillStyle(backgroundColor)
      .setAlpha(alpha)
      .fillRoundedRect(0, 0, width, height, radius);
    
    this.label = this.scene.add.text(0, 0, text, {
      fontFamily: fontFamily,
      fontSize: fontSize,
      fontStyle: 'bold',
      color: textColor,
    });
  }
  
  #add() {
    this.add(this.bg);
    this.add(this.label);
    this.scene.add.existing(this);
  }
}
