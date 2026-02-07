

import { ACubismMotion } from './acubismmotion';
import { CubismMotionQueueEntryHandle } from './cubismmotionqueuemanager';


export class CubismMotionQueueEntry {
  
  public constructor() {
    this._autoDelete = false;
    this._motion = null;
    this._available = true;
    this._finished = false;
    this._started = false;
    this._startTimeSeconds = -1.0;
    this._fadeInStartTimeSeconds = 0.0;
    this._endTimeSeconds = -1.0;
    this._stateTimeSeconds = 0.0;
    this._stateWeight = 0.0;
    this._lastEventCheckSeconds = 0.0;
    this._motionQueueEntryHandle = this;
    this._fadeOutSeconds = 0.0;
    this._isTriggeredFadeOut = false;
  }

  
  public release(): void {
    if (this._autoDelete && this._motion) {
      ACubismMotion.delete(this._motion);
    }
  }

  
  public setFadeOut(fadeOutSeconds: number): void {
    this._fadeOutSeconds = fadeOutSeconds;
    this._isTriggeredFadeOut = true;
  }

  
  public startFadeOut(fadeOutSeconds: number, userTimeSeconds: number): void {
    const newEndTimeSeconds: number = userTimeSeconds + fadeOutSeconds;
    this._isTriggeredFadeOut = true;

    if (
      this._endTimeSeconds < 0.0 ||
      newEndTimeSeconds < this._endTimeSeconds
    ) {
      this._endTimeSeconds = newEndTimeSeconds;
    }
  }

  
  public isFinished(): boolean {
    return this._finished;
  }

  
  public isStarted(): boolean {
    return this._started;
  }

  
  public getStartTime(): number {
    return this._startTimeSeconds;
  }

  
  public getFadeInStartTime(): number {
    return this._fadeInStartTimeSeconds;
  }

  
  public getEndTime(): number {
    return this._endTimeSeconds;
  }

  
  public setStartTime(startTime: number): void {
    this._startTimeSeconds = startTime;
  }

  
  public setFadeInStartTime(startTime: number): void {
    this._fadeInStartTimeSeconds = startTime;
  }

  
  public setEndTime(endTime: number): void {
    this._endTimeSeconds = endTime;
  }

  
  public setIsFinished(f: boolean): void {
    this._finished = f;
  }

  
  public setIsStarted(f: boolean): void {
    this._started = f;
  }

  
  public isAvailable(): boolean {
    return this._available;
  }

  
  public setIsAvailable(v: boolean): void {
    this._available = v;
  }

  
  public setState(timeSeconds: number, weight: number): void {
    this._stateTimeSeconds = timeSeconds;
    this._stateWeight = weight;
  }

  
  public getStateTime(): number {
    return this._stateTimeSeconds;
  }

  
  public getStateWeight(): number {
    return this._stateWeight;
  }

  
  public getLastCheckEventSeconds(): number {
    return this._lastEventCheckSeconds;
  }

  
  public setLastCheckEventSeconds(checkSeconds: number): void {
    this._lastEventCheckSeconds = checkSeconds;
  }

  
  public isTriggeredFadeOut(): boolean {
    return this._isTriggeredFadeOut;
  }

  
  public getFadeOutSeconds(): number {
    return this._fadeOutSeconds;
  }

  _autoDelete: boolean;
  _motion: ACubismMotion;

  _available: boolean;
  _finished: boolean;
  _started: boolean;
  _startTimeSeconds: number;
  _fadeInStartTimeSeconds: number;
  _endTimeSeconds: number;
  _stateTimeSeconds: number;
  _stateWeight: number;
  _lastEventCheckSeconds: number;
  private _fadeOutSeconds: number;
  private _isTriggeredFadeOut: boolean;

  _motionQueueEntryHandle: CubismMotionQueueEntryHandle;
}
import * as $ from './cubismmotionqueueentry';
export namespace Live2DCubismFramework {
  export const CubismMotionQueueEntry = $.CubismMotionQueueEntry;
  export type CubismMotionQueueEntry = $.CubismMotionQueueEntry;
}
