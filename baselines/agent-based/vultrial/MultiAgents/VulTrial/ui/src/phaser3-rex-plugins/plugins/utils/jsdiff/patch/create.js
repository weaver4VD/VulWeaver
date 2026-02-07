import {diffLines} from '../diff/line';

export function structuredPatch(oldFileName, newFileName, oldStr, newStr, oldHeader, newHeader, options) {
  if (!options) {
    options = {};
  }
  if (typeof options.context === 'undefined') {
    options.context = 4;
  }

  const diff = diffLines(oldStr, newStr, options);
  if(!diff) {
    return;
  }

  diff.push({value: '', lines: []});

  function contextLines(lines) {
    return lines.map(function(entry) { return ' ' + entry; });
  }

  let hunks = [];
  let oldRangeStart = 0, newRangeStart = 0, curRange = [],
      oldLine = 1, newLine = 1;
  for (let i = 0; i < diff.length; i++) {
    const current = diff[i],
          lines = current.lines || current.value.replace(/\n$/, '').split('\n');
    current.lines = lines;

    if (current.added || current.removed) {
      if (!oldRangeStart) {
        const prev = diff[i - 1];
        oldRangeStart = oldLine;
        newRangeStart = newLine;

        if (prev) {
          curRange = options.context > 0 ? contextLines(prev.lines.slice(-options.context)) : [];
          oldRangeStart -= curRange.length;
          newRangeStart -= curRange.length;
        }
      }
      curRange.push(... lines.map(function(entry) {
        return (current.added ? '+' : '-') + entry;
      }));
      if (current.added) {
        newLine += lines.length;
      } else {
        oldLine += lines.length;
      }
    } else {
      if (oldRangeStart) {
        if (lines.length <= options.context * 2 && i < diff.length - 2) {
          curRange.push(... contextLines(lines));
        } else {
          let contextSize = Math.min(lines.length, options.context);
          curRange.push(... contextLines(lines.slice(0, contextSize)));

          let hunk = {
            oldStart: oldRangeStart,
            oldLines: (oldLine - oldRangeStart + contextSize),
            newStart: newRangeStart,
            newLines: (newLine - newRangeStart + contextSize),
            lines: curRange
          };
          if (i >= diff.length - 2 && lines.length <= options.context) {
            let oldEOFNewline = ((/\n$/).test(oldStr));
            let newEOFNewline = ((/\n$/).test(newStr));
            let noNlBeforeAdds = lines.length == 0 && curRange.length > hunk.oldLines;
            if (!oldEOFNewline && noNlBeforeAdds && oldStr.length > 0) {
              curRange.splice(hunk.oldLines, 0, '\\ No newline at end of file');
            }
            if ((!oldEOFNewline && !noNlBeforeAdds) || !newEOFNewline) {
              curRange.push('\\ No newline at end of file');
            }
          }
          hunks.push(hunk);

          oldRangeStart = 0;
          newRangeStart = 0;
          curRange = [];
        }
      }
      oldLine += lines.length;
      newLine += lines.length;
    }
  }

  return {
    oldFileName: oldFileName, newFileName: newFileName,
    oldHeader: oldHeader, newHeader: newHeader,
    hunks: hunks
  };
}

export function formatPatch(diff) {
  const ret = [];
  if (diff.oldFileName == diff.newFileName) {
    ret.push('Index: ' + diff.oldFileName);
  }
  ret.push('===================================================================');
  ret.push('--- ' + diff.oldFileName + (typeof diff.oldHeader === 'undefined' ? '' : '\t' + diff.oldHeader));
  ret.push('+++ ' + diff.newFileName + (typeof diff.newHeader === 'undefined' ? '' : '\t' + diff.newHeader));

  for (let i = 0; i < diff.hunks.length; i++) {
    const hunk = diff.hunks[i];
    if (hunk.oldLines === 0) {
      hunk.oldStart -= 1;
    }
    if (hunk.newLines === 0) {
      hunk.newStart -= 1;
    }
    ret.push(
      '@@ -' + hunk.oldStart + ',' + hunk.oldLines
      + ' +' + hunk.newStart + ',' + hunk.newLines
      + ' @@'
    );
    ret.push.apply(ret, hunk.lines);
  }

  return ret.join('\n') + '\n';
}

export function createTwoFilesPatch(oldFileName, newFileName, oldStr, newStr, oldHeader, newHeader, options) {
  return formatPatch(structuredPatch(oldFileName, newFileName, oldStr, newStr, oldHeader, newHeader, options));
}

export function createPatch(fileName, oldStr, newStr, oldHeader, newHeader, options) {
  return createTwoFilesPatch(fileName, fileName, oldStr, newStr, oldHeader, newHeader, options);
}
