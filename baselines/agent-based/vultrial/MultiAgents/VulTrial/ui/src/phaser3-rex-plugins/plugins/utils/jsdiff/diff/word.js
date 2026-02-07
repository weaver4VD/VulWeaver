import Diff from './base';
import {generateOptions} from '../util/params';
const extendedWordChars = /^[a-zA-Z\u{C0}-\u{FF}\u{D8}-\u{F6}\u{F8}-\u{2C6}\u{2C8}-\u{2D7}\u{2DE}-\u{2FF}\u{1E00}-\u{1EFF}]+$/u;

const reWhitespace = /\S/;

export const wordDiff = new Diff();
wordDiff.equals = function(left, right) {
  if (this.options.ignoreCase) {
    left = left.toLowerCase();
    right = right.toLowerCase();
  }
  return left === right || (this.options.ignoreWhitespace && !reWhitespace.test(left) && !reWhitespace.test(right));
};
wordDiff.tokenize = function(value) {
  let tokens = value.split(/([^\S\r\n]+|[()[\]{}'"\r\n]|\b)/);
  for (let i = 0; i < tokens.length - 1; i++) {
    if (!tokens[i + 1] && tokens[i + 2]
          && extendedWordChars.test(tokens[i])
          && extendedWordChars.test(tokens[i + 2])) {
      tokens[i] += tokens[i + 2];
      tokens.splice(i + 1, 2);
      i--;
    }
  }

  return tokens;
};

export function diffWords(oldStr, newStr, options) {
  options = generateOptions(options, {ignoreWhitespace: true});
  return wordDiff.diff(oldStr, newStr, options);
}

export function diffWordsWithSpace(oldStr, newStr, options) {
  return wordDiff.diff(oldStr, newStr, options);
}
