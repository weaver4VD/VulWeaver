import {Vector2Like} from '../types';
import Rectangle from '../rectangle/Rectangle';


declare class Point {
    
    constructor(x?: number, y?: number);

    
    static Ceil<O extends Point>(point: O): O;

    
    static Clone(source: Point): Point;

    
    static CopyFrom<O extends Point>(source: Point, dest: O): O;

    
    static Equals(point: Point, toCompare: Point): boolean;

    
    static Floor<O extends Point>(point: O): O;

    
    static GetCentroid<O extends Point>(points: Vector2Like[], out?: O): O;

    
    static GetMagnitude(point: Point): number;

    
    static GetMagnitudeSq(point: Point): number;

    
    static GetRectangleFromPoints<O extends Rectangle>(points: Vector2Like[], out?: O): O;

    
    static Interpolate<O extends Point>(pointA: Point, pointB: Point, t?: number, out?: O): O;

    
    static Invert<O extends Point>(point: O): O;

    
    static Negative<O extends Point>(point: Point, out?: O): O;

    
    readonly type: number;

    
    x: number;

    
    y: number;

    
    setTo(x?: number, y?: number): this;

    
    static Project<O extends Point>(pointA: Point, pointB: Point, out?: O): O;

    
    static ProjectUnit<O extends Point>(pointA: Point, pointB: Point, out?: O): O;

    
    static SetMagnitude<O extends Point>(point: O, magnitude: number): O;

}

export default Point;