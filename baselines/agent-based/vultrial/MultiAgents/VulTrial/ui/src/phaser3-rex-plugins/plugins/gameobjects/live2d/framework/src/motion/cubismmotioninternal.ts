

import { CubismIdHandle } from '../id/cubismid';
import { csmString } from '../type/csmstring';
import { csmVector } from '../type/csmvector';


export enum CubismMotionCurveTarget {
  CubismMotionCurveTarget_Model,
  CubismMotionCurveTarget_Parameter,
  CubismMotionCurveTarget_PartOpacity
}


export enum CubismMotionSegmentType {
  CubismMotionSegmentType_Linear = 0,
  CubismMotionSegmentType_Bezier = 1,
  CubismMotionSegmentType_Stepped = 2,
  CubismMotionSegmentType_InverseStepped = 3
}


export class CubismMotionPoint {
  time = 0.0;
  value = 0.0;
}


export interface csmMotionSegmentEvaluationFunction {
  (points: CubismMotionPoint[], time: number): number;
}


export class CubismMotionSegment {
  
  public constructor() {
    this.evaluate = null;
    this.basePointIndex = 0;
    this.segmentType = 0;
  }

  evaluate: csmMotionSegmentEvaluationFunction;
  basePointIndex: number;
  segmentType: number;
}


export class CubismMotionCurve {
  public constructor() {
    this.type = CubismMotionCurveTarget.CubismMotionCurveTarget_Model;
    this.segmentCount = 0;
    this.baseSegmentIndex = 0;
    this.fadeInTime = 0.0;
    this.fadeOutTime = 0.0;
  }

  type: CubismMotionCurveTarget;
  id: CubismIdHandle;
  segmentCount: number;
  baseSegmentIndex: number;
  fadeInTime: number;
  fadeOutTime: number;
}


export class CubismMotionEvent {
  fireTime = 0.0;
  value: csmString;
}


export class CubismMotionData {
  public constructor() {
    this.duration = 0.0;
    this.loop = false;
    this.curveCount = 0;
    this.eventCount = 0;
    this.fps = 0.0;

    this.curves = new csmVector<CubismMotionCurve>();
    this.segments = new csmVector<CubismMotionSegment>();
    this.points = new csmVector<CubismMotionPoint>();
    this.events = new csmVector<CubismMotionEvent>();
  }

  duration: number;
  loop: boolean;
  curveCount: number;
  eventCount: number;
  fps: number;
  curves: csmVector<CubismMotionCurve>;
  segments: csmVector<CubismMotionSegment>;
  points: csmVector<CubismMotionPoint>;
  events: csmVector<CubismMotionEvent>;
}
import * as $ from './cubismmotioninternal';
export namespace Live2DCubismFramework {
  export const CubismMotionCurve = $.CubismMotionCurve;
  export type CubismMotionCurve = $.CubismMotionCurve;
  export const CubismMotionCurveTarget = $.CubismMotionCurveTarget;
  export type CubismMotionCurveTarget = $.CubismMotionCurveTarget;
  export const CubismMotionData = $.CubismMotionData;
  export type CubismMotionData = $.CubismMotionData;
  export const CubismMotionEvent = $.CubismMotionEvent;
  export type CubismMotionEvent = $.CubismMotionEvent;
  export const CubismMotionPoint = $.CubismMotionPoint;
  export type CubismMotionPoint = $.CubismMotionPoint;
  export const CubismMotionSegment = $.CubismMotionSegment;
  export type CubismMotionSegment = $.CubismMotionSegment;
  export const CubismMotionSegmentType = $.CubismMotionSegmentType;
  export type CubismMotionSegmentType = $.CubismMotionSegmentType;
  export type csmMotionSegmentEvaluationFunction = $.csmMotionSegmentEvaluationFunction;
}
