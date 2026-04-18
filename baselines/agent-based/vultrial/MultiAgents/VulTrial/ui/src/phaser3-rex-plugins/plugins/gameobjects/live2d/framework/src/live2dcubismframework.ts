

import { CubismIdManager } from './id/cubismidmanager';
import { CubismRenderer } from './rendering/cubismrenderer';
import {
  CSM_ASSERT,
  CubismLogInfo,
  CubismLogWarning
} from './utils/cubismdebug';
import { Value } from './utils/cubismjson';

export function strtod(s: string, endPtr: string[]): number {
  let index = 0;
  for (let i = 1; ; i++) {
    const testC: string = s.slice(i - 1, i);
    if (testC == 'e' || testC == '-' || testC == 'E') {
      continue;
    }

    const test: string = s.substring(0, i);
    const number = Number(test);
    if (isNaN(number)) {
      break;
    }

    index = i;
  }
  let d = parseFloat(s);

  if (isNaN(d)) {
    d = NaN;
  }

  endPtr[0] = s.slice(index);
  return d;
}

let s_isStarted = false;
let s_isInitialized = false;
let s_option: Option = null;
let s_cubismIdManager: CubismIdManager = null;


export const Constant = Object.freeze<Record<string, number>>({
  vertexOffset: 0,
  vertexStep: 2
});

export function csmDelete<T>(address: T): void {
  if (!address) {
    return;
  }

  address = void 0;
}


export class CubismFramework {
  
  public static startUp(option: Option = null): boolean {
    if (s_isStarted) {
      CubismLogInfo('CubismFramework.startUp() is already done.');
      return s_isStarted;
    }

    s_option = option;

    if (s_option != null) {
      Live2DCubismCore.Logging.csmSetLogFunction(s_option.logFunction);
    }

    s_isStarted = true;
    if (s_isStarted) {
      const version: number = Live2DCubismCore.Version.csmGetVersion();
      const major: number = (version & 0xff000000) >> 24;
      const minor: number = (version & 0x00ff0000) >> 16;
      const patch: number = version & 0x0000ffff;
      const versionNumber: number = version;

      CubismLogInfo(
        `Live2D Cubism Core version: {0}.{1}.{2} ({3})`,
        ('00' + major).slice(-2),
        ('00' + minor).slice(-2),
        ('0000' + patch).slice(-4),
        versionNumber
      );
    }

    CubismLogInfo('CubismFramework.startUp() is complete.');

    return s_isStarted;
  }

  
  public static cleanUp(): void {
    s_isStarted = false;
    s_isInitialized = false;
    s_option = null;
    s_cubismIdManager = null;
  }

  
  public static initialize(): void {
    CSM_ASSERT(s_isStarted);
    if (!s_isStarted) {
      CubismLogWarning('CubismFramework is not started.');
      return;
    }
    if (s_isInitialized) {
      CubismLogWarning(
        'CubismFramework.initialize() skipped, already initialized.'
      );
      return;
    }
    Value.staticInitializeNotForClientCall();

    s_cubismIdManager = new CubismIdManager();

    s_isInitialized = true;

    CubismLogInfo('CubismFramework.initialize() is complete.');
  }

  
  public static dispose(): void {
    CSM_ASSERT(s_isStarted);
    if (!s_isStarted) {
      CubismLogWarning('CubismFramework is not started.');
      return;
    }
    if (!s_isInitialized) {
      CubismLogWarning('CubismFramework.dispose() skipped, not initialized.');
      return;
    }

    Value.staticReleaseNotForClientCall();

    s_cubismIdManager.release();
    s_cubismIdManager = null;
    CubismRenderer.staticRelease();

    s_isInitialized = false;

    CubismLogInfo('CubismFramework.dispose() is complete.');
  }

  
  public static isStarted(): boolean {
    return s_isStarted;
  }

  
  public static isInitialized(): boolean {
    return s_isInitialized;
  }

  
  public static coreLogFunction(message: string): void {
    if (!Live2DCubismCore.Logging.csmGetLogFunction()) {
      return;
    }

    Live2DCubismCore.Logging.csmGetLogFunction()(message);
  }

  
  public static getLoggingLevel(): LogLevel {
    if (s_option != null) {
      return s_option.loggingLevel;
    }
    return LogLevel.LogLevel_Off;
  }

  
  public static getIdManager(): CubismIdManager {
    return s_cubismIdManager;
  }

  
  private constructor() {}
}

export class Option {
  logFunction: Live2DCubismCore.csmLogFunction;
  loggingLevel: LogLevel;
}


export enum LogLevel {
  LogLevel_Verbose = 0,
  LogLevel_Debug,
  LogLevel_Info,
  LogLevel_Warning,
  LogLevel_Error,
  LogLevel_Off
}
import * as $ from './live2dcubismframework';
export namespace Live2DCubismFramework {
  export const Constant = $.Constant;
  export const csmDelete = $.csmDelete;
  export const CubismFramework = $.CubismFramework;
  export type CubismFramework = $.CubismFramework;
}
