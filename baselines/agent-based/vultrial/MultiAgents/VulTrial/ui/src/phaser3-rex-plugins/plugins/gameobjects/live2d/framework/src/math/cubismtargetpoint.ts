

import { CubismMath } from './cubismmath';

const FrameRate = 30;
const Epsilon = 0.01;


export class CubismTargetPoint {
  
  public constructor() {
    this._faceTargetX = 0.0;
    this._faceTargetY = 0.0;
    this._faceX = 0.0;
    this._faceY = 0.0;
    this._faceVX = 0.0;
    this._faceVY = 0.0;
    this._lastTimeSeconds = 0.0;
    this._userTimeSeconds = 0.0;
  }

  
  public update(deltaTimeSeconds: number): void {
    this._userTimeSeconds += deltaTimeSeconds;
    const faceParamMaxV: number = 40.0 / 10.0;
    const maxV: number = (faceParamMaxV * 1.0) / FrameRate;

    if (this._lastTimeSeconds == 0.0) {
      this._lastTimeSeconds = this._userTimeSeconds;
      return;
    }

    const deltaTimeWeight: number =
      (this._userTimeSeconds - this._lastTimeSeconds) * FrameRate;
    this._lastTimeSeconds = this._userTimeSeconds;
    const timeToMaxSpeed = 0.15;
    const frameToMaxSpeed: number = timeToMaxSpeed * FrameRate;
    const maxA: number = (deltaTimeWeight * maxV) / frameToMaxSpeed;
    const dx: number = this._faceTargetX - this._faceX;
    const dy: number = this._faceTargetY - this._faceY;

    if (CubismMath.abs(dx) <= Epsilon && CubismMath.abs(dy) <= Epsilon) {
      return;
    }
    const d: number = CubismMath.sqrt(dx * dx + dy * dy);
    const vx: number = (maxV * dx) / d;
    const vy: number = (maxV * dy) / d;
    let ax: number = vx - this._faceVX;
    let ay: number = vy - this._faceVY;

    const a: number = CubismMath.sqrt(ax * ax + ay * ay);
    if (a < -maxA || a > maxA) {
      ax *= maxA / a;
      ay *= maxA / a;
    }
    this._faceVX += ax;
    this._faceVY += ay;
    {

      const maxV: number =
        0.5 *
        (CubismMath.sqrt(maxA * maxA + 16.0 * maxA * d - 8.0 * maxA * d) -
          maxA);
      const curV: number = CubismMath.sqrt(
        this._faceVX * this._faceVX + this._faceVY * this._faceVY
      );

      if (curV > maxV) {
        this._faceVX *= maxV / curV;
        this._faceVY *= maxV / curV;
      }
    }

    this._faceX += this._faceVX;
    this._faceY += this._faceVY;
  }

  
  public getX(): number {
    return this._faceX;
  }

  
  public getY(): number {
    return this._faceY;
  }

  
  public set(x: number, y: number): void {
    this._faceTargetX = x;
    this._faceTargetY = y;
  }

  private _faceTargetX: number;
  private _faceTargetY: number;
  private _faceX: number;
  private _faceY: number;
  private _faceVX: number;
  private _faceVY: number;
  private _lastTimeSeconds: number;
  private _userTimeSeconds: number;
}
import * as $ from './cubismtargetpoint';
export namespace Live2DCubismFramework {
  export const CubismTargetPoint = $.CubismTargetPoint;
  export type CubismTargetPoint = $.CubismTargetPoint;
}
