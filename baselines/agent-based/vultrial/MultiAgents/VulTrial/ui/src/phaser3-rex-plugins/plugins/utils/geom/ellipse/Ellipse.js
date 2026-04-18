

import Class from '../../object/Class.js';
import Contains from './Contains.js';
import GetPoint from './GetPoint.js';
import GetPoints from './GetPoints.js';
import Random from './Random.js';


var Ellipse = new Class({

    initialize:

        function Ellipse(x, y, width, height) {
            if (x === undefined) { x = 0; }
            if (y === undefined) { y = 0; }
            if (width === undefined) { width = 0; }
            if (height === undefined) { height = 0; }

            
            this.x = x;

            
            this.y = y;

            
            this.width = width;

            
            this.height = height;
        },

    
    contains: function (x, y) {
        return Contains(this, x, y);
    },

    
    getPoint: function (position, point) {
        return GetPoint(this, position, point);
    },

    
    getPoints: function (quantity, stepRate, output) {
        return GetPoints(this, quantity, stepRate, output);
    },

    
    getRandomPoint: function (point) {
        return Random(this, point);
    },

    
    setTo: function (x, y, width, height) {
        this.x = x;
        this.y = y;
        this.width = width;
        this.height = height;

        return this;
    },

    
    setEmpty: function () {
        this.width = 0;
        this.height = 0;

        return this;
    },

    
    setPosition: function (x, y) {
        if (y === undefined) { y = x; }

        this.x = x;
        this.y = y;

        return this;
    },

    
    setSize: function (width, height) {
        if (height === undefined) { height = width; }

        this.width = width;
        this.height = height;

        return this;
    },

    
    isEmpty: function () {
        return (this.width <= 0 || this.height <= 0);
    },

    
    getMinorRadius: function () {
        return Math.min(this.width, this.height) / 2;
    },

    
    getMajorRadius: function () {
        return Math.max(this.width, this.height) / 2;
    },

    
    left: {

        get: function () {
            return this.x - (this.width / 2);
        },

        set: function (value) {
            this.x = value + (this.width / 2);
        }

    },

    
    right: {

        get: function () {
            return this.x + (this.width / 2);
        },

        set: function (value) {
            this.x = value - (this.width / 2);
        }

    },

    
    top: {

        get: function () {
            return this.y - (this.height / 2);
        },

        set: function (value) {
            this.y = value + (this.height / 2);
        }

    },

    
    bottom: {

        get: function () {
            return this.y + (this.height / 2);
        },

        set: function (value) {
            this.y = value - (this.height / 2);
        }

    }

});

export default Ellipse;
