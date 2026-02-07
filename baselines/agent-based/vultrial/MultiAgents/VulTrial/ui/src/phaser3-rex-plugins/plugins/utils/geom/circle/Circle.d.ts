import Point from '../point/Point';
import Rectangle from '../rectangle/Rectangle';


declare class Circle {
    
    constructor(x?: number, y?: number, radius?: number);

    
    static Area(circle: Circle): number;

    
    readonly type: number;

    
    x: number;

    
    y: number;

    
    contains(x: number, y: number): boolean;

    
    getPoint<O extends Point>(position: number, out?: O): O;

    
    getPoints<O extends Point[]>(quantity: number, stepRate?: number, output?: O): O;

    
    getRandomPoint<O extends Point>(point?: O): O;

    
    setTo(x?: number, y?: number, radius?: number): this;

    
    setEmpty(): this;

    
    setPosition(x?: number, y?: number): this;

    
    isEmpty(): boolean;

    
    radius: number;

    
    diameter: number;

    
    left: number;

    
    right: number;

    
    top: number;

    
    bottom: number;

    
    static Circumference(circle: Circle): number;

    
    static CircumferencePoint<O extends Point>(circle: Circle, angle: number, out?: O): O;

    
    static Clone(source: Circle | object): Circle;

    
    static Contains(circle: Circle, x: number, y: number): boolean;

    
    static ContainsPoint(circle: Circle, point: Point | object): boolean;

    
    static ContainsRect(circle: Circle, rect: Rectangle | object): boolean;

    
    static CopyFrom<O extends Circle>(source: Circle, dest: O): O;

    
    static Equals(circle: Circle, toCompare: Circle): boolean;

    
    static GetBounds<O extends Rectangle>(circle: Circle, out?: O): O;

    
    static GetPoint<O extends Point>(circle: Circle, position: number, out?: O): O;

    
    static GetPoints(circle: Circle, quantity: number, stepRate?: number, output?: any[]): Point[];

    
    static Offset<O extends Circle>(circle: O, x: number, y: number): O;

    
    static OffsetPoint<O extends Circle>(circle: O, point: Point | object): O;

    
    static Random<O extends Point>(circle: Circle, out?: O): O;

}

export default Circle;