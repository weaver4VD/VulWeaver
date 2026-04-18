

import { CubismModel } from '../model/cubismmodel';
import { ACubismMotion } from './acubismmotion';
import {
  CubismMotionQueueEntryHandle,
  CubismMotionQueueManager
} from './cubismmotionqueuemanager';


export class CubismMotionManager extends CubismMotionQueueManager {
  
  public constructor() {
    super();
    this._currentPriority = 0;
    this._reservePriority = 0;
  }

  
  public getCurrentPriority(): number {
    return this._currentPriority;
  }

  
  public getReservePriority(): number {
    return this._reservePriority;
  }

  
  public setReservePriority(val: number): void {
    this._reservePriority = val;
  }

  
  public startMotionPriority(
    motion: ACubismMotion,
    autoDelete: boolean,
    priority: number
  ): CubismMotionQueueEntryHandle {
    if (priority == this._reservePriority) {
      this._reservePriority = 0;
    }

    this._currentPriority = priority;

    return super.startMotion(motion, autoDelete, this._userTimeSeconds);
  }

  
  public updateMotion(model: CubismModel, deltaTimeSeconds: number): boolean {
    this._userTimeSeconds += deltaTimeSeconds;

    const updated: boolean = super.doUpdateMotion(model, this._userTimeSeconds);

    if (this.isFinished()) {
      this._currentPriority = 0;
    }

    return updated;
  }

  
  public reserveMotion(priority: number): boolean {
    if (
      priority <= this._reservePriority ||
      priority <= this._currentPriority
    ) {
      return false;
    }

    this._reservePriority = priority;

    return true;
  }

  _currentPriority: number;
  _reservePriority: number;
}
import * as $ from './cubismmotionmanager';
export namespace Live2DCubismFramework {
  export const CubismMotionManager = $.CubismMotionManager;
  export type CubismMotionManager = $.CubismMotionManager;
}
