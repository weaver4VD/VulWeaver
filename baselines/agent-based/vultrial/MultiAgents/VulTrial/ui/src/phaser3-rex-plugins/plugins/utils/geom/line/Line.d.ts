import Point from '../point/Point';
import { Vector2Like, Vector2 } from '../types';


declare class Line {
    
    constructor(x1?: number, y1?: number, x2?: number, y2?: number);

    
    static Angle(line: Line): number;

    
    static BresenhamPoints(line: Line, stepRate?: number, results?: Vector2Like[]): Vector2Like[];

    
    static CenterOn(line: Line, x: number, y: number): Line;

    
    static Clone(source: Line): Line;

    
    static CopyFrom<O extends Line>(source: Line, dest: O): O;

    
    static Equals(line: Line, toCompare: Line): boolean;

    
    static Extend(line: Line, left: number, right?: number): Line;

    
    static GetEasedPoints<O extends Point[]>(line: Line, ease: string | Function, quantity: number, collinearThreshold?: number, easeParams?: number[]): O;

    
    static GetMidPoint<O extends Point>(line: Line, out?: O): O;

    
    static GetNearestPoint<O extends Point>(line: Line, point: Point | object, out?: O): O;

    
    static GetNormal<O extends Point>(line: Line, out?: O): O;

    
    static GetPoint<O extends Point>(line: Line, position: number, out?: O): O;

    
    static GetPoints<O extends Point[]>(line: Line, quantity: number, stepRate?: number, out?: O): O;

    
    static GetShortestDistance<O extends Point>(line: Line, point: Point | object): O;

    
    static Height(line: Line): number;

    
    static Length(line: Line): number;

    
    readonly type: number;

    
    x1: number;

    
    y1: number;

    
    x2: number;

    
    y2: number;

    
    getPoint<O extends Point>(position: number, output?: O): O;

    
    getPoints<O extends Point[]>(quantity: number, stepRate?: number, output?: O): O;

    
    getRandomPoint<O extends Point>(point?: O): O;

    
    setTo(x1?: number, y1?: number, x2?: number, y2?: number): this;

    
    getPointA(vec2?: Vector2): Vector2;

    
    getPointB(vec2?: Vector2): Vector2;

    
    left: number;

    
    right: number;

    
    top: number;

    
    bottom: number;

    
    static NormalAngle(line: Line): number;

    
    static NormalX(line: Line): number;

    
    static NormalY(line: Line): number;

    
    static Offset<O extends Line>(line: O, x: number, y: number): O;

    
    static PerpSlope(line: Line): number;

    
    static Random<O extends Point>(line: Line, out?: O): O;

    
    static ReflectAngle(lineA: Line, lineB: Line): number;

    
    static Rotate<O extends Line>(line: O, angle: number): O;

    
    static RotateAroundPoint<O extends Line>(line: O, point: Point | object, angle: number): O;

    
    static RotateAroundXY<O extends Line>(line: O, x: number, y: number, angle: number): O;

    
    static SetToAngle<O extends Line>(line: O, x: number, y: number, angle: number, length: number): O;

    
    static Slope(line: Line): number;

    
    static Width(line: Line): number;

}

export default Line;