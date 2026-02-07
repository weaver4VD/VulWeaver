var LinesCountToTextHeight = function (linesCount) {
    return (linesCount * (this.textLineHeight + this.textLineSpacing)) - this.textLineSpacing;
}
export default LinesCountToTextHeight;