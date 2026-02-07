

import { CubismIdHandle } from '../id/cubismid';
import { CubismFramework } from '../live2dcubismframework';
import { CubismMath } from '../math/cubismmath';
import { CubismModel } from '../model/cubismmodel';
import { csmString } from '../type/csmstring';
import { csmVector } from '../type/csmvector';
import {
  CSM_ASSERT,
  CubismLogDebug,
  CubismLogWarning
} from '../utils/cubismdebug';
import { ACubismMotion, FinishedMotionCallback } from './acubismmotion';
import {
  CubismMotionCurve,
  CubismMotionCurveTarget,
  CubismMotionData,
  CubismMotionEvent,
  CubismMotionPoint,
  CubismMotionSegment,
  CubismMotionSegmentType
} from './cubismmotioninternal';
import { CubismMotionJson, EvaluationOptionFlag } from './cubismmotionjson';
import { CubismMotionQueueEntry } from './cubismmotionqueueentry';

const EffectNameEyeBlink = 'EyeBlink';
const EffectNameLipSync = 'LipSync';
const TargetNameModel = 'Model';
const TargetNameParameter = 'Parameter';
const TargetNamePartOpacity = 'PartOpacity';


const UseOldBeziersCurveMotion = false;

function lerpPoints(
  a: CubismMotionPoint,
  b: CubismMotionPoint,
  t: number
): CubismMotionPoint {
  const result: CubismMotionPoint = new CubismMotionPoint();

  result.time = a.time + (b.time - a.time) * t;
  result.value = a.value + (b.value - a.value) * t;

  return result;
}

function linearEvaluate(points: CubismMotionPoint[], time: number): number {
  let t: number = (time - points[0].time) / (points[1].time - points[0].time);

  if (t < 0.0) {
    t = 0.0;
  }

  return points[0].value + (points[1].value - points[0].value) * t;
}

function bezierEvaluate(points: CubismMotionPoint[], time: number): number {
  let t: number = (time - points[0].time) / (points[3].time - points[0].time);

  if (t < 0.0) {
    t = 0.0;
  }

  const p01: CubismMotionPoint = lerpPoints(points[0], points[1], t);
  const p12: CubismMotionPoint = lerpPoints(points[1], points[2], t);
  const p23: CubismMotionPoint = lerpPoints(points[2], points[3], t);

  const p012: CubismMotionPoint = lerpPoints(p01, p12, t);
  const p123: CubismMotionPoint = lerpPoints(p12, p23, t);

  return lerpPoints(p012, p123, t).value;
}

function bezierEvaluateBinarySearch(
  points: CubismMotionPoint[],
  time: number
): number {
  const x_error = 0.01;

  const x: number = time;
  let x1: number = points[0].time;
  let x2: number = points[3].time;
  let cx1: number = points[1].time;
  let cx2: number = points[2].time;

  let ta = 0.0;
  let tb = 1.0;
  let t = 0.0;
  let i = 0;

  for (let var33 = true; i < 20; ++i) {
    if (x < x1 + x_error) {
      t = ta;
      break;
    }

    if (x2 - x_error < x) {
      t = tb;
      break;
    }

    let centerx: number = (cx1 + cx2) * 0.5;
    cx1 = (x1 + cx1) * 0.5;
    cx2 = (x2 + cx2) * 0.5;
    const ctrlx12: number = (cx1 + centerx) * 0.5;
    const ctrlx21: number = (cx2 + centerx) * 0.5;
    centerx = (ctrlx12 + ctrlx21) * 0.5;
    if (x < centerx) {
      tb = (ta + tb) * 0.5;
      if (centerx - x_error < x) {
        t = tb;
        break;
      }

      x2 = centerx;
      cx2 = ctrlx12;
    } else {
      ta = (ta + tb) * 0.5;
      if (x < centerx + x_error) {
        t = ta;
        break;
      }

      x1 = centerx;
      cx1 = ctrlx21;
    }
  }

  if (i == 20) {
    t = (ta + tb) * 0.5;
  }

  if (t < 0.0) {
    t = 0.0;
  }
  if (t > 1.0) {
    t = 1.0;
  }

  const p01: CubismMotionPoint = lerpPoints(points[0], points[1], t);
  const p12: CubismMotionPoint = lerpPoints(points[1], points[2], t);
  const p23: CubismMotionPoint = lerpPoints(points[2], points[3], t);

  const p012: CubismMotionPoint = lerpPoints(p01, p12, t);
  const p123: CubismMotionPoint = lerpPoints(p12, p23, t);

  return lerpPoints(p012, p123, t).value;
}

function bezierEvaluateCardanoInterpretation(
  points: CubismMotionPoint[],
  time: number
): number {
  const x: number = time;
  const x1: number = points[0].time;
  const x2: number = points[3].time;
  const cx1: number = points[1].time;
  const cx2: number = points[2].time;

  const a: number = x2 - 3.0 * cx2 + 3.0 * cx1 - x1;
  const b: number = 3.0 * cx2 - 6.0 * cx1 + 3.0 * x1;
  const c: number = 3.0 * cx1 - 3.0 * x1;
  const d: number = x1 - x;

  const t: number = CubismMath.cardanoAlgorithmForBezier(a, b, c, d);

  const p01: CubismMotionPoint = lerpPoints(points[0], points[1], t);
  const p12: CubismMotionPoint = lerpPoints(points[1], points[2], t);
  const p23: CubismMotionPoint = lerpPoints(points[2], points[3], t);

  const p012: CubismMotionPoint = lerpPoints(p01, p12, t);
  const p123: CubismMotionPoint = lerpPoints(p12, p23, t);

  return lerpPoints(p012, p123, t).value;
}

function steppedEvaluate(points: CubismMotionPoint[], time: number): number {
  return points[0].value;
}

function inverseSteppedEvaluate(
  points: CubismMotionPoint[],
  time: number
): number {
  return points[1].value;
}

function evaluateCurve(
  motionData: CubismMotionData,
  index: number,
  time: number
): number {
  const curve: CubismMotionCurve = motionData.curves.at(index);

  let target = -1;
  const totalSegmentCount: number = curve.baseSegmentIndex + curve.segmentCount;
  let pointPosition = 0;
  for (let i: number = curve.baseSegmentIndex; i < totalSegmentCount; ++i) {
    pointPosition =
      motionData.segments.at(i).basePointIndex +
      (motionData.segments.at(i).segmentType ==
      CubismMotionSegmentType.CubismMotionSegmentType_Bezier
        ? 3
        : 1);
    if (motionData.points.at(pointPosition).time > time) {
      target = i;
      break;
    }
  }

  if (target == -1) {
    return motionData.points.at(pointPosition).value;
  }

  const segment: CubismMotionSegment = motionData.segments.at(target);

  return segment.evaluate(motionData.points.get(segment.basePointIndex), time);
}


export class CubismMotion extends ACubismMotion {
  
  public static create(
    buffer: ArrayBuffer,
    size: number,
    onFinishedMotionHandler?: FinishedMotionCallback
  ): CubismMotion {
    const ret = new CubismMotion();

    ret.parse(buffer, size);
    ret._sourceFrameRate = ret._motionData.fps;
    ret._loopDurationSeconds = ret._motionData.duration;
    ret._onFinishedMotion = onFinishedMotionHandler;
    return ret;
  }

  
  public doUpdateParameters(
    model: CubismModel,
    userTimeSeconds: number,
    fadeWeight: number,
    motionQueueEntry: CubismMotionQueueEntry
  ): void {
    if (this._modelCurveIdEyeBlink == null) {
      this._modelCurveIdEyeBlink = CubismFramework.getIdManager().getId(
        EffectNameEyeBlink
      );
    }

    if (this._modelCurveIdLipSync == null) {
      this._modelCurveIdLipSync = CubismFramework.getIdManager().getId(
        EffectNameLipSync
      );
    }

    let timeOffsetSeconds: number =
      userTimeSeconds - motionQueueEntry.getStartTime();

    if (timeOffsetSeconds < 0.0) {
      timeOffsetSeconds = 0.0;
    }

    let lipSyncValue: number = Number.MAX_VALUE;
    let eyeBlinkValue: number = Number.MAX_VALUE;
    const MaxTargetSize = 64;
    let lipSyncFlags = 0;
    let eyeBlinkFlags = 0;
    if (this._eyeBlinkParameterIds.getSize() > MaxTargetSize) {
      CubismLogDebug(
        'too many eye blink targets : {0}',
        this._eyeBlinkParameterIds.getSize()
      );
    }
    if (this._lipSyncParameterIds.getSize() > MaxTargetSize) {
      CubismLogDebug(
        'too many lip sync targets : {0}',
        this._lipSyncParameterIds.getSize()
      );
    }

    const tmpFadeIn: number =
      this._fadeInSeconds <= 0.0
        ? 1.0
        : CubismMath.getEasingSine(
            (userTimeSeconds - motionQueueEntry.getFadeInStartTime()) /
              this._fadeInSeconds
          );

    const tmpFadeOut: number =
      this._fadeOutSeconds <= 0.0 || motionQueueEntry.getEndTime() < 0.0
        ? 1.0
        : CubismMath.getEasingSine(
            (motionQueueEntry.getEndTime() - userTimeSeconds) /
              this._fadeOutSeconds
          );
    let value: number;
    let c: number, parameterIndex: number;
    let time: number = timeOffsetSeconds;

    if (this._isLoop) {
      while (time > this._motionData.duration) {
        time -= this._motionData.duration;
      }
    }

    const curves: csmVector<CubismMotionCurve> = this._motionData.curves;
    for (
      c = 0;
      c < this._motionData.curveCount &&
      curves.at(c).type ==
        CubismMotionCurveTarget.CubismMotionCurveTarget_Model;
      ++c
    ) {
      value = evaluateCurve(this._motionData, c, time);

      if (curves.at(c).id == this._modelCurveIdEyeBlink) {
        eyeBlinkValue = value;
      } else if (curves.at(c).id == this._modelCurveIdLipSync) {
        lipSyncValue = value;
      }
    }

    let parameterMotionCurveCount = 0;

    for (
      ;
      c < this._motionData.curveCount &&
      curves.at(c).type ==
        CubismMotionCurveTarget.CubismMotionCurveTarget_Parameter;
      ++c
    ) {
      parameterMotionCurveCount++;
      parameterIndex = model.getParameterIndex(curves.at(c).id);
      if (parameterIndex == -1) {
        continue;
      }

      const sourceValue: number = model.getParameterValueByIndex(
        parameterIndex
      );
      value = evaluateCurve(this._motionData, c, time);

      if (eyeBlinkValue != Number.MAX_VALUE) {
        for (
          let i = 0;
          i < this._eyeBlinkParameterIds.getSize() && i < MaxTargetSize;
          ++i
        ) {
          if (this._eyeBlinkParameterIds.at(i) == curves.at(c).id) {
            value *= eyeBlinkValue;
            eyeBlinkFlags |= 1 << i;
            break;
          }
        }
      }

      if (lipSyncValue != Number.MAX_VALUE) {
        for (
          let i = 0;
          i < this._lipSyncParameterIds.getSize() && i < MaxTargetSize;
          ++i
        ) {
          if (this._lipSyncParameterIds.at(i) == curves.at(c).id) {
            value += lipSyncValue;
            lipSyncFlags |= 1 << i;
            break;
          }
        }
      }

      let v: number;
      if (curves.at(c).fadeInTime < 0.0 && curves.at(c).fadeOutTime < 0.0) {
        v = sourceValue + (value - sourceValue) * fadeWeight;
      } else {
        let fin: number;
        let fout: number;

        if (curves.at(c).fadeInTime < 0.0) {
          fin = tmpFadeIn;
        } else {
          fin =
            curves.at(c).fadeInTime == 0.0
              ? 1.0
              : CubismMath.getEasingSine(
                  (userTimeSeconds - motionQueueEntry.getFadeInStartTime()) /
                    curves.at(c).fadeInTime
                );
        }

        if (curves.at(c).fadeOutTime < 0.0) {
          fout = tmpFadeOut;
        } else {
          fout =
            curves.at(c).fadeOutTime == 0.0 ||
            motionQueueEntry.getEndTime() < 0.0
              ? 1.0
              : CubismMath.getEasingSine(
                  (motionQueueEntry.getEndTime() - userTimeSeconds) /
                    curves.at(c).fadeOutTime
                );
        }

        const paramWeight: number = this._weight * fin * fout;
        v = sourceValue + (value - sourceValue) * paramWeight;
      }

      model.setParameterValueByIndex(parameterIndex, v, 1.0);
    }

    {
      if (eyeBlinkValue != Number.MAX_VALUE) {
        for (
          let i = 0;
          i < this._eyeBlinkParameterIds.getSize() && i < MaxTargetSize;
          ++i
        ) {
          const sourceValue: number = model.getParameterValueById(
            this._eyeBlinkParameterIds.at(i)
          );
          if ((eyeBlinkFlags >> i) & 0x01) {
            continue;
          }

          const v: number =
            sourceValue + (eyeBlinkValue - sourceValue) * fadeWeight;

          model.setParameterValueById(this._eyeBlinkParameterIds.at(i), v);
        }
      }

      if (lipSyncValue != Number.MAX_VALUE) {
        for (
          let i = 0;
          i < this._lipSyncParameterIds.getSize() && i < MaxTargetSize;
          ++i
        ) {
          const sourceValue: number = model.getParameterValueById(
            this._lipSyncParameterIds.at(i)
          );
          if ((lipSyncFlags >> i) & 0x01) {
            continue;
          }

          const v: number =
            sourceValue + (lipSyncValue - sourceValue) * fadeWeight;

          model.setParameterValueById(this._lipSyncParameterIds.at(i), v);
        }
      }
    }

    for (
      ;
      c < this._motionData.curveCount &&
      curves.at(c).type ==
        CubismMotionCurveTarget.CubismMotionCurveTarget_PartOpacity;
      ++c
    ) {
      parameterIndex = model.getParameterIndex(curves.at(c).id);
      if (parameterIndex == -1) {
        continue;
      }
      value = evaluateCurve(this._motionData, c, time);

      model.setParameterValueByIndex(parameterIndex, value);
    }

    if (timeOffsetSeconds >= this._motionData.duration) {
      if (this._isLoop) {
        motionQueueEntry.setStartTime(userTimeSeconds);
        if (this._isLoopFadeIn) {
          motionQueueEntry.setFadeInStartTime(userTimeSeconds);
        }
      } else {
        if (this._onFinishedMotion) {
          this._onFinishedMotion(this);
        }

        motionQueueEntry.setIsFinished(true);
      }
    }
    this._lastWeight = fadeWeight;
  }

  
  public setIsLoop(loop: boolean): void {
    this._isLoop = loop;
  }

  
  public isLoop(): boolean {
    return this._isLoop;
  }

  
  public setIsLoopFadeIn(loopFadeIn: boolean): void {
    this._isLoopFadeIn = loopFadeIn;
  }

  
  public isLoopFadeIn(): boolean {
    return this._isLoopFadeIn;
  }

  
  public getDuration(): number {
    return this._isLoop ? -1.0 : this._loopDurationSeconds;
  }

  
  public getLoopDuration(): number {
    return this._loopDurationSeconds;
  }

  
  public setParameterFadeInTime(
    parameterId: CubismIdHandle,
    value: number
  ): void {
    const curves: csmVector<CubismMotionCurve> = this._motionData.curves;

    for (let i = 0; i < this._motionData.curveCount; ++i) {
      if (parameterId == curves.at(i).id) {
        curves.at(i).fadeInTime = value;
        return;
      }
    }
  }

  
  public setParameterFadeOutTime(
    parameterId: CubismIdHandle,
    value: number
  ): void {
    const curves: csmVector<CubismMotionCurve> = this._motionData.curves;

    for (let i = 0; i < this._motionData.curveCount; ++i) {
      if (parameterId == curves.at(i).id) {
        curves.at(i).fadeOutTime = value;
        return;
      }
    }
  }

  
  public getParameterFadeInTime(parameterId: CubismIdHandle): number {
    const curves: csmVector<CubismMotionCurve> = this._motionData.curves;

    for (let i = 0; i < this._motionData.curveCount; ++i) {
      if (parameterId == curves.at(i).id) {
        return curves.at(i).fadeInTime;
      }
    }

    return -1;
  }

  
  public getParameterFadeOutTime(parameterId: CubismIdHandle): number {
    const curves: csmVector<CubismMotionCurve> = this._motionData.curves;

    for (let i = 0; i < this._motionData.curveCount; ++i) {
      if (parameterId == curves.at(i).id) {
        return curves.at(i).fadeOutTime;
      }
    }

    return -1;
  }

  
  public setEffectIds(
    eyeBlinkParameterIds: csmVector<CubismIdHandle>,
    lipSyncParameterIds: csmVector<CubismIdHandle>
  ): void {
    this._eyeBlinkParameterIds = eyeBlinkParameterIds;
    this._lipSyncParameterIds = lipSyncParameterIds;
  }

  
  public constructor() {
    super();
    this._sourceFrameRate = 30.0;
    this._loopDurationSeconds = -1.0;
    this._isLoop = false;
    this._isLoopFadeIn = true;
    this._lastWeight = 0.0;
    this._motionData = null;
    this._modelCurveIdEyeBlink = null;
    this._modelCurveIdLipSync = null;
    this._eyeBlinkParameterIds = null;
    this._lipSyncParameterIds = null;
  }

  
  public release(): void {
    this._motionData = void 0;
    this._motionData = null;
  }

  
  public parse(motionJson: ArrayBuffer, size: number): void {
    this._motionData = new CubismMotionData();

    let json: CubismMotionJson = new CubismMotionJson(motionJson, size);

    this._motionData.duration = json.getMotionDuration();
    this._motionData.loop = json.isMotionLoop();
    this._motionData.curveCount = json.getMotionCurveCount();
    this._motionData.fps = json.getMotionFps();
    this._motionData.eventCount = json.getEventCount();

    const areBeziersRestructed: boolean = json.getEvaluationOptionFlag(
      EvaluationOptionFlag.EvaluationOptionFlag_AreBeziersRistricted
    );

    if (json.isExistMotionFadeInTime()) {
      this._fadeInSeconds =
        json.getMotionFadeInTime() < 0.0 ? 1.0 : json.getMotionFadeInTime();
    } else {
      this._fadeInSeconds = 1.0;
    }

    if (json.isExistMotionFadeOutTime()) {
      this._fadeOutSeconds =
        json.getMotionFadeOutTime() < 0.0 ? 1.0 : json.getMotionFadeOutTime();
    } else {
      this._fadeOutSeconds = 1.0;
    }

    this._motionData.curves.updateSize(
      this._motionData.curveCount,
      CubismMotionCurve,
      true
    );
    this._motionData.segments.updateSize(
      json.getMotionTotalSegmentCount(),
      CubismMotionSegment,
      true
    );
    this._motionData.points.updateSize(
      json.getMotionTotalPointCount(),
      CubismMotionPoint,
      true
    );
    this._motionData.events.updateSize(
      this._motionData.eventCount,
      CubismMotionEvent,
      true
    );

    let totalPointCount = 0;
    let totalSegmentCount = 0;
    for (
      let curveCount = 0;
      curveCount < this._motionData.curveCount;
      ++curveCount
    ) {
      if (json.getMotionCurveTarget(curveCount) == TargetNameModel) {
        this._motionData.curves.at(curveCount).type =
          CubismMotionCurveTarget.CubismMotionCurveTarget_Model;
      } else if (json.getMotionCurveTarget(curveCount) == TargetNameParameter) {
        this._motionData.curves.at(curveCount).type =
          CubismMotionCurveTarget.CubismMotionCurveTarget_Parameter;
      } else if (
        json.getMotionCurveTarget(curveCount) == TargetNamePartOpacity
      ) {
        this._motionData.curves.at(curveCount).type =
          CubismMotionCurveTarget.CubismMotionCurveTarget_PartOpacity;
      } else {
        CubismLogWarning(
          'Warning : Unable to get segment type from Curve! The number of "CurveCount" may be incorrect!'
        );
      }

      this._motionData.curves.at(curveCount).id = json.getMotionCurveId(
        curveCount
      );

      this._motionData.curves.at(
        curveCount
      ).baseSegmentIndex = totalSegmentCount;

      this._motionData.curves.at(
        curveCount
      ).fadeInTime = json.isExistMotionCurveFadeInTime(curveCount)
        ? json.getMotionCurveFadeInTime(curveCount)
        : -1.0;
      this._motionData.curves.at(
        curveCount
      ).fadeOutTime = json.isExistMotionCurveFadeOutTime(curveCount)
        ? json.getMotionCurveFadeOutTime(curveCount)
        : -1.0;
      for (
        let segmentPosition = 0;
        segmentPosition < json.getMotionCurveSegmentCount(curveCount);

      ) {
        if (segmentPosition == 0) {
          this._motionData.segments.at(
            totalSegmentCount
          ).basePointIndex = totalPointCount;

          this._motionData.points.at(
            totalPointCount
          ).time = json.getMotionCurveSegment(curveCount, segmentPosition);
          this._motionData.points.at(
            totalPointCount
          ).value = json.getMotionCurveSegment(curveCount, segmentPosition + 1);

          totalPointCount += 1;
          segmentPosition += 2;
        } else {
          this._motionData.segments.at(totalSegmentCount).basePointIndex =
            totalPointCount - 1;
        }

        const segment: number = json.getMotionCurveSegment(
          curveCount,
          segmentPosition
        );
        switch (segment) {
          case CubismMotionSegmentType.CubismMotionSegmentType_Linear: {
            this._motionData.segments.at(totalSegmentCount).segmentType =
              CubismMotionSegmentType.CubismMotionSegmentType_Linear;
            this._motionData.segments.at(
              totalSegmentCount
            ).evaluate = linearEvaluate;

            this._motionData.points.at(
              totalPointCount
            ).time = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 1
            );
            this._motionData.points.at(
              totalPointCount
            ).value = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 2
            );

            totalPointCount += 1;
            segmentPosition += 3;

            break;
          }
          case CubismMotionSegmentType.CubismMotionSegmentType_Bezier: {
            this._motionData.segments.at(totalSegmentCount).segmentType =
              CubismMotionSegmentType.CubismMotionSegmentType_Bezier;

            if (areBeziersRestructed || UseOldBeziersCurveMotion) {
              this._motionData.segments.at(
                totalSegmentCount
              ).evaluate = bezierEvaluate;
            } else {
              this._motionData.segments.at(
                totalSegmentCount
              ).evaluate = bezierEvaluateCardanoInterpretation;
            }

            this._motionData.points.at(
              totalPointCount
            ).time = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 1
            );
            this._motionData.points.at(
              totalPointCount
            ).value = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 2
            );

            this._motionData.points.at(
              totalPointCount + 1
            ).time = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 3
            );
            this._motionData.points.at(
              totalPointCount + 1
            ).value = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 4
            );

            this._motionData.points.at(
              totalPointCount + 2
            ).time = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 5
            );
            this._motionData.points.at(
              totalPointCount + 2
            ).value = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 6
            );

            totalPointCount += 3;
            segmentPosition += 7;

            break;
          }

          case CubismMotionSegmentType.CubismMotionSegmentType_Stepped: {
            this._motionData.segments.at(totalSegmentCount).segmentType =
              CubismMotionSegmentType.CubismMotionSegmentType_Stepped;
            this._motionData.segments.at(
              totalSegmentCount
            ).evaluate = steppedEvaluate;

            this._motionData.points.at(
              totalPointCount
            ).time = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 1
            );
            this._motionData.points.at(
              totalPointCount
            ).value = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 2
            );

            totalPointCount += 1;
            segmentPosition += 3;

            break;
          }

          case CubismMotionSegmentType.CubismMotionSegmentType_InverseStepped: {
            this._motionData.segments.at(totalSegmentCount).segmentType =
              CubismMotionSegmentType.CubismMotionSegmentType_InverseStepped;
            this._motionData.segments.at(
              totalSegmentCount
            ).evaluate = inverseSteppedEvaluate;

            this._motionData.points.at(
              totalPointCount
            ).time = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 1
            );
            this._motionData.points.at(
              totalPointCount
            ).value = json.getMotionCurveSegment(
              curveCount,
              segmentPosition + 2
            );

            totalPointCount += 1;
            segmentPosition += 3;

            break;
          }
          default: {
            CSM_ASSERT(0);
            break;
          }
        }

        ++this._motionData.curves.at(curveCount).segmentCount;
        ++totalSegmentCount;
      }
    }

    for (
      let userdatacount = 0;
      userdatacount < json.getEventCount();
      ++userdatacount
    ) {
      this._motionData.events.at(userdatacount).fireTime = json.getEventTime(
        userdatacount
      );
      this._motionData.events.at(userdatacount).value = json.getEventValue(
        userdatacount
      );
    }

    json.release();
    json = void 0;
    json = null;
  }

  
  public getFiredEvent(
    beforeCheckTimeSeconds: number,
    motionTimeSeconds: number
  ): csmVector<csmString> {
    this._firedEventValues.updateSize(0);
    for (let u = 0; u < this._motionData.eventCount; ++u) {
      if (
        this._motionData.events.at(u).fireTime > beforeCheckTimeSeconds &&
        this._motionData.events.at(u).fireTime <= motionTimeSeconds
      ) {
        this._firedEventValues.pushBack(
          new csmString(this._motionData.events.at(u).value.s)
        );
      }
    }

    return this._firedEventValues;
  }

  public _sourceFrameRate: number;
  public _loopDurationSeconds: number;
  public _isLoop: boolean;
  public _isLoopFadeIn: boolean;
  public _lastWeight: number;

  public _motionData: CubismMotionData;

  public _eyeBlinkParameterIds: csmVector<CubismIdHandle>;
  public _lipSyncParameterIds: csmVector<CubismIdHandle>;

  public _modelCurveIdEyeBlink: CubismIdHandle;
  public _modelCurveIdLipSync: CubismIdHandle;
}
import * as $ from './cubismmotion';
export namespace Live2DCubismFramework {
  export const CubismMotion = $.CubismMotion;
  export type CubismMotion = $.CubismMotion;
}
