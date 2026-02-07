

import { strtod } from '../live2dcubismframework';
import { csmMap, iterator as csmMap_iterator } from '../type/csmmap';
import { csmString } from '../type/csmstring';
import { csmVector, iterator as csmVector_iterator } from '../type/csmvector';
import { CubismLogInfo } from './cubismdebug';
const CSM_JSON_ERROR_TYPE_MISMATCH = 'Error: type mismatch';
const CSM_JSON_ERROR_INDEX_OF_BOUNDS = 'Error: index out of bounds';


export abstract class Value {
  
  public constructor() {}

  
  public abstract getString(defaultValue?: string, indent?: string): string;

  
  public getRawString(defaultValue?: string, indent?: string): string {
    return this.getString(defaultValue, indent);
  }

  
  public toInt(defaultValue = 0): number {
    return defaultValue;
  }

  
  public toFloat(defaultValue = 0): number {
    return defaultValue;
  }

  
  public toBoolean(defaultValue = false): boolean {
    return defaultValue;
  }

  
  public getSize(): number {
    return 0;
  }

  
  public getArray(defaultValue: Value[] = null): Value[] {
    return defaultValue;
  }

  
  public getVector(defaultValue = new csmVector<Value>()): csmVector<Value> {
    return defaultValue;
  }

  
  public getMap(defaultValue?: csmMap<string, Value>): csmMap<string, Value> {
    return defaultValue;
  }

  
  public getValueByIndex(index: number): Value {
    return Value.errorValue.setErrorNotForClientCall(
      CSM_JSON_ERROR_TYPE_MISMATCH
    );
  }

  
  public getValueByString(s: string | csmString): Value {
    return Value.nullValue.setErrorNotForClientCall(
      CSM_JSON_ERROR_TYPE_MISMATCH
    );
  }

  
  public getKeys(): csmVector<string> {
    return Value.s_dummyKeys;
  }

  
  public isError(): boolean {
    return false;
  }

  
  public isNull(): boolean {
    return false;
  }

  
  public isBool(): boolean {
    return false;
  }

  
  public isFloat(): boolean {
    return false;
  }

  
  public isString(): boolean {
    return false;
  }

  
  public isArray(): boolean {
    return false;
  }

  
  public isMap(): boolean {
    return false;
  }

  
  public equals(value: csmString): boolean;
  public equals(value: string): boolean;
  public equals(value: number): boolean;
  public equals(value: boolean): boolean;
  public equals(value: any): boolean {
    return false;
  }

  
  public isStatic(): boolean {
    return false;
  }

  
  public setErrorNotForClientCall(errorStr: string): Value {
    return JsonError.errorValue;
  }

  
  public static staticInitializeNotForClientCall(): void {
    JsonBoolean.trueValue = new JsonBoolean(true);
    JsonBoolean.falseValue = new JsonBoolean(false);
    Value.errorValue = new JsonError('ERROR', true);
    Value.nullValue = new JsonNullvalue();
    Value.s_dummyKeys = new csmVector<string>();
  }

  
  public static staticReleaseNotForClientCall(): void {
    JsonBoolean.trueValue = null;
    JsonBoolean.falseValue = null;
    Value.errorValue = null;
    Value.nullValue = null;
    Value.s_dummyKeys = null;
  }

  protected _stringBuffer: string;

  private static s_dummyKeys: csmVector<string>;

  public static errorValue: Value;
  public static nullValue: Value;
}


export class CubismJson {
  
  public constructor(buffer?: ArrayBuffer, length?: number) {
    this._error = null;
    this._lineCount = 0;
    this._root = null;

    if (buffer != undefined) {
      this.parseBytes(buffer, length);
    }
  }

  
  public static create(buffer: ArrayBuffer, size: number) {
    const json = new CubismJson();
    const succeeded: boolean = json.parseBytes(buffer, size);

    if (!succeeded) {
      CubismJson.delete(json);
      return null;
    } else {
      return json;
    }
  }

  
  public static delete(instance: CubismJson) {
    instance = null;
  }

  
  public getRoot(): Value {
    return this._root;
  }

  
  public arrayBufferToString(buffer: ArrayBuffer): string {
    const uint8Array: Uint8Array = new Uint8Array(buffer);
    let str = '';

    for (let i = 0, len: number = uint8Array.length; i < len; ++i) {
      str += '%' + this.pad(uint8Array[i].toString(16));
    }

    str = decodeURIComponent(str);
    return str;
  }

  
  private pad(n: string): string {
    return n.length < 2 ? '0' + n : n;
  }

  
  public parseBytes(buffer: ArrayBuffer, size: number): boolean {
    const endPos: number[] = new Array(1);
    const decodeBuffer: string = this.arrayBufferToString(buffer);
    this._root = this.parseValue(decodeBuffer, size, 0, endPos);

    if (this._error) {
      let strbuf = '\0';
      strbuf = 'Json parse error : @line ' + (this._lineCount + 1) + '\n';
      this._root = new JsonString(strbuf);

      CubismLogInfo('{0}', this._root.getRawString());
      return false;
    } else if (this._root == null) {
      this._root = new JsonError(new csmString(this._error), false);
      return false;
    }
    return true;
  }

  
  public getParseError(): string {
    return this._error;
  }

  
  public checkEndOfFile(): boolean {
    return this._root.getArray()[1].equals('EOF');
  }

  
  protected parseValue(
    buffer: string,
    length: number,
    begin: number,
    outEndPos: number[]
  ) {
    if (this._error) return null;

    let o: Value = null;
    let i: number = begin;
    let f: number;

    for (; i < length; i++) {
      const c: string = buffer[i];
      switch (c) {
        case '-':
        case '.':
        case '0':
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
        case '7':
        case '8':
        case '9': {
          const afterString: string[] = new Array(1);
          f = strtod(buffer.slice(i), afterString);
          outEndPos[0] = buffer.indexOf(afterString[0]);
          return new JsonFloat(f);
        }
        case '"':
          return new JsonString(
            this.parseString(buffer, length, i + 1, outEndPos)
          );
        case '[':
          o = this.parseArray(buffer, length, i + 1, outEndPos);
          return o;
        case '{':
          o = this.parseObject(buffer, length, i + 1, outEndPos);
          return o;
        case 'n':
          if (i + 3 < length) {
            o = new JsonNullvalue();
            outEndPos[0] = i + 4;
          } else {
            this._error = 'parse null';
          }
          return o;
        case 't':
          if (i + 3 < length) {
            o = JsonBoolean.trueValue;
            outEndPos[0] = i + 4;
          } else {
            this._error = 'parse true';
          }
          return o;
        case 'f':
          if (i + 4 < length) {
            o = JsonBoolean.falseValue;
            outEndPos[0] = i + 5;
          } else {
            this._error = "illegal ',' position";
          }
          return o;
        case ',':
          this._error = "illegal ',' position";
          return null;
        case ']':
          outEndPos[0] = i;
          return null;
        case '\n':
          this._lineCount++;
        case ' ':
        case '\t':
        case '\r':
        default:
          break;
      }
    }

    this._error = 'illegal end of value';
    return null;
  }

  
  protected parseString(
    string: string,
    length: number,
    begin: number,
    outEndPos: number[]
  ): string {
    if (this._error) return null;

    let i = begin;
    let c: string, c2: string;
    const ret: csmString = new csmString('');
    let bufStart: number = begin;

    for (; i < length; i++) {
      c = string[i];

      switch (c) {
        case '"': {
          outEndPos[0] = i + 1;
          ret.append(string.slice(bufStart), i - bufStart);
          return ret.s;
        }
        case '//': {
          i++;

          if (i - 1 > bufStart) {
            ret.append(string.slice(bufStart), i - bufStart);
          }
          bufStart = i + 1;

          if (i < length) {
            c2 = string[i];

            switch (c2) {
              case '\\':
                ret.expansion(1, '\\');
                break;
              case '"':
                ret.expansion(1, '"');
                break;
              case '/':
                ret.expansion(1, '/');
                break;
              case 'b':
                ret.expansion(1, '\b');
                break;
              case 'f':
                ret.expansion(1, '\f');
                break;
              case 'n':
                ret.expansion(1, '\n');
                break;
              case 'r':
                ret.expansion(1, '\r');
                break;
              case 't':
                ret.expansion(1, '\t');
                break;
              case 'u':
                this._error = 'parse string/unicord escape not supported';
                break;
              default:
                break;
            }
          } else {
            this._error = 'parse string/escape error';
          }
        }
        default: {
          break;
        }
      }
    }

    this._error = 'parse string/illegal end';
    return null;
  }

  
  protected parseObject(
    buffer: string,
    length: number,
    begin: number,
    outEndPos: number[]
  ): Value {
    if (this._error) return null;
    const ret: JsonMap = new JsonMap();
    let key = '';
    let i: number = begin;
    let c = '';
    const localRetEndPos2: number[] = Array(1);
    let ok = false;
    for (; i < length; i++) {
      FOR_LOOP: for (; i < length; i++) {
        c = buffer[i];

        switch (c) {
          case '"':
            key = this.parseString(buffer, length, i + 1, localRetEndPos2);
            if (this._error) {
              return null;
            }

            i = localRetEndPos2[0];
            ok = true;
            break FOR_LOOP;
          case '}':
            outEndPos[0] = i + 1;
            return ret;
          case ':':
            this._error = "illegal ':' position";
            break;
          case '\n':
            this._lineCount++;
          default:
            break;
        }
      }
      if (!ok) {
        this._error = 'key not found';
        return null;
      }

      ok = false;
      FOR_LOOP2: for (; i < length; i++) {
        c = buffer[i];

        switch (c) {
          case ':':
            ok = true;
            i++;
            break FOR_LOOP2;
          case '}':
            this._error = "illegal '}' position";
            break;
          case '\n':
            this._lineCount++;
          default:
            break;
        }
      }

      if (!ok) {
        this._error = "':' not found";
        return null;
      }
      const value: Value = this.parseValue(buffer, length, i, localRetEndPos2);
      if (this._error) {
        return null;
      }

      i = localRetEndPos2[0];
      ret.put(key, value);

      FOR_LOOP3: for (; i < length; i++) {
        c = buffer[i];

        switch (c) {
          case ',':
            break FOR_LOOP3;
          case '}':
            outEndPos[0] = i + 1;
            return ret;
          case '\n':
            this._lineCount++;
          default:
            break;
        }
      }
    }

    this._error = 'illegal end of perseObject';
    return null;
  }

  
  protected parseArray(
    buffer: string,
    length: number,
    begin: number,
    outEndPos: number[]
  ): Value {
    if (this._error) return null;
    let ret: JsonArray = new JsonArray();
    let i: number = begin;
    let c: string;
    const localRetEndpos2: number[] = new Array(1);
    for (; i < length; i++) {
      const value: Value = this.parseValue(buffer, length, i, localRetEndpos2);

      if (this._error) {
        return null;
      }
      i = localRetEndpos2[0];

      if (value) {
        ret.add(value);
      }
      FOR_LOOP: for (; i < length; i++) {
        c = buffer[i];

        switch (c) {
          case ',':
            break FOR_LOOP;
          case ']':
            outEndPos[0] = i + 1;
            return ret;
          case '\n':
            ++this._lineCount;
          default:
            break;
        }
      }
    }

    ret = void 0;
    this._error = 'illegal end of parseObject';
    return null;
  }

  _error: string;
  _lineCount: number;
  _root: Value;
}


export class JsonFloat extends Value {
  
  constructor(v: number) {
    super();

    this._value = v;
  }

  
  public isFloat(): boolean {
    return true;
  }

  
  public getString(defaultValue: string, indent: string): string {
    const strbuf = '\0';
    this._value = parseFloat(strbuf);
    this._stringBuffer = strbuf;

    return this._stringBuffer;
  }

  
  public toInt(defaultValue = 0): number {
    return parseInt(this._value.toString());
  }

  
  public toFloat(defaultValue = 0.0): number {
    return this._value;
  }

  
  public equals(value: csmString): boolean;
  public equals(value: string): boolean;
  public equals(value: number): boolean;
  public equals(value: boolean): boolean;
  public equals(value: any): boolean {
    if ('number' === typeof value) {
      if (Math.round(value)) {
        return false;
      }
      else {
        return value == this._value;
      }
    }
    return false;
  }

  private _value: number;
}


export class JsonBoolean extends Value {
  
  public isBool(): boolean {
    return true;
  }

  
  public toBoolean(defaultValue = false): boolean {
    return this._boolValue;
  }

  
  public getString(defaultValue: string, indent: string): string {
    this._stringBuffer = this._boolValue ? 'true' : 'false';

    return this._stringBuffer;
  }

  
  public equals(value: csmString): boolean;
  public equals(value: string): boolean;
  public equals(value: number): boolean;
  public equals(value: boolean): boolean;
  public equals(value: any): boolean {
    if ('boolean' === typeof value) {
      return value == this._boolValue;
    }
    return false;
  }

  
  public isStatic(): boolean {
    return true;
  }

  
  public constructor(v: boolean) {
    super();

    this._boolValue = v;
  }

  static trueValue: JsonBoolean;
  static falseValue: JsonBoolean;

  private _boolValue: boolean;
}


export class JsonString extends Value {
  
  public constructor(s: string);
  public constructor(s: csmString);
  public constructor(s: any) {
    super();

    if ('string' === typeof s) {
      this._stringBuffer = s;
    }

    if (s instanceof csmString) {
      this._stringBuffer = s.s;
    }
  }

  
  public isString(): boolean {
    return true;
  }

  
  public getString(defaultValue: string, indent: string): string {
    return this._stringBuffer;
  }

  
  public equals(value: csmString): boolean;
  public equals(value: string): boolean;
  public equals(value: number): boolean;
  public equals(value: boolean): boolean;
  public equals(value: any): boolean {
    if ('string' === typeof value) {
      return this._stringBuffer == value;
    }

    if (value instanceof csmString) {
      return this._stringBuffer == value.s;
    }

    return false;
  }
}


export class JsonError extends JsonString {
  
  public isStatic(): boolean {
    return this._isStatic;
  }

  
  public setErrorNotForClientCall(s: string): Value {
    this._stringBuffer = s;
    return this;
  }

  
  public constructor(s: csmString | string, isStatic: boolean) {
    if ('string' === typeof s) {
      super(s);
    } else {
      super(s);
    }
    this._isStatic = isStatic;
  }

  
  public isError(): boolean {
    return true;
  }

  protected _isStatic: boolean;
}


export class JsonNullvalue extends Value {
  
  public isNull(): boolean {
    return true;
  }

  
  public getString(defaultValue: string, indent: string): string {
    return this._stringBuffer;
  }

  
  public isStatic(): boolean {
    return true;
  }

  
  public setErrorNotForClientCall(s: string): Value {
    this._stringBuffer = s;
    return JsonError.nullValue;
  }

  
  public constructor() {
    super();

    this._stringBuffer = 'NullValue';
  }
}


export class JsonArray extends Value {
  
  public constructor() {
    super();
    this._array = new csmVector<Value>();
  }

  
  public release(): void {
    for (
      let ite: csmVector_iterator<Value> = this._array.begin();
      ite.notEqual(this._array.end());
      ite.preIncrement()
    ) {
      let v: Value = ite.ptr();

      if (v && !v.isStatic()) {
        v = void 0;
        v = null;
      }
    }
  }

  
  public isArray(): boolean {
    return true;
  }

  
  public getValueByIndex(index: number): Value {
    if (index < 0 || this._array.getSize() <= index) {
      return Value.errorValue.setErrorNotForClientCall(
        CSM_JSON_ERROR_INDEX_OF_BOUNDS
      );
    }

    const v: Value = this._array.at(index);

    if (v == null) {
      return Value.nullValue;
    }

    return v;
  }

  
  public getValueByString(s: string | csmString): Value {
    return Value.errorValue.setErrorNotForClientCall(
      CSM_JSON_ERROR_TYPE_MISMATCH
    );
  }

  
  public getString(defaultValue: string, indent: string): string {
    const stringBuffer: string = indent + '[\n';

    for (
      let ite: csmVector_iterator<Value> = this._array.begin();
      ite.notEqual(this._array.end());
      ite.increment()
    ) {
      const v: Value = ite.ptr();
      this._stringBuffer += indent + '' + v.getString(indent + ' ') + '\n';
    }

    this._stringBuffer = stringBuffer + indent + ']\n';

    return this._stringBuffer;
  }

  
  public add(v: Value): void {
    this._array.pushBack(v);
  }

  
  public getVector(defaultValue: csmVector<Value> = null): csmVector<Value> {
    return this._array;
  }

  
  public getSize(): number {
    return this._array.getSize();
  }

  private _array: csmVector<Value>;
}


export class JsonMap extends Value {
  
  public constructor() {
    super();
    this._map = new csmMap<string, Value>();
  }

  
  public release(): void {
    const ite: csmMap_iterator<string, Value> = this._map.begin();

    while (ite.notEqual(this._map.end())) {
      let v: Value = ite.ptr().second;

      if (v && !v.isStatic()) {
        v = void 0;
        v = null;
      }

      ite.preIncrement();
    }
  }

  
  public isMap(): boolean {
    return true;
  }

  
  public getValueByString(s: string | csmString): Value {
    if (s instanceof csmString) {
      const ret: Value = this._map.getValue(s.s);
      if (ret == null) {
        return Value.nullValue;
      }
      return ret;
    }

    for (
      let iter: csmMap_iterator<string, Value> = this._map.begin();
      iter.notEqual(this._map.end());
      iter.preIncrement()
    ) {
      if (iter.ptr().first == s) {
        if (iter.ptr().second == null) {
          return Value.nullValue;
        }
        return iter.ptr().second;
      }
    }

    return Value.nullValue;
  }

  
  public getValueByIndex(index: number): Value {
    return Value.errorValue.setErrorNotForClientCall(
      CSM_JSON_ERROR_TYPE_MISMATCH
    );
  }

  
  public getString(defaultValue: string, indent: string) {
    this._stringBuffer = indent + '{\n';

    const ite: csmMap_iterator<string, Value> = this._map.begin();
    while (ite.notEqual(this._map.end())) {
      const key = ite.ptr().first;
      const v: Value = ite.ptr().second;

      this._stringBuffer +=
        indent + ' ' + key + ' : ' + v.getString(indent + '   ') + ' \n';
      ite.preIncrement();
    }

    this._stringBuffer += indent + '}\n';

    return this._stringBuffer;
  }

  
  public getMap(defaultValue?: csmMap<string, Value>): csmMap<string, Value> {
    return this._map;
  }

  
  public put(key: string, v: Value): void {
    this._map.setValue(key, v);
  }

  
  public getKeys(): csmVector<string> {
    if (!this._keys) {
      this._keys = new csmVector<string>();

      const ite: csmMap_iterator<string, Value> = this._map.begin();

      while (ite.notEqual(this._map.end())) {
        const key: string = ite.ptr().first;
        this._keys.pushBack(key);
        ite.preIncrement();
      }
    }
    return this._keys;
  }

  
  public getSize(): number {
    return this._keys.getSize();
  }

  private _map: csmMap<string, Value>;
  private _keys: csmVector<string>;
}
import * as $ from './cubismjson';
export namespace Live2DCubismFramework {
  export const CubismJson = $.CubismJson;
  export type CubismJson = $.CubismJson;
  export const JsonArray = $.JsonArray;
  export type JsonArray = $.JsonArray;
  export const JsonBoolean = $.JsonBoolean;
  export type JsonBoolean = $.JsonBoolean;
  export const JsonError = $.JsonError;
  export type JsonError = $.JsonError;
  export const JsonFloat = $.JsonFloat;
  export type JsonFloat = $.JsonFloat;
  export const JsonMap = $.JsonMap;
  export type JsonMap = $.JsonMap;
  export const JsonNullvalue = $.JsonNullvalue;
  export type JsonNullvalue = $.JsonNullvalue;
  export const JsonString = $.JsonString;
  export type JsonString = $.JsonString;
  export const Value = $.Value;
  export type Value = $.Value;
}
