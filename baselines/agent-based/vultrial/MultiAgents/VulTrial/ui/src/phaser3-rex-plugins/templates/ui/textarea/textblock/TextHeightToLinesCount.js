var TextHeightToLinesCount = function (height) {
    return (height - this.textLineSpacing) / (this.textLineHeight + this.textLineSpacing);
}
export default TextHeightToLinesCount;