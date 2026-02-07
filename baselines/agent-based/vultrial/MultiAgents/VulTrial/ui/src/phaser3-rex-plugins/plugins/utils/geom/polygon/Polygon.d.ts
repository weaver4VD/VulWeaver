import Point from '../point/Point';
import Rectangle from '../rectangle/Rectangle';
import { Vector2Like } from '../types';


declare class Polygon {
    
    constructor(points?: string | number[] | Vector2Like[]);

    
    static Clone(polygon: Polygon): Polygon;

    
    static Contains(polygon: Polygon, x: number, y: number): boolean;

    
    static ContainsPoint(polygon: Polygon, point: Point): boolean;

    
    static Earcut(data: number[], holeIndices?: number[], dimensions?: number): number[];

    
    static GetAABB<O extends Rectangle>(polygon: Polygon, out?: O): O;

    
    static GetNumberArray<O extends number[]>(polygon: Polygon, output?: O): O;

    
    static GetPoints(polygon: Polygon, quantity: number, stepRate?: number, output?: any[]): Point[];

    
    static Perimeter(polygon: Polygon): number;

    
    readonly type: number;

    
    area: number;

    
    points: Point[];

    
    contains(x: number, y: number): boolean;

    
    setTo(points?: string | number[] | Vector2Like[]): this;

    
    calculateArea(): number;

    
    getPoints<O extends Point[]>(quantity: number, stepRate?: number, output?: O): O;

    
    static Reverse<O extends Polygon>(polygon: O): O;

    
    static Simplify<O extends Polygon>(polygon: O, tolerance?: number, highestQuality?: boolean): O;

    
    static Smooth<O extends Polygon>(polygon: O): O;

    
    static Translate<O extends Polygon>(polygon: O, x: number, y: number): O;

}

export default Polygon;