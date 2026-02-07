import Point from '../point/Point';
import Line from '../line/Line';


declare class Rectangle {
    
    constructor(x?: number, y?: number, width?: number, height?: number);

    
    static Area(rect: Rectangle): number;

    
    static Ceil<O extends Rectangle>(rect: O): O;

    
    static CeilAll<O extends Rectangle>(rect: O): O;

    
    static CenterOn<O extends Rectangle>(rect: O, x: number, y: number): O;

    
    static Clone(source: Rectangle): Rectangle;

    
    static Contains(rect: Rectangle, x: number, y: number): boolean;

    
    static ContainsPoint(rect: Rectangle, point: Point): boolean;

    
    static ContainsRect(rectA: Rectangle, rectB: Rectangle): boolean;

    
    static CopyFrom<O extends Rectangle>(source: Rectangle, dest: O): O;

    
    static Decompose(rect: Rectangle, out?: any[]): any[];

    
    static Equals(rect: Rectangle, toCompare: Rectangle): boolean;

    
    static FitInside<O extends Rectangle>(target: O, source: Rectangle): O;

    
    static FitOutside<O extends Rectangle>(target: O, source: Rectangle): O;

    
    static Floor<O extends Rectangle>(rect: O): O;

    
    static FloorAll<O extends Rectangle>(rect: O): O;

    
    static FromPoints<O extends Rectangle>(points: any[], out?: O): O;

    
    static FromXY<O extends Rectangle>(x1: number, y1: number, x2: number, y2: number, out?: O): O;

    
    static GetAspectRatio(rect: Rectangle): number;

    
    static GetCenter<O extends Point>(rect: Rectangle, out?: O): O;

    
    static GetPoint<O extends Point>(rectangle: Rectangle, position: number, out?: O): O;

    
    static GetPoints<O extends Point[]>(rectangle: Rectangle, step: number, quantity: number, out?: O): O;

    
    static GetSize<O extends Point>(rect: Rectangle, out?: O): O;

    
    static Inflate<O extends Rectangle>(rect: O, x: number, y: number): O;

    
    static Intersection<O extends Rectangle>(rectA: Rectangle, rectB: Rectangle, out?: Rectangle): O;

    
    static MarchingAnts<O extends Point[]>(rect: Rectangle, step?: number, quantity?: number, out?: O): O;

    
    static MergePoints<O extends Rectangle>(target: O, points: Point[]): O;

    
    static MergeRect<O extends Rectangle>(target: O, source: Rectangle): O;

    
    static MergeXY<O extends Rectangle>(target: O, x: number, y: number): O;

    
    static Offset<O extends Rectangle>(rect: O, x: number, y: number): O;

    
    static OffsetPoint<O extends Rectangle>(rect: O, point: Point): O;

    
    static Overlaps(rectA: Rectangle, rectB: Rectangle): boolean;

    
    static Perimeter(rect: Rectangle): number;

    
    static PerimeterPoint<O extends Point>(rectangle: Rectangle, angle: number, out?: O): O;

    
    static Random<O extends Point>(rect: Rectangle, out: O): O;

    
    static RandomOutside<O extends Point>(outer: Rectangle, inner: Rectangle, out?: O): O;

    
    readonly type: number;

    
    x: number;

    
    y: number;

    
    width: number;

    
    height: number;

    
    contains(x: number, y: number): boolean;

    
    getPoint<O extends Point>(position: number, output?: O): O;

    
    getPoints<O extends Point[]>(quantity: number, stepRate?: number, output?: O): O;

    
    getRandomPoint<O extends Point>(point?: O): O;

    
    setTo(x: number, y: number, width: number, height: number): this;

    
    setEmpty(): this;

    
    setPosition(x: number, y?: number): this;

    
    setSize(width: number, height?: number): this;

    
    isEmpty(): boolean;

    
    getLineA<O extends Line>(line?: O): O;

    
    getLineB<O extends Line>(line?: O): O;

    
    getLineC<O extends Line>(line?: O): O;

    
    getLineD<O extends Line>(line?: O): O;

    
    left: number;

    
    right: number;

    
    top: number;

    
    bottom: number;

    
    centerX: number;

    
    centerY: number;

    
    static SameDimensions(rect: Rectangle, toCompare: Rectangle): boolean;

    
    static Scale<O extends Rectangle>(rect: O, x: number, y: number): O;

    
    static Union<O extends Rectangle>(rectA: Rectangle, rectB: Rectangle, out?: O): O;

}

export default Rectangle;