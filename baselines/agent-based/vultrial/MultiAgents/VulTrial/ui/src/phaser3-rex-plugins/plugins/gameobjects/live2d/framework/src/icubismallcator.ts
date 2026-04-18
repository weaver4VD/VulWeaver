


export abstract class ICubismAllocator {
  
  public abstract allocate(size: number): any;

  
  public abstract deallocate(memory: any): void;

  
  public abstract allocateAligned(size: number, alignment: number): any;

  
  public abstract deallocateAligned(alignedMemory: any): void;
}
import * as $ from './icubismallcator';
export namespace Live2DCubismFramework {
  export const ICubismAllocator = $.ICubismAllocator;
  export type ICubismAllocator = $.ICubismAllocator;
}
