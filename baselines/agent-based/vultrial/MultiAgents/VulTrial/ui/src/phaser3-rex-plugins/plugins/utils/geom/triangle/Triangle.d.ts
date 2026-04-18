import Point from '../point/Point';
import Circle from '../circle/Circle';
import Line from '../line/Line';
import { Vector2Like } from '../types';


declare class Triangle {
    
    constructor(x1?: number, y1?: number, x2?: number, y2?: number, x3?: number, y3?: number);

    
    static Area(triangle: Triangle): number;

    
    static BuildEquilateral(x: number, y: number, length: number): Triangle;

    
    static BuildFromPolygon<O extends Triangle[]>(data: any[], holes?: any[], scaleX?: number, scaleY?: number, out?: O): O;

    
    static BuildRight(x: number, y: number, width: number, height: number): Triangle;

    
    static CenterOn<O extends Triangle>(triangle: O, x: number, y: number, centerFunc?: CenterFunction): O;

    
    static Centroid<O extends Point>(triangle: Triangle, out?: O): O;

    
    static CircumCenter(triangle: Triangle, out?: Vector2Like): Vector2Like;

    
    static CircumCircle(triangle: Triangle, out?: Circle): Circle;

    
    static Clone(source: Triangle): Triangle;

    
    static Contains(triangle: Triangle, x: number, y: number): boolean;

    
    static ContainsArray(triangle: Triangle, points: Point[], returnFirst?: boolean, out?: any[]): Point[];

    
    static ContainsPoint(triangle: Triangle, point: Vector2Like): boolean;

    
    static CopyFrom<O extends Triangle>(source: Triangle, dest: O): O;

    
    static Decompose(triangle: Triangle, out?: any[]): any[];

    
    static Equals(triangle: Triangle, toCompare: Triangle): boolean;

    
    static GetPoint<O extends Point>(triangle: Triangle, position: number, out?: O): O;

    
    static GetPoints<O extends Point>(triangle: Triangle, quantity: number, stepRate: number, out?: O): O;

    
    static InCenter<O extends Point>(triangle: Triangle, out?: O): O;

    
    static Offset<O extends Triangle>(triangle: O, x: number, y: number): O;

    
    static Perimeter(triangle: Triangle): number;

    
    static Random<O extends Point>(triangle: Triangle, out?: O): O;

    
    static Rotate<O extends Triangle>(triangle: O, angle: number): O;

    
    static RotateAroundPoint<O extends Triangle>(triangle: O, point: Point, angle: number): O;

    
    static RotateAroundXY<O extends Triangle>(triangle: O, x: number, y: number, angle: number): O;

    
    readonly type: number;

    
    x1: number;

    
    y1: number;

    
    x2: number;

    
    y2: number;

    
    x3: number;

    
    y3: number;

    
    contains(x: number, y: number): boolean;

    
    getPoint<O extends Point>(position: number, output?: O): O;

    
    getPoints<O extends Point[]>(quantity: number, stepRate?: number, output?: O): O;

    
    getRandomPoint<O extends Point>(point?: O): O;

    
    setTo(x1?: number, y1?: number, x2?: number, y2?: number, x3?: number, y3?: number): this;

    
    getLineA(line?: Line): Line;

    
    getLineB(line?: Line): Line;

    
    getLineC(line?: Line): Line;

    
    left: number;

    
    right: number;

    
    top: number;

    
    bottom: number;

}

export default Triangle;