export const COLORS = {
  black: '#000000',
  red: '#FF0000',
  blue: '#0000FF',
  green: '#008000',
  yellow: '#ffea00',
  orange: '#ffa500',
};

function hexToRgba(hexCode, alpha = 0.4) {
  const val = (s, e) => parseInt(hexCode.slice(s, e), 16)
  
  const r = val(1, 3)
  const g = val(3, 5)
  const b = val(5, 7)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export function colorToRgba(colorName, alpha = 0.4) {
  const hexCode = COLORS[colorName]
  console.log(colorName)
  console.log(hexCode)
  return hexToRgba(hexCode, alpha);
}