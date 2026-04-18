

import { CubismMath } from '../math/cubismmath';
import { CubismModel } from '../model/cubismmodel';
import { csmString } from '../type/csmstring';
import { csmVector } from '../type/csmvector';
import { CSM_ASSERT } from '../utils/cubismdebug';
import { CubismMotionQueueEntry } from './cubismmotionqueueentry';


export type FinishedMotionCallback = (self: ACubismMotion) => void;


export abstract class ACubismMotion {
  
  public static delete(motion: ACubismMotion): void {
    motion.release();
    motion = null;
  }

  
  public constructor() {
    this._fadeInSeconds = -1.0;
    this._fadeOutSeconds = -1.0;
    this._weight = 1.0;
    this._offsetSeconds = 0.0;
    this._firedEventValues = new csmVector<csmString>();
  }

  
  public release(): void {
    this._weight = 0.0;
  }

  
  public updateParameters(
    model: CubismModel,
    motionQueueEntry: CubismMotionQueueEntry,
    userTimeSeconds: number
  ): void {
    if (!motionQueueEntry.isAvailable() || motionQueueEntry.isFinished()) {
      return;
    }

    if (!motionQueueEntry.isStarted()) {
      motionQueueEntry.setIsStarted(true);
      motionQueueEntry.setStartTime(userTimeSeconds - this._offsetSeconds);
      motionQueueEntry.setFadeInStartTime(userTimeSeconds);

      const duration: number = this.getDuration();

      if (motionQueueEntry.getEndTime() < 0) {
        motionQueueEntry.setEndTime(
          duration <= 0 ? -1 : motionQueueEntry.getStartTime() + duration
        );
      }
    }

    let fadeWeight: number = this._weight;
    const fadeIn: number =
      this._fadeInSeconds == 0.0
        ? 1.0
        : CubismMath.getEasingSine(
            (userTimeSeconds - motionQueueEntry.getFadeInStartTime()) /
              this._fadeInSeconds
          );

    const fadeOut: number =
      this._fadeOutSeconds == 0.0 || motionQueueEntry.getEndTime() < 0.0
        ? 1.0
        : CubismMath.getEasingSine(
            (motionQueueEntry.getEndTime() - userTimeSeconds) /
              this._fadeOutSeconds
          );

    fadeWeight = fadeWeight * fadeIn * fadeOut;

    motionQueueEntry.setState(userTimeSeconds, fadeWeight);

    CSM_ASSERT(0.0 <= fadeWeight && fadeWeight <= 1.0);
    this.doUpdateParameters(
      model,
      userTimeSeconds,
      fadeWeight,
      motionQueueEntry
    );
    if (
      motionQueueEntry.getEndTime() > 0 &&
      motionQueueEntry.getEndTime() < userTimeSeconds
    ) {
      motionQueueEntry.setIsFinished(true);
    }
  }

  
  public setFadeInTime(fadeInSeconds: number): void {
    this._fadeInSeconds = fadeInSeconds;
  }

  
  public setFadeOutTime(fadeOutSeconds: number): void {
    this._fadeOutSeconds = fadeOutSeconds;
  }

  
  public getFadeOutTime(): number {
    return this._fadeOutSeconds;
  }

  
  public getFadeInTime(): number {
    return this._fadeInSeconds;
  }

  
  public setWeight(weight: number): void {
    this._weight = weight;
  }

  
  public getWeight(): number {
    return this._weight;
  }

  
  public getDuration(): number {
    return -1.0;
  }

  
  public getLoopDuration(): number {
    return -1.0;
  }

  
  public setOffsetTime(offsetSeconds: number): void {
    this._offsetSeconds = offsetSeconds;
  }

  
  public getFiredEvent(
    beforeCheckTimeSeconds: number,
    motionTimeSeconds: number
  ): csmVector<csmString> {
    return this._firedEventValues;
  }

  
  public abstract doUpdateParameters(
    model: CubismModel,
    userTimeSeconds: number,
    weight: number,
    motionQueueEntry: CubismMotionQueueEntry
  ): void;

  
  public setFinishedMotionHandler = (
    onFinishedMotionHandler: FinishedMotionCallback
  ) => (this._onFinishedMotion = onFinishedMotionHandler);

  
  public getFinishedMotionHandler = () => this._onFinishedMotion;

  public _fadeInSeconds: number;
  public _fadeOutSeconds: number;
  public _weight: number;
  public _offsetSeconds: number;

  public _firedEventValues: csmVector<csmString>;
  public _onFinishedMotion?: FinishedMotionCallback;
}
import * as $ from './acubismmotion';
export namespace Live2DCubismFramework {
  export const ACubismMotion = $.ACubismMotion;
  export type ACubismMotion = $.ACubismMotion;
  export type FinishedMotionCallback = $.FinishedMotionCallback;
}
