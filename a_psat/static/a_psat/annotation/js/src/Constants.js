const writingStyle = {
  pen: {
    strokeWidth: 2,
    strokeCap: 'round',
    blendMode: 'normal',
  },
  highlighter: {
    strokeWidth: 20,
    strokeCap: 'round',
    blendMode: 'multiply'
  },
  eraser: {
    strokeWidth: 20,
    strokeCap: 'round',
    blendMode: 'destination-out',
  }
};

export const constants = {
  angleStep: Math.PI / 100,
  writingStyle: writingStyle,
}
