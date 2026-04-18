

import { ACubismMotion } from './acubismmotion';
import { CubismMotionQueueEntry } from './cubismmotionqueueentry';
import { csmVector, iterator } from '../type/csmvector';
import { CubismModel } from '../model/cubismmodel';
import { csmString } from '../type/csmstring';


export class CubismMotionQueueManager {
  
  public constructor() {
    this._userTimeSeconds = 0.0;
    this._eventCallBack = null;
    this._eventCustomData = null;
    this._motions = new csmVector<CubismMotionQueueEntry>();
  }

  
  public release(): void {
    for (let i = 0; i < this._motions.getSize(); ++i) {
      if (this._motions.at(i)) {
        this._motions.at(i).release();
        this._motions.set(i, null);
      }
    }

    this._motions = null;
  }

  
  public startMotion(
    motion: ACubismMotion,
    autoDelete: boolean,
    userTimeSeconds: number
  ): CubismMotionQueueEntryHandle {
    if (motion == null) {
      return InvalidMotionQueueEntryHandleValue;
    }

    let motionQueueEntry: CubismMotionQueueEntry = null;
    for (let i = 0; i < this._motions.getSize(); ++i) {
      motionQueueEntry = this._motions.at(i);
      if (motionQueueEntry == null) {
        continue;
      }

      motionQueueEntry.setFadeOut(motionQueueEntry._motion.getFadeOutTime());
    }

    motionQueueEntry = new CubismMotionQueueEntry();
    motionQueueEntry._autoDelete = autoDelete;
    motionQueueEntry._motion = motion;

    this._motions.pushBack(motionQueueEntry);

    return motionQueueEntry._motionQueueEntryHandle;
  }

  
  public isFinished(): boolean {

    for (
      let ite: iterator<CubismMotionQueueEntry> = this._motions.begin();
      ite.notEqual(this._motions.end());

    ) {
      let motionQueueEntry: CubismMotionQueueEntry = ite.ptr();

      if (motionQueueEntry == null) {
        ite = this._motions.erase(ite);
        continue;
      }

      const motion: ACubismMotion = motionQueueEntry._motion;

      if (motion == null) {
        motionQueueEntry.release();
        motionQueueEntry = null;
        ite = this._motions.erase(ite);
        continue;
      }
      if (!motionQueueEntry.isFinished()) {
        return false;
      } else {
        ite.preIncrement();
      }
    }

    return true;
  }

  
  public isFinishedByHandle(
    motionQueueEntryNumber: CubismMotionQueueEntryHandle
  ): boolean {
    for (
      let ite: iterator<CubismMotionQueueEntry> = this._motions.begin();
      ite.notEqual(this._motions.end());
      ite.increment()
    ) {
      const motionQueueEntry: CubismMotionQueueEntry = ite.ptr();

      if (motionQueueEntry == null) {
        continue;
      }

      if (
        motionQueueEntry._motionQueueEntryHandle == motionQueueEntryNumber &&
        !motionQueueEntry.isFinished()
      ) {
        return false;
      }
    }
    return true;
  }

  
  public stopAllMotions(): void {

    for (
      let ite: iterator<CubismMotionQueueEntry> = this._motions.begin();
      ite.notEqual(this._motions.end());

    ) {
      let motionQueueEntry: CubismMotionQueueEntry = ite.ptr();

      if (motionQueueEntry == null) {
        ite = this._motions.erase(ite);

        continue;
      }
      motionQueueEntry.release();
      motionQueueEntry = null;
      ite = this._motions.erase(ite);
    }
  }

  
  public getCubismMotionQueueEntry(
    motionQueueEntryNumber: any
  ): CubismMotionQueueEntry {
    for (
      let ite: iterator<CubismMotionQueueEntry> = this._motions.begin();
      ite.notEqual(this._motions.end());
      ite.preIncrement()
    ) {
      const motionQueueEntry: CubismMotionQueueEntry = ite.ptr();

      if (motionQueueEntry == null) {
        continue;
      }

      if (motionQueueEntry._motionQueueEntryHandle == motionQueueEntryNumber) {
        return motionQueueEntry;
      }
    }

    return null;
  }

  
  public setEventCallback(
    callback: CubismMotionEventFunction,
    customData: any = null
  ): void {
    this._eventCallBack = callback;
    this._eventCustomData = customData;
  }

  
  public doUpdateMotion(model: CubismModel, userTimeSeconds: number): boolean {
    let updated = false;

    for (
      let ite: iterator<CubismMotionQueueEntry> = this._motions.begin();
      ite.notEqual(this._motions.end());

    ) {
      let motionQueueEntry: CubismMotionQueueEntry = ite.ptr();

      if (motionQueueEntry == null) {
        ite = this._motions.erase(ite);
        continue;
      }

      const motion: ACubismMotion = motionQueueEntry._motion;

      if (motion == null) {
        motionQueueEntry.release();
        motionQueueEntry = null;
        ite = this._motions.erase(ite);

        continue;
      }
      motion.updateParameters(model, motionQueueEntry, userTimeSeconds);
      updated = true;
      const firedList: csmVector<csmString> = motion.getFiredEvent(
        motionQueueEntry.getLastCheckEventSeconds() -
          motionQueueEntry.getStartTime(),
        userTimeSeconds - motionQueueEntry.getStartTime()
      );

      for (let i = 0; i < firedList.getSize(); ++i) {
        this._eventCallBack(this, firedList.at(i), this._eventCustomData);
      }

      motionQueueEntry.setLastCheckEventSeconds(userTimeSeconds);
      if (motionQueueEntry.isFinished()) {
        motionQueueEntry.release();
        motionQueueEntry = null;
        ite = this._motions.erase(ite);
      } else {
        if (motionQueueEntry.isTriggeredFadeOut()) {
          motionQueueEntry.startFadeOut(
            motionQueueEntry.getFadeOutSeconds(),
            userTimeSeconds
          );
        }
        ite.preIncrement();
      }
    }

    return updated;
  }
  _userTimeSeconds: number;

  _motions: csmVector<CubismMotionQueueEntry>;
  _eventCallBack: CubismMotionEventFunction;
  _eventCustomData: any;
}


export interface CubismMotionEventFunction {
  (
    caller: CubismMotionQueueManager,
    eventValue: csmString,
    customData: any
  ): void;
}


export declare type CubismMotionQueueEntryHandle = any;
export const InvalidMotionQueueEntryHandleValue: CubismMotionQueueEntryHandle = -1;
import * as $ from './cubismmotionqueuemanager';
export namespace Live2DCubismFramework {
  export const CubismMotionQueueManager = $.CubismMotionQueueManager;
  export type CubismMotionQueueManager = $.CubismMotionQueueManager;
  export const InvalidMotionQueueEntryHandleValue =
    $.InvalidMotionQueueEntryHandleValue;
  export type CubismMotionQueueEntryHandle = $.CubismMotionQueueEntryHandle;
  export type CubismMotionEventFunction = $.CubismMotionEventFunction;
}
