const RotateAround = Phaser.Math.RotateAround;

export default {
    worldToLocal(point) {
        point.x -= this.x;
        point.y -= this.y;
        RotateAround(point, 0, 0, -this.rotation);
        point.x /= this.scaleX;
        point.y /= this.scaleY;
        return point;
    },

    localToWorld(point) {
        point.x *= this.scaleX;
        point.y *= this.scaleY;
        RotateAround(point, 0, 0, this.rotation);
        point.x += this.x;
        point.y += this.y;
        return point;
    }
};