var UpdateShapes = function () {
    var skewX = this.skewX;
    var width = this.width - Math.abs(skewX);
    var height = this.height;
    var trackFill = this.getShape('trackFill');
    trackFill.fillStyle(this.trackColor);
    if (trackFill.isFilled) {
        BuildRectangle(
            trackFill,
            0, 0,
            width, height,
            skewX
        )
            .close()
    }

    var bar = this.getShape('bar');
    bar.fillStyle(this.barColor);
    if (bar.isFilled) {
        var barX0, barX1;
        if (!this.rtl) {
            barX0 = 0;
            barX1 = width * this.value;
        } else {
            barX0 = width * (1 - this.value);
            barX1 = width;
        }

        BuildRectangle(
            bar,
            barX0, 0,
            barX1, height,
            skewX
        )
            .close()
    }

    var trackStroke = this.getShape('trackStroke');
    trackStroke.lineStyle(this.trackStrokeThickness, this.trackStrokeColor);
    if (trackStroke.isStroked) {
        BuildRectangle(
            trackStroke,
            0, 0,
            width, height,
            skewX
        )
            .end()
    }
}

var BuildRectangle = function (lines, x0, y0, x1, y1, skewX) {
    if (skewX >= 0) {
        lines
            .startAt(x0 + skewX, y0).lineTo(x1 + skewX, y0)
            .lineTo(x1, y1)
            .lineTo(x0, y1)
            .lineTo(x0 + skewX, y0)
    } else {
        lines
            .startAt(x0, y0).lineTo(x1, y0)
            .lineTo(x1 - skewX, y1)
            .lineTo(x0 - skewX, y1)
            .lineTo(x0, y0)
    }

    return lines;
}

export default UpdateShapes;