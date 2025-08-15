/** @type {import('../types/phaser')} */

import {settings} from '../constants.js';

export class InformationBox extends Phaser.GameObjects.Container {
  #options = {};
  #labelBox = null;
  #dataBox = null;
  #label = null;
  dataValue = null;
  
  constructor(scene, x, y = 0, options = {}) {
    super(scene, x, y);
    
    this.#options = options;
    this.#draw();
    
    this.add([this.#labelBox, this.#dataBox, this.#label, this.dataValue]);
    scene.add.existing(this);
  }
  
  #draw() {
    const
      {
        WIDTH, HEIGHT,
        BORDER_WIDTH, BACKGROUND_COLOR,
        TEXT_COLOR_LABEL, TEXT_COLOR_DATA,
      } = settings.textbox,
      
      {
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
      } = this.#options,
      
      styleLabel = {
        fontFamily: fontFamily,
        fontSize: fontSize,
        fontStyle: fontStyle,
        color: textColorLabel,
      },
      styleData = {...styleLabel};
    
    styleData.color = textColorData;
    styleData.fontStyle = 'normal';
    
    this.#labelBox = this.scene.add.graphics()
      .lineStyle(lineWidth, backgroundColor)
      .fillStyle(backgroundColor)
      .setAlpha(alpha)
      .fillRect(0, 0, width * 5 / 8, height)
      .strokeRect(0, 0, width * 5 / 8, height);
    
    this.#dataBox = this.scene.add.graphics()
      .lineStyle(lineWidth, backgroundColor)
      .setAlpha(alpha)
      .strokeRect(0, 0, width, height);
    
    this.#label = this.scene.add
      .text(width * 5 / 16, height / 2, labelText, styleLabel)
      .setOrigin(0.5);
    
    this.dataValue = this.scene.add
      .text(width * 13 / 16, height / 2, dataText, styleData)
      .setOrigin(0.5);
  }
}

function alphaEffect(scene, targets, alpha) {
  scene.tweens.add({
    targets: targets, alpha: alpha, duration: 100, ease: 'Power2',
  });
}

function setInteractiveAndPointerOverOut(container) {
  container.setInteractive(
    new Phaser.Geom.Rectangle(0, 0, container.width, container.height),
    Phaser.Geom.Rectangle.Contains,
  );
  container.input.cursor = 'pointer'; // 커서 손가락으로
}

function drawBorder(container, borderWidth, color) {
  return container.scene.add.graphics()
    .lineStyle(borderWidth, color)
    .strokeRect(
      -container.width / 2, -container.height / 2,
      container.width, container.height,
    );
}

export class CardSprite extends Phaser.GameObjects.Container {
  width = settings.card.WIDTH;
  height = settings.card.HEIGHT;
  
  #borderWidth = settings.card.BORDER_WIDTH;
  #borderColor = settings.card.BORDER_COLOR_DEFAULT;
  #borderColorDefault = settings.card.BORDER_COLOR_DEFAULT;
  #borderColorSelected = settings.card.BORDER_COLOR_SELECTED;
  
  #card = null;
  #selectionCover = null;
  #border = null;
  #alphaDefault = 0;
  #alphaSelected = 0.05;
  
  index = null;
  cardData = null;
  selected = false;
  
  constructor(scene, index, card) {
    const
      {
        ATLAS_KEY, getFrameKey, WIDTH, HEIGHT,
        PADDING_X, PADDING_Y, BORDER_WIDTH,
      } = settings.card,
      
      x = WIDTH / 2 + (index % 4) * (WIDTH + PADDING_X) -
        settings.textbox.BORDER_WIDTH,
      y = HEIGHT / 2 +
        Math.floor(index / 4) * (HEIGHT + PADDING_Y);
    super(scene, x, y);
    
    this.#setInteractive();
    
    this.#card = scene.add.image(0, 0, ATLAS_KEY, getFrameKey(card))
      .setDisplaySize(WIDTH - BORDER_WIDTH, HEIGHT - BORDER_WIDTH);
    this.#drawSelectionCover();
    this.#drawBorder(this.#borderColor);
    
    this.add([this.#card, this.#selectionCover, this.#border]);
    scene.add.existing(this);
    
    this.index = index;
    this.cardData = card;
  }
  
  #setInteractive() {
    setInteractiveAndPointerOverOut(this);
    this.on('pointerover', () => this.#alphaEffect(this.#alphaSelected));
    this.on('pointerout', () => this.#alphaEffect(this.#alphaDefault));
    
    this.on('pointerup', () => {
      this.disableInteractive();
      this.scene.tweens.add({
        targets: this, duration: 100, yoyo: true,
        alpha: 0.5, scaleX: 0.95, scaleY: 0.95,
        onComplete: () => this.setInteractive(),
      });
    });
  }
  
  #alphaEffect(alpha) {
    if (!this.selected) {
      alphaEffect(this.scene, this.#selectionCover, alpha);
    }
  }
  
  #drawSelectionCover() {
    this.#selectionCover = this.scene.add.graphics()
      .fillStyle(0x000000)
      .setAlpha(this.#alphaDefault)
      .fillRect(-this.width / 2, -this.height / 2, this.width, this.height);
    
  }
  
  #drawBorder(color) {
    if (this.#border) this.#border.destroy(); // Clean up old border
    this.#border = drawBorder(this, this.#borderWidth, color);
    this.add(this.#border);
  }
  
  #updateBorder(finalColor) {
    const
      duration = 100,
      ease = 'Poser2';
    
    if (finalColor !== this.#borderColor) {
      this.scene.tweens.add({
        targets: this.#border, alpha: 0, duration: duration, ease: ease,
        onComplete: () => {
          this.#border.clear();
          this.#drawBorder(finalColor);
          this.#border.setAlpha(0);
          this.#borderColor = finalColor;
          this.scene.tweens.add({
            targets: this.#border, alpha: 1, duration: duration, ease: ease,
          });
        },
      });
    }
  }
  
  #setAlphaDefault() {
    this.#selectionCover.setAlpha(this.#alphaDefault);
  }
  
  #setAlphaSelected() {
    this.#selectionCover.setAlpha(this.#alphaSelected);
  }
  
  toggleSelect() {
    this.selected = !this.selected;
    if (this.selected) {
      this.#updateBorder(this.#borderColorSelected);
      this.#setAlphaSelected();
    } else {
      this.#updateBorder(this.#borderColorDefault);
      this.#setAlphaDefault();
    }
  }
  
  checkBorder() {
    if (this.selected) {
      this.#drawBorder(this.#borderColorSelected);
      this.#setAlphaSelected();
    } else {
      this.#drawBorder(this.#borderColorDefault);
      this.#setAlphaDefault();
    }
  }
  
  replaceCard(newCard) {
    const
      atlasKey = settings.card.ATLAS_KEY,
      frameKey = settings.card.getFrameKey(newCard);
    
    this.deselect();
    settings.fadeOutAnimation(
      this.scene, this.#card,
      (card) => card.setTexture(atlasKey, frameKey),
    );
    this.cardData = newCard;
    this.setInteractive();
  }
  
  removeCard() {
    this.deselect();
    settings.fadeOutAnimation(
      this.scene, this.#card,
      (card) => card.setTexture('__WHITE'),
    );
    this.disableInteractive();
  }
  
  deselect() {
    this.selected = false;
    this.#updateBorder(this.#borderColorDefault);
    this.#setAlphaDefault();
  }
}

export class ThumbnailSprite extends Phaser.GameObjects.Container {
  width = settings.thumbnail.WIDTH;
  height = settings.thumbnail.HEIGHT;
  
  #borderWidth = settings.thumbnail.BORDER_WIDTH;
  #borderColor = settings.thumbnail.BORDER_COLOR;
  
  #card = null;
  #border = null;
  
  index = null;
  cardData = null;
  
  constructor(scene, index, card) {
    const
      {
        ATLAS_KEY, getFrameKey, WIDTH, HEIGHT,
        MARGIN, BORDER_WIDTH,
      } = settings.thumbnail,
      
      x = WIDTH / 2 + index * (WIDTH + MARGIN),
      y = HEIGHT / 2 + settings.thumbnailText.HEIGHT +
        settings.thumbnailText.MARGIN;
    super(scene, x, y);
    
    this.#card = scene.add.image(0, 0, ATLAS_KEY, getFrameKey(card))
      .setDisplaySize(WIDTH - BORDER_WIDTH, HEIGHT - BORDER_WIDTH);
    this.#drawBorder(this.#borderColor);
    
    this.add([this.#card, this.#border]);
    
    scene.add.existing(this);
  }
  
  #drawBorder(color) {
    if (this.#border) this.#border.destroy(); // Clean up old border
    this.#border = drawBorder(this, this.#borderWidth, color);
    this.add(this.#border);
  }
  
  replaceCard(newCard) {
    const
      atlasKey = settings.thumbnail.ATLAS_KEY,
      frameKey = settings.thumbnail.getFrameKey(newCard);
    
    settings.fadeOutAnimation(
      this.scene, this.#card,
      (card) => card.setTexture(atlasKey, frameKey),
    );
    this.cardData = newCard;
  }
}

export class TextButton extends Phaser.GameObjects.Container {
  width = settings.button.WIDTH;
  height = settings.button.HEIGHT;
  
  #options = {};
  #bg = null;
  #shadow = null;
  #label = null;
  
  #textColor = settings.button.TEXT_COLOR;
  #alphaDefault = 0.8;
  #alphaSelected = 1;
  #radius = 8;
  
  constructor(scene, x, y, options = {}) {
    super(scene, x, y);
    
    this.#options = options;
    this.#draw();
    
    this.add([this.#shadow, this.#bg, this.#label]);
    this.#setInteractive();
    scene.add.existing(this);
  }
  
  #draw() {
    const
      {text, fillColor, textColor = this.#textColor} = this.#options,
      width = this.width,
      height = this.height;
    
    this.#bg = this.scene.add.graphics()
      .fillStyle(fillColor)
      .setAlpha(this.#alphaDefault)
      .fillRoundedRect(-width / 2, -height / 2, width, height, this.#radius);
    
    this.#shadow = this.scene.add.graphics()
      .fillStyle(0x000000, 0.1)
      .fillRoundedRect(-width / 2 + 3, -height / 2 + 3, width, height,
        this.#radius);
    
    this.#label = this.scene.add.text(0, 0, text, {
      fontFamily: settings.window.FONT_FAMILY,
      fontSize: '18px',
      fontStyle: 'bold',
      color: textColor,
    }).setOrigin(0.5);
  }
  
  #setInteractive() {
    setInteractiveAndPointerOverOut(this);
    this.on('pointerover', () => this.#alphaEffect(this.#alphaSelected));
    this.on('pointerout', () => this.#alphaEffect(this.#alphaDefault));
    
    this.on('pointerup', () => {
      this.disableInteractive();
      this.scene.tweens.add({
        targets: this, duration: 100, yoyo: true,
        alpha: 0.5, scaleX: 0.95, scaleY: 0.95,
        onComplete: () => this.setInteractive(),
      });
      this.execute();
    });
  }
  
  #alphaEffect(alpha) {
    alphaEffect(this.scene, this.#bg, alpha);
  }
  
  execute() {
    throw new Error('execute() must be implemented by subclass');
  }
}

export class TextBox extends Phaser.GameObjects.Container {
  width = settings.button.WIDTH;
  height = settings.button.HEIGHT;
  
  #options = {};
  #bg = null;
  label = null;
  
  constructor(scene, x, y, options = {}) {
    super(scene, x, y);
    
    this.#options = options;
    this.#draw();
    
    this.add([this.#bg, this.label]);
    scene.add.existing(this);
  }
  
  #draw() {
    const {
      text = '',
      width = this.width,
      height = this.height,
      backgroundColor = settings.window.BACKGROUND,
      alpha = 0,
      align = 'right',
      textColor = '#000000',
      fontFamily = settings.window.FONT_FAMILY,
      fontSize = '18px',
      radius = 8,
    } = this.#options;
    
    this.#bg = this.scene.add.graphics()
      .fillStyle(backgroundColor)
      .setAlpha(alpha)
      .fillRoundedRect(0, 0, width, height, radius);
    
    this.label = this.scene.add.text(width, 0, text, {
      align: align,
      fontFamily: fontFamily,
      fontSize: fontSize,
      fontStyle: 'bold',
      color: textColor,
    }).setOrigin(1, 0);
  }
}
