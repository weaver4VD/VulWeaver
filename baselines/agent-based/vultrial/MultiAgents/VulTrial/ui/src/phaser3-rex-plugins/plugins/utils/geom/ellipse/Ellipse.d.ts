import Point from '../point/Point';
import Rectangle from '../rectangle/Rectangle';


declare class Ellipse {
    
    constructor(x?: number, y?: number, width?: number, height?: number);

    
    static Area(ellipse: Ellipse): number;

    
    static Circumference(ellipse: Ellipse): number;

    
    static CircumferencePoint<O extends Point>(ellipse: Ellipse, angle: number, out?: O): O;

    
    static Clone(source: Ellipse): Ellipse;

    
    static Contains(ellipse: Ellipse, x: number, y: number): boolean;

    
    static ContainsPoint(ellipse: Ellipse, point: Point | object): boolean;

    
    static ContainsRect(ellipse: Ellipse, rect: Rectangle | object): boolean;

    
    static CopyFrom<O extends Ellipse>(source: Ellipse, dest: O): O;

    
    readonly type: number;

    
    x: number;

    
    y: number;

    
    width: number;

    
    height: number;

    
    contains(x: number, y: number): boolean;

    
    getPoint<O extends Point>(position: number, out?: O): O;

    
    getPoints<O extends Point[]>(quantity: number, stepRate?: number, output?: O): O;

    
    getRandomPoint<O extends Point>(point?: O): O;

    
    setTo(x: number, y: number, width: number, height: number): this;

    
    setEmpty(): this;

    
    setPosition(x: number, y: number): this;

    
    setSize(width: number, height?: number): this;

    
    isEmpty(): boolean;

    
    getMinorRadius(): number;

    
    getMajorRadius(): number;

    
    left: number;

    
    right: number;

    
    top: number;

    
    bottom: number;

    
    static Equals(ellipse: Ellipse, toCompare: Ellipse): boolean;

    
    static GetBounds<O extends Rectangle>(ellipse: Ellipse, out?: O): O;

    
    static GetPoint<O extends Point>(ellipse: Ellipse, position: number, out?: O): O;

    
    static GetPoints<O extends Point[]>(ellipse: Ellipse, quantity: number, stepRate?: number, out?: O): O;

    
    static Offset<O extends Ellipse>(ellipse: O, x: number, y: number): O;

    
    static OffsetPoint<O extends Ellipse>(ellipse: O, point: Point | object): O;

    
    static Random<O extends Point>(ellipse: Ellipse, out?: O): O;

}

export default Ellipse;