export function capitalizeFirstLetter(string: string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

export function roundToTwoDecimalPlaces(value: number) {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}
