/** @type {import('../types/phaser')} */

import {settings} from '../constants.js';
import {
  InformationBox,
  CardSprite,
  ThumbnailSprite,
  TextBox,
} from './interface.js';
import {
  ResetButton,
  CardChangeButton,
  HintButton,
} from './buttons.js';

export default class MainScene extends Phaser.Scene {
  session = {};
  cardSprites = [];
  isSelecting = false;
  selectedCardSprites = new Set();
  
  hintSets = [];
  logMessages = [];
  elapsedTime = 0;
  formattedTime = '0:00';
  remainingCards = 69;
  hintRequests = 0;
  failureCount = 0;
  successCount = 0;
  score = 0;
  thumbnailSprites = [];
  
  restartButton = null;
  cardChangeButton = null;
  hintButton = null;
  
  messageTextBox = null;
  elapsedTimeBox = null;
  remainingCardsBox = null;
  hintRequestsBox = null;
  failSuccessBox = null;
  currentScoreBox = null;
  thumbnailTextBox = null;
  
  constructor() {
    super('MainScene');
  }
  
  preload() {
    this.load.setBaseURL(settings.URL_ASSETS);
    this.loadAtlas(settings.card.ATLAS_KEY);
    this.loadAtlas(settings.thumbnail.ATLAS_KEY);
  }
  
  loadAtlas(key) {
    this.load.atlas(key, `${key}.png`, `${key}.json`);
  }
  
  create() {
    this.cameras.main.fadeIn(250, 255, 255, 255);
    this.handleHotKeys();
    this.createInformationBoxes();
    this.createInitialSprites();
    this.createButtons();
    this.createThumbnail();
  }
  
  SetDefaultToSelectRecords() {
    this.isSelecting = false;
    this.selectedCardSprites.clear();
    
    this.hintSets = [];
    this.messageTextBox.label.setText('');
  }
  
  restart() {
    const
      sessionId = this.session.id,
      sessionStatus = this.getSessionStatus(),
      cardSprites = this.cardSprites;
    
    fetch(settings.URL_GAME_RESTART, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': settings.CSRFToken,
      },
      body: JSON.stringify({sessionId, sessionStatus}),
    })
      .then(res => res.json())
      .then(data => {
        const {session, newCards} = data;
        
        this.session = session;
        this.isSelecting = false;
        this.selectedCardSprites.clear();
        
        this.setDefaultFields();
        cardSprites.forEach((cs, i) => {
          cs.replaceCard(newCards[i]);
          cs.setInteractive();
        });
      });
  }
  
  setDefaultFields() {
    this.hintSets = [];
    this.logMessages = [];
    this.elapsedTime = 0;
    this.formattedTime = '0:00';
    this.remainingCards = 69;
    this.hintRequests = 0;
    this.failureCount = 0;
    this.successCount = 0;
    this.score = 0;
    this.thumbnailSprites = [];
    
    this.addLog('게임을 새로 시작했습니다.', 'success');
    this.elapsedTimeBox.dataValue.setText('0:00');
    this.remainingCardsBox.dataValue.setText(`${this.remainingCards}`);
    this.hintRequestsBox.dataValue.setText(`${this.hintRequests}`);
    this.failSuccessBox.dataValue.setText(
      `${this.failureCount} / ${this.successCount}`);
    this.currentScoreBox.dataValue.setText(`${this.score}`);
  }
  
  getSessionStatus() {
    return {
      elapsedTime: this.elapsedTime,
      score: this.score,
      hintRequests: this.hintRequests,
      failureCount: this.failureCount,
      successCount: this.successCount,
    };
  }
  
  createInitialSprites() {
    fetch(settings.URL_CARD_INITIATE, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': settings.CSRFToken,
      },
    })
      .then(res => res.json())
      .then(data => {
        const
          {POSITION_X, POSITION_Y} = settings.card,
          {session, newCards, remainingCards} = data,
          
          {
            elapsed_time, score, hint_requests, failure_count, success_count,
          } = session;
        
        this.session = session;
        
        this.elapsedTime = elapsed_time;
        this.remainingCards = remainingCards;
        this.remainingCardsBox.dataValue.setText(remainingCards);
        this.hintRequests = hint_requests;
        this.failureCount = failure_count;
        this.successCount = success_count;
        this.score = score;
        
        newCards.forEach((newCard, index) => {
          const cardSprite = new CardSprite(this, index, newCard)
            .on('pointerup', () => this.handleCardSelection(cardSprite));
          this.cardSprites.push(cardSprite);
        });
        
        this.add.container(POSITION_X, POSITION_Y, this.cardSprites);
      });
  }
  
  createInformationBoxes() {
    const
      {
        POSITION_X, POSITION_Y, WIDTH,
      } = settings.textbox,
      y = 0;
    
    let x = 0;
    this.elapsedTimeBox = new InformationBox(this, x, y, {
      labelText: '게임 시간',
      dataText: this.formatElapsedTime(this.elapsedTime),
    });
    
    x += WIDTH;
    this.remainingCardsBox = new InformationBox(this, x, y, {
      labelText: '남은 카드',
      dataText: `${this.remainingCards}`,
    });
    
    x += WIDTH;
    this.hintRequestsBox = new InformationBox(this, x, y, {
      labelText: '힌트 확인',
      dataText: `${this.hintRequests}`,
    });
    
    x += WIDTH;
    this.failSuccessBox = new InformationBox(this, x, y, {
      labelText: '실패/성공',
      dataText: `${this.failureCount} / ${this.successCount}`,
    });
    
    x += WIDTH;
    this.currentScoreBox = new InformationBox(this, x, y, {
      labelText: '현재 점수',
      dataText: `${this.score}`,
    });
    
    this.add.container(POSITION_X, POSITION_Y, [
      this.elapsedTimeBox,
      this.remainingCardsBox,
      this.hintRequestsBox,
      this.failSuccessBox,
      this.currentScoreBox,
    ]);
  }
  
  createButtons() {
    const
      {
        POSITION_X, POSITION_Y,
        WIDTH, HEIGHT, PADDING,
        FILL_RESTART: fillRestart,
        FILL_CHANGE: fillChange,
        FILL_HINT: fillHint,
      } = settings.button;
    
    let x = WIDTH / 2;
    let y = HEIGHT / 2;
    const incrementY = HEIGHT + PADDING;
    this.restartButton = new ResetButton(this, x, y, {
      text: '새로 시작(R)',
      fillColor: fillRestart,
    });
    
    y += incrementY;
    this.cardChangeButton = new CardChangeButton(this, x, y, {
      text: '카드 교체(C)',
      fillColor: fillChange,
    });
    
    y += incrementY;
    this.hintButton = new HintButton(this, x, y, {
      text: '힌트 보기(H)',
      fillColor: fillHint,
    });
    
    y += HEIGHT / 2 + PADDING;
    this.messageTextBox = new TextBox(this, y);
    
    this.add.container(POSITION_X, POSITION_Y, [
      this.restartButton,
      this.cardChangeButton,
      this.hintButton,
      this.messageTextBox,
    ]);
  }
  
  createThumbnail() {
    const {
      POSITION_X, POSITION_Y, FONT_FAMILY,
      WIDTH, HEIGHT, BORDER_WIDTH, BACKGROUND_COLOR,
    } = settings.thumbnailText;
    
    const bg = this.add.graphics()
      .fillStyle(BACKGROUND_COLOR)
      .fillRect(0, 0, WIDTH, HEIGHT)
      .strokeRect(0, 0, WIDTH, HEIGHT);
    
    const label = this.add.text(WIDTH / 2, HEIGHT / 2, '찾은 세트', {
      fontFamily: FONT_FAMILY,
      fontSize: '18px',
      fontStyle: 'bold',
      color: '#ffffff',
    }).setOrigin(0.5);
    
    const container = this.add.container(
      POSITION_X, POSITION_Y, [bg, label]);
    
    for (let i = 0; i < 3; i++) {
      const thumbnail = new ThumbnailSprite(
        this, i, null);
      this.thumbnailSprites.push(thumbnail);
      container.add(thumbnail);
    }
  }
  
  update(time, delta) {
    this.updateTimer(delta);
    this.updateUI();
    // this.checkGameState();
  }
  
  updateTimer(delta) {
    this.elapsedTime += delta;
    this.formattedTime = this.formatElapsedTime(this.elapsedTime);
  }
  
  formatElapsedTime(ms) {
    const
      totalSeconds = Math.floor(ms / 1000),
      hours = Math.floor(totalSeconds / 3600),
      minutes = Math.floor((totalSeconds % 3600) / 60),
      seconds = totalSeconds % 60;
    
    return hours > 0
      ? `${hours}:${minutes.toString().padStart(2, '0')}`
      : `${minutes}:${seconds.toString().padStart(2, '0')}`;
  }
  
  updateUI() {
    this.elapsedTimeBox.dataValue.setText(this.formattedTime);
  }
  
  checkGameState() {
    this.cardSprites.forEach(cardSprite => cardSprite.checkBorder());
  }
  
  async handleCardSelection(cardSprite) {
    if (this.isSelecting) return;
    
    this.isSelecting = true;
    
    if (this.selectedCardSprites.size > 3) {
      this.selectedCardSprites.forEach(cs => {
        cs.selected = false;
        cs.checkBorder();
      });
      this.selectedCardSprites.clear();
      this.isSelecting = false;
      return;
    }
    
    await cardSprite.toggleSelect();
    
    cardSprite.selected
      ? this.selectedCardSprites.add(cardSprite)
      : this.selectedCardSprites.delete(cardSprite);
    
    if (this.selectedCardSprites.size === 3) {
      const selectedCardIds = [...this.selectedCardSprites]
        .map(cs => cs.cardData.id);
      
      try {
        const sessionId = this.session.id;
        
        const res = await fetch(settings.URL_VALIDATE, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': settings.CSRFToken,
          },
          body: JSON.stringify({sessionId, selectedCardIds}),
        });
        
        const data = await res.json();
        setTimeout(() => this.validateSet(data), 500);
      } catch (err) {
        console.error('서버 통신 오류:', err);
      }
    }
    
    this.isSelecting = false;
  }
  
  validateSet(data) {
    const
      {isValidSet, remainingCards, newCards} = data,
      selected = [...this.selectedCardSprites];
    
    if (!isValidSet) {
      this.addLog('세트가 아닙니다.', 'failure');
      this.failureCount += 1;
      selected.forEach(cs => cs.deselect());
    } else {
      this.addLog('세트 성공!', 'success');
      
      this.remainingCards = remainingCards;
      this.successCount += 1;
      this.score += 3;
      this.hintSets = [];
      
      this.remainingCardsBox.dataValue.setText(`${this.remainingCards}`);
      this.currentScoreBox.dataValue.setText(`${this.score}`);
      
      selected.forEach((cs, i) => {
        this.thumbnailSprites[i].replaceCard(cs.cardData);
      });
      
      newCards.length === 3
        ? selected.forEach((cs, i) => cs.replaceCard(newCards[i]))
        : selected.forEach(cs => cs.removeCard());
    }
    
    this.failSuccessBox.dataValue.setText(
      `${this.failureCount} / ${this.successCount}`);
    this.selectedCardSprites.clear();
  }
  
  handleHotKeys() {
    this.input.keyboard.on('keydown', event => {
      switch (event.code) {
        case 'KeyR':
          this.restartButton.execute();
          break;
        case 'KeyC':
          this.cardChangeButton.execute();
          break;
        case 'KeyH':
          this.hintButton.execute();
          break;
      }
    });
  }
  
  addLog(message, logType = 'normal') {
    const
      logColor = {
        'normal': '#000000',
        'failure': '#ff0000',
        'success': '#008800',
      },
      color = logColor[logType];
    
    this.logMessages.push(message);
    if (this.logMessages.length > 1) this.logMessages.shift(); // 최근 1개만 표시
    this.messageTextBox.label
      .setText(this.logMessages.join('\n'))
      .setColor(color);
  }
}
