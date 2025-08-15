const CSRFToken = document.cookie.split('; ')
  .find(row => row.startsWith('csrftoken='))?.split('=')[1];

function getFrameKey(card) {
  return card ? `${card.color}_${card.shape}_${card.count}_${card.fill}` : 'empty';
}

const URL_BASE = '/boardgame/set/'
const URL_STATIC = '/static/a_boardgame_set/'

const windowSettings = {
  WIDTH: 600,
  HEIGHT: 800,
  BACKGROUND: 0xffffff,
  FONT_FAMILY: 'Noto Sans KR',
  MARGIN_X: 10,
  MARGIN_Y: 10,
}

const textboxSettings = {
  POSITION_X: windowSettings.MARGIN_X,
  POSITION_Y: windowSettings.MARGIN_Y,
  WIDTH: 116,
  HEIGHT: 30,
  MARGIN: 5,
  TEXT_COLOR_LABEL: '#ffffff',
  TEXT_COLOR_DATA: '#002060',
  BACKGROUND_COLOR: 0x002060,
  BORDER_WIDTH: 2,
  FONT_FAMILY: windowSettings.FONT_FAMILY,
}

const cardSize = {
  WIDTH: 120,
  HEIGHT: 180,
}

const cardSettings = {
  ATLAS_KEY: 'cardsheet',
  getFrameKey: getFrameKey,
  POSITION_X: windowSettings.MARGIN_X,
  POSITION_Y: 50,
  WIDTH: cardSize.WIDTH,
  HEIGHT: cardSize.HEIGHT,
  PADDING_X: (windowSettings.WIDTH - 2 * windowSettings.MARGIN_X - 4 * cardSize.WIDTH) / 3,
  PADDING_Y: 10,
  BORDER_WIDTH: 4,
  BORDER_COLOR_DEFAULT: 0xeeeeee,
  BORDER_COLOR_SELECTED: 0x008800,
}

const buttonSettings = {
  POSITION_X: windowSettings.MARGIN_X,
  POSITION_Y: 623,
  WIDTH: cardSize.WIDTH,
  HEIGHT: 35,
  PADDING: 10,
  TEXT_COLOR: '#ffffff',
  FILL_RESTART: 0x007bff,
  FILL_CHANGE: 0xc45816,
  FILL_HINT: 0x28a745,
  FONT_FAMILY: windowSettings.FONT_FAMILY,
}

const thumbnailTextSettings = {
  POSITION_X: 316,
  POSITION_Y: 623,
  WIDTH: 275,
  HEIGHT: 30,
  MARGIN: 10,
  BACKGROUND_COLOR: textboxSettings.BACKGROUND_COLOR,
  BORDER_WIDTH: 2,
  BORDER_COLOR: 0xeeeeee,
  FONT_FAMILY: windowSettings.FONT_FAMILY,
}

const thumbnailSettings = {
  ATLAS_KEY: 'cardsheet_small',
  getFrameKey: getFrameKey,
  WIDTH: 85,
  HEIGHT: 129,
  MARGIN: 10,
  BACKGROUND_COLOR: textboxSettings.BACKGROUND_COLOR,
  BORDER_WIDTH: 2,
  BORDER_COLOR: 0xeeeeee,
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
  thumbnailText: thumbnailTextSettings,
  button: buttonSettings,
  textbox: textboxSettings,
  fadeOutAnimation: fadeOutAnimation,
};
