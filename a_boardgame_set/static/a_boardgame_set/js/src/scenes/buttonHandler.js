import {settings} from '../constants.js';
import {TextButton} from './interface.js';

function changeCards(scene, urlInput) {
  let cardSprites = scene.cardSprites;
  const sessionId = scene.session.id;
  const sessionStatus = scene.getSessionStatus();
  
  fetch(urlInput, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': settings.CSRFToken,
    },
    body: JSON.stringify({sessionId, sessionStatus}),
  })
    .then(res => res.json())
    .then(data => {
      const {session, newCards, remainingCards} = data;
      const {
        elapsed_time, score, hint_requests,
        failure_count, success_count,
      } = session;
      
      scene.session = session;
      scene.remainingCards = remainingCards;
      scene.remainingCardsBox.data.setText(remainingCards);
      
      scene.elapsedTime = elapsed_time;
      scene.formattedTime = scene.formatElapsedTime(elapsed_time);
      scene.score = score;
      scene.hintRequests = hint_requests;
      scene.failureCount = failure_count;
      scene.successCount = success_count;
      
      scene.elapsedTimeBox.data.setText('0:00');
      scene.remainingCardsBox.data.setText(`${scene.remainingCards}`);
      scene.hintRequestsBox.data.setText(`${scene.hintRequests}`);
      scene.failSuccessBox.data.setText(
        `${scene.failureCount} / ${scene.successCount}`);
      scene.currentScoreBox.data.setText(`${scene.score}`);
      
      cardSprites.forEach((cs, i) => cs.replaceCard(newCards[i]));
    })
    .catch(error => console.error('게임 시작 데이터 요청 실패:', error));
}

export class ResetButton extends TextButton {
  execute() {
    const mainScene = this.scene.scene.get('MainScene');
    mainScene.restart();
  }
}

export class CardChangeButton extends TextButton {
  execute() {
    if (this.scene.remainingCards) {
      changeCards(this.scene, settings.URL_CARD_CHANGE);
      this.scene.SetDefaultToSelectRecords();
      this.scene.addLog('카드를 교체했습니다.', 'success');
    } else {
      this.scene.addLog('남은 카드가 없습니다.', 'failure');
    }
  }
}

export class HintButton extends TextButton {
  execute() {
    this.scene.hintSets.length === 0 ? this.requestHint() : this.showHint();
  }
  
  requestHint() {
    let cardSprites = this.scene.cardSprites;
    const sessionId = this.scene.session.id;
    
    fetch(settings.URL_HINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': settings.CSRFToken,
      },
      body: JSON.stringify({sessionId}),
    })
      .then(res => res.json())
      .then(data => {
        const {possibleSets, newCards} = data;
        
        if (possibleSets.length === 0) {
          if (newCards.length === 0) {
            this.scene.addLog('남은 카드가 없습니다.', 'failure');
            this.scene.scene.pause();
            this.scene.scene.launch('GameOverScene', {
              score: this.scene.score,
            });
          } else {
            this.scene.addLog('세트가 없습니다.', 'failure');
            cardSprites.forEach((cs, i) => cs.replaceCard(newCards[i]));
          }
        } else {
          this.scene.hintSets = possibleSets; // [[id1, id2, id3], [id4, id5, id6], ...]
          this.showHint();
        }
      });
  }
  
  showHint() {
    this.scene.hintRequests += 1;
    this.scene.addLog(`세트가 ${this.scene.hintSets.length}개 있습니다.`, 'success');
    this.scene.hintRequestsBox.data.setText(`${this.scene.hintRequests}`);
    this.showHintSprites();
  }
  
  showHintSprites() {
    this.scene.hintSets.forEach(hintSet => {
      let spriteIds = [];
      hintSet.forEach(cardId => {
        this.scene.cardSprites.forEach(cs => {
          if (cs.cardData.id === cardId) spriteIds.push(cs.index);
        });
      });
      spriteIds.sort((a, b) => a.index - b.index);
      console.log(spriteIds);
    });
  }
}
