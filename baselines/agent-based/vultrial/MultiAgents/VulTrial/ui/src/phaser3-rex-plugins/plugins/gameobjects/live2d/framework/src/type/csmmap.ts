

import { CubismLogDebug } from '../utils/cubismdebug';


export class csmPair<_KeyT, _ValT> {
  
  public constructor(key?: _KeyT, value?: _ValT) {
    this.first = key == undefined ? null : key;

    this.second = value == undefined ? null : value;
  }

  public first: _KeyT;
  public second: _ValT;
}


export class csmMap<_KeyT, _ValT> {
  
  public constructor(size?: number) {
    if (size != undefined) {
      if (size < 1) {
        this._keyValues = [];
        this._dummyValue = null;
        this._size = 0;
      } else {
        this._keyValues = new Array(size);
        this._size = size;
      }
    } else {
      this._keyValues = [];
      this._dummyValue = null;
      this._size = 0;
    }
  }

  
  public release() {
    this.clear();
  }

  
  public appendKey(key: _KeyT): void {
    this.prepareCapacity(this._size + 1, false);

    this._keyValues[this._size] = new csmPair<_KeyT, _ValT>(key);
    this._size += 1;
  }

  
  public getValue(key: _KeyT): _ValT {
    let found = -1;

    for (let i = 0; i < this._size; i++) {
      if (this._keyValues[i].first == key) {
        found = i;
        break;
      }
    }

    if (found >= 0) {
      return this._keyValues[found].second;
    } else {
      this.appendKey(key);
      return this._keyValues[this._size - 1].second;
    }
  }

  
  public setValue(key: _KeyT, value: _ValT): void {
    let found = -1;

    for (let i = 0; i < this._size; i++) {
      if (this._keyValues[i].first == key) {
        found = i;
        break;
      }
    }

    if (found >= 0) {
      this._keyValues[found].second = value;
    } else {
      this.appendKey(key);
      this._keyValues[this._size - 1].second = value;
    }
  }

  
  public isExist(key: _KeyT): boolean {
    for (let i = 0; i < this._size; i++) {
      if (this._keyValues[i].first == key) {
        return true;
      }
    }
    return false;
  }

  
  public clear(): void {
    this._keyValues = void 0;
    this._keyValues = null;
    this._keyValues = [];

    this._size = 0;
  }

  
  public getSize(): number {
    return this._size;
  }

  
  public prepareCapacity(newSize: number, fitToSize: boolean): void {
    if (newSize > this._keyValues.length) {
      if (this._keyValues.length == 0) {
        if (!fitToSize && newSize < csmMap.DefaultSize)
          newSize = csmMap.DefaultSize;
        this._keyValues.length = newSize;
      } else {
        if (!fitToSize && newSize < this._keyValues.length * 2)
          newSize = this._keyValues.length * 2;
        this._keyValues.length = newSize;
      }
    }
  }

  
  public begin(): iterator<_KeyT, _ValT> {
    const ite: iterator<_KeyT, _ValT> = new iterator<_KeyT, _ValT>(this, 0);
    return ite;
  }

  
  public end(): iterator<_KeyT, _ValT> {
    const ite: iterator<_KeyT, _ValT> = new iterator<_KeyT, _ValT>(
      this,
      this._size
    );
    return ite;
  }

  
  public erase(ite: iterator<_KeyT, _ValT>): iterator<_KeyT, _ValT> {
    const index: number = ite._index;
    if (index < 0 || this._size <= index) {
      return ite;
    }
    this._keyValues.splice(index, 1);
    --this._size;

    const ite2: iterator<_KeyT, _ValT> = new iterator<_KeyT, _ValT>(
      this,
      index
    );
    return ite2;
  }

  
  public dumpAsInt() {
    for (let i = 0; i < this._size; i++) {
      CubismLogDebug('{0} ,', this._keyValues[i]);
      CubismLogDebug('\n');
    }
  }

  public static readonly DefaultSize = 10;
  public _keyValues: csmPair<_KeyT, _ValT>[];
  public _dummyValue: _ValT;
  public _size: number;
}


export class iterator<_KeyT, _ValT> {
  
  constructor(v?: csmMap<_KeyT, _ValT>, idx?: number) {
    this._map = v != undefined ? v : new csmMap<_KeyT, _ValT>();

    this._index = idx != undefined ? idx : 0;
  }

  
  public set(ite: iterator<_KeyT, _ValT>): iterator<_KeyT, _ValT> {
    this._index = ite._index;
    this._map = ite._map;
    return this;
  }

  
  public preIncrement(): iterator<_KeyT, _ValT> {
    ++this._index;
    return this;
  }

  
  public preDecrement(): iterator<_KeyT, _ValT> {
    --this._index;
    return this;
  }

  
  public increment(): iterator<_KeyT, _ValT> {
    const iteold = new iterator<_KeyT, _ValT>(this._map, this._index++);
    return iteold;
  }

  
  public decrement(): iterator<_KeyT, _ValT> {
    const iteold = new iterator<_KeyT, _ValT>(this._map, this._index);
    this._map = iteold._map;
    this._index = iteold._index;
    return this;
  }

  
  public ptr(): csmPair<_KeyT, _ValT> {
    return this._map._keyValues[this._index];
  }

  
  public notEqual(ite: iterator<_KeyT, _ValT>): boolean {
    return this._index != ite._index || this._map != ite._map;
  }

  _index: number;
  _map: csmMap<_KeyT, _ValT>;
}
import * as $ from './csmmap';
export namespace Live2DCubismFramework {
  export const csmMap = $.csmMap;
  export type csmMap<K, V> = $.csmMap<K, V>;
  export const csmPair = $.csmPair;
  export type csmPair<K, V> = $.csmPair<K, V>;
  export const iterator = $.iterator;
  export type iterator<K, V> = $.iterator<K, V>;
}
