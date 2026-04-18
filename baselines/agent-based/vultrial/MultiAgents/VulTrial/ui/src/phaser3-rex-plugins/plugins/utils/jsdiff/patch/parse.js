export function parsePatch(uniDiff, options = {}) {
  let diffstr = uniDiff.split(/\r\n|[\n\v\f\r\x85]/),
      delimiters = uniDiff.match(/\r\n|[\n\v\f\r\x85]/g) || [],
      list = [],
      i = 0;

  function parseIndex() {
    let index = {};
    list.push(index);
    while (i < diffstr.length) {
      let line = diffstr[i];
      if ((/^(\-\-\-|\+\+\+|@@)\s/).test(line)) {
        break;
      }
      let header = (/^(?:Index:|diff(?: -r \w+)+)\s+(.+?)\s*$/).exec(line);
      if (header) {
        index.index = header[1];
      }

      i++;
    }
    parseFileHeader(index);
    parseFileHeader(index);
    index.hunks = [];

    while (i < diffstr.length) {
      let line = diffstr[i];

      if ((/^(Index:|diff|\-\-\-|\+\+\+)\s/).test(line)) {
        break;
      } else if ((/^@@/).test(line)) {
        index.hunks.push(parseHunk());
      } else if (line && options.strict) {
        throw new Error('Unknown line ' + (i + 1) + ' ' + JSON.stringify(line));
      } else {
        i++;
      }
    }
  }
  function parseFileHeader(index) {
    const fileHeader = (/^(---|\+\+\+)\s+(.*)$/).exec(diffstr[i]);
    if (fileHeader) {
      let keyPrefix = fileHeader[1] === '---' ? 'old' : 'new';
      const data = fileHeader[2].split('\t', 2);
      let fileName = data[0].replace(/\\\\/g, '\\');
      if ((/^".*"$/).test(fileName)) {
        fileName = fileName.substr(1, fileName.length - 2);
      }
      index[keyPrefix + 'FileName'] = fileName;
      index[keyPrefix + 'Header'] = (data[1] || '').trim();

      i++;
    }
  }
  function parseHunk() {
    let chunkHeaderIndex = i,
        chunkHeaderLine = diffstr[i++],
        chunkHeader = chunkHeaderLine.split(/@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@/);

    let hunk = {
      oldStart: +chunkHeader[1],
      oldLines: typeof chunkHeader[2] === 'undefined' ? 1 : +chunkHeader[2],
      newStart: +chunkHeader[3],
      newLines: typeof chunkHeader[4] === 'undefined' ? 1 : +chunkHeader[4],
      lines: [],
      linedelimiters: []
    };
    if (hunk.oldLines === 0) {
      hunk.oldStart += 1;
    }
    if (hunk.newLines === 0) {
      hunk.newStart += 1;
    }

    let addCount = 0,
        removeCount = 0;
    for (; i < diffstr.length; i++) {
      if (diffstr[i].indexOf('--- ') === 0
            && (i + 2 < diffstr.length)
            && diffstr[i + 1].indexOf('+++ ') === 0
            && diffstr[i + 2].indexOf('@@') === 0) {
          break;
      }
      let operation = (diffstr[i].length == 0 && i != (diffstr.length - 1)) ? ' ' : diffstr[i][0];

      if (operation === '+' || operation === '-' || operation === ' ' || operation === '\\') {
        hunk.lines.push(diffstr[i]);
        hunk.linedelimiters.push(delimiters[i] || '\n');

        if (operation === '+') {
          addCount++;
        } else if (operation === '-') {
          removeCount++;
        } else if (operation === ' ') {
          addCount++;
          removeCount++;
        }
      } else {
        break;
      }
    }
    if (!addCount && hunk.newLines === 1) {
      hunk.newLines = 0;
    }
    if (!removeCount && hunk.oldLines === 1) {
      hunk.oldLines = 0;
    }
    if (options.strict) {
      if (addCount !== hunk.newLines) {
        throw new Error('Added line count did not match for hunk at line ' + (chunkHeaderIndex + 1));
      }
      if (removeCount !== hunk.oldLines) {
        throw new Error('Removed line count did not match for hunk at line ' + (chunkHeaderIndex + 1));
      }
    }

    return hunk;
  }

  while (i < diffstr.length) {
    parseIndex();
  }

  return list;
}
