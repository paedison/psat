const writingStyle = {
  pen: {
    strokeWidth: 2,
    alpha: 0.4,
    strokeCap: 'round',
    blendMode: 'normal',
  },
  highlighter: {
    strokeWidth: 20,
    alpha: 0.4,
    strokeCap: 'round',
    blendMode: 'multiply'
  },
  eraser: {
    strokeWidth: 20,
    alpha: 1,
    strokeCap: 'round',
    blendMode: 'destination-out',
  }
};

export const constants = {
  angleStep: Math.PI / 100,
  writingStyle: writingStyle,
}
