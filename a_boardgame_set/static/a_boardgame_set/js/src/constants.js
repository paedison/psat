const CSRFToken = document.cookie.split('; ').
    find(row => row.startsWith('csrftoken='))?.split('=')[1];

function getFrameKey(card) {
  return card ? `${card.color}_${card.shape}_${card.count}_${card.fill}` : 'empty';
}

const URL_BASE = '/boardgame/set/'
const URL_STATIC = '/static/a_boardgame_set/'

const windowSettings = {
  WIDTH: 800,
  HEIGHT: 600,
  BACKGROUND: 0xffffff,
  FONT_FAMILY: 'Noto Sans KR',
  MARGIN_X: 55,
  MARGIN_Y: 40,
}

const cardSettings = {
  ATLAS_KEY: 'cardsheet',
  getFrameKey: getFrameKey,
  WIDTH: 100,
  HEIGHT: 150,
  MARGIN: 30,
  BORDER_WIDTH: 4,
  BORDER_COLOR_DEFAULT: 0xeeeeee,
  BORDER_COLOR_SELECTED: 0x008800,
}

const thumbnailSettings = {
  ATLAS_KEY: 'cardsheet_small',
  getFrameKey: getFrameKey,
  WIDTH: 50,
  HEIGHT: 73,
  MARGIN: 10,
  BORDER_WIDTH: 2,
  BORDER_COLOR: 0xeeeeee,
}

const buttonSettings = {
  WIDTH: 170,
  HEIGHT: 30,
  MARGIN: 10,
  TEXT_COLOR: '#ffffff',
  BACKGROUND_RESTART: 0x007bff,
  BACKGROUND_CHANGE: 0xc45816,
  BACKGROUND_HINT: 0x28a745,
}

const textboxSettings = {
  WIDTH: 170,
  HEIGHT: 30,
  MARGIN: 5,
  TEXT_COLOR_LABEL: '#ffffff',
  TEXT_COLOR_DATA: '#002060',
  BACKGROUND_COLOR: 0x002060,
  BORDER_WIDTH: 2,
}

function fadeOutAnimation(
  scene, targets, callback, duration = 250, ease = 'Power2') {
  scene.tweens.add({
    targets: targets, alpha: 0, duration: duration, ease: ease,
    onComplete: () => {
      if (typeof callback === 'function') callback(targets);
      scene.tweens.add(
        {targets: targets, alpha: 1, duration: duration, ease: ease});
    },
  });
}

export const settings = {
  CSRFToken: CSRFToken,
  
  URL_GAME_RESTART: `${URL_BASE}game/restart/`,
  URL_CARD_INITIATE: `${URL_BASE}card/initiate/`,
  URL_CARD_DRAW: `${URL_BASE}card/draw/`,
  URL_CARD_CHANGE: `${URL_BASE}card/change/`,
  URL_VALIDATE: `${URL_BASE}validate/`,
  URL_HINT: `${URL_BASE}hint/`,
  URL_ASSETS: `${URL_STATIC}assets/`,
  
  window: windowSettings,
  card: cardSettings,
  thumbnail: thumbnailSettings,
  button: buttonSettings,
  textbox: textboxSettings,
  fadeOutAnimation: fadeOutAnimation,
};
