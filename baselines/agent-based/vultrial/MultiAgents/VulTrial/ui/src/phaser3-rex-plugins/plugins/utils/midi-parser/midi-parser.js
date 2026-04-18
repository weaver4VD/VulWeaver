


'use strict';
var _atob = function(string) {
	var b64 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
	var b64re = /^(?:[A-Za-z\d+\/]{4})*?(?:[A-Za-z\d+\/]{2}(?:==)?|[A-Za-z\d+\/]{3}=?)?$/;
   	string = string.replace( /^.*?base64,/ , "");
    string = String(string).replace(/[\t\n\f\r ]+/g, "");
    if (!b64re.test(string))
        throw new TypeError("Failed to execute '_atob' : The string to be decoded is not correctly encoded.");
    string += "==".slice(2 - (string.length & 3));
    var bitmap, result = "", r1, r2, i = 0;
    for (; i < string.length;) {
        bitmap = b64.indexOf(string.charAt(i++)) << 18 | b64.indexOf(string.charAt(i++)) << 12
                | (r1 = b64.indexOf(string.charAt(i++))) << 6 | (r2 = b64.indexOf(string.charAt(i++)));

        result += r1 === 64 ? String.fromCharCode(bitmap >> 16 & 255)
                : r2 === 64 ? String.fromCharCode(bitmap >> 16 & 255, bitmap >> 8 & 255)
                : String.fromCharCode(bitmap >> 16 & 255, bitmap >> 8 & 255, bitmap & 255);
    }
    return result;
};


var MIDIParser = {
	debug: false,

	parse: function(input, _callback){
		if(input instanceof Uint8Array) return MIDIParser.Uint8(input);
		else if(typeof input === 'string') return MIDIParser.Base64(input);
		else if(input instanceof HTMLElement && input.type === 'file') return MIDIParser.addListener(input , _callback);
		else throw new Error('MIDIParser.parse() : Invalid input provided');
	},
	addListener: function(_fileElement, _callback){
		if(!File || !FileReader) throw new Error('The File|FileReader APIs are not supported in this browser. Use instead MIDIParser.Base64() or MIDIParser.Uint8()');
		if( _fileElement === undefined ||
			!(_fileElement instanceof HTMLElement) ||
			_fileElement.tagName !== 'INPUT' ||
			_fileElement.type.toLowerCase() !== 'file' ){
				console.warn('MIDIParser.addListener() : Provided element is not a valid FILE INPUT element');
				return false;
		}
		_callback = _callback || function(){};

		_fileElement.addEventListener('change', function(InputEvt){
			if (!InputEvt.target.files.length) return false;
			console.log('MIDIParser.addListener() : File detected in INPUT ELEMENT processing data..');
			var reader = new FileReader();
			reader.readAsArrayBuffer(InputEvt.target.files[0]);
			reader.onload =  function(e){
				_callback( MIDIParser.Uint8(new Uint8Array(e.target.result)));
			};
		});
	},

	Base64 : function(b64String){
		b64String = String(b64String);

		var raw = _atob(b64String);
		var rawLength = raw.length;
		var array = new Uint8Array(new ArrayBuffer(rawLength));

		for(var i=0; i<rawLength; i++) array[i] = raw.charCodeAt(i);
		return  MIDIParser.Uint8(array) ;
	},
	Uint8: function(FileAsUint8Array){
		var file = {
			data: null,
			pointer: 0,
			movePointer: function(_bytes){
				this.pointer += _bytes;
				return this.pointer;
			},
			readInt: function(_bytes){
				_bytes = Math.min(_bytes, this.data.byteLength-this.pointer);
				if (_bytes < 1) return -1;
				var value = 0;
				if(_bytes > 1){
					for(var i=1; i<= (_bytes-1); i++){
						value += this.data.getUint8(this.pointer) * Math.pow(256, (_bytes - i));
						this.pointer++;
					}
				}
				value += this.data.getUint8(this.pointer);
				this.pointer++;
				return value;
			},
			readStr: function(_bytes){
				var text = '';
				for(var char=1; char <= _bytes; char++) text +=  String.fromCharCode(this.readInt(1));
				return text;
			},
			readIntVLV: function(){
				var value = 0;
				if ( this.pointer >= this.data.byteLength ){
					return -1;
				}else if(this.data.getUint8(this.pointer) < 128){
					value = this.readInt(1);
				}else{
					var FirstBytes = [];
					while(this.data.getUint8(this.pointer) >= 128){
						FirstBytes.push(this.readInt(1) - 128);
					}
					var lastByte  = this.readInt(1);
					for(var dt = 1; dt <= FirstBytes.length; dt++){
						value = FirstBytes[FirstBytes.length - dt] * Math.pow(128, dt);
					}
					value += lastByte;
				}
				return value;
			}
		};

		file.data = new DataView(FileAsUint8Array.buffer, FileAsUint8Array.byteOffset, FileAsUint8Array.byteLength);
		if(file.readInt(4) !== 0x4D546864){
			console.warn('Header validation failed (not MIDI standard or file corrupt.)');
			return false;
		}
		var headerSize 			= file.readInt(4);
		var MIDI 				= {};
		MIDI.formatType   		= file.readInt(2);
		MIDI.tracks 			= file.readInt(2);
		MIDI.track				= [];
		var timeDivisionByte1   = file.readInt(1);
		var timeDivisionByte2   = file.readInt(1);
		if(timeDivisionByte1 >= 128){
			MIDI.timeDivision    = [];
			MIDI.timeDivision[0] = timeDivisionByte1 - 128;
			MIDI.timeDivision[1] = timeDivisionByte2;
		}else MIDI.timeDivision  = (timeDivisionByte1 * 256) + timeDivisionByte2;// else... ticks per beat MODE  (2 bytes value)
		for(var t=1; t <= MIDI.tracks; t++){
			MIDI.track[t-1] 	= {event: []};
			var headerValidation = file.readInt(4);
			if ( headerValidation === -1 ) break;
			if(headerValidation !== 0x4D54726B) return false;
			file.readInt(4);
			var e		  		= 0;
			var endOfTrack 		= false;
			var statusByte;
			var laststatusByte;
			while(!endOfTrack){
				e++;
				MIDI.track[t-1].event[e-1] = {};
				MIDI.track[t-1].event[e-1].deltaTime  = file.readIntVLV();
				statusByte = file.readInt(1);
				if(statusByte === -1) break;
                else if(statusByte >= 128) laststatusByte = statusByte;
				else{
					statusByte = laststatusByte;
					file.movePointer(-1);
				}
				if(statusByte === 0xFF){
					MIDI.track[t-1].event[e-1].type = 0xFF;
					MIDI.track[t-1].event[e-1].metaType =  file.readInt(1);
					var metaEventLength = file.readIntVLV();
					switch(MIDI.track[t-1].event[e-1].metaType){
						case 0x2F:
						case -1:
							endOfTrack = true;
							break;
						case 0x01:
						case 0x02:
						case 0x03:
						case 0x06:
							MIDI.track[t-1].event[e-1].data = file.readStr(metaEventLength);
							break;
						case 0x21:
						case 0x59:
						case 0x51:
							MIDI.track[t-1].event[e-1].data = file.readInt(metaEventLength);
							break;
						case 0x54:
						case 0x58:
							MIDI.track[t-1].event[e-1].data	   = [];
							MIDI.track[t-1].event[e-1].data[0] = file.readInt(1);
							MIDI.track[t-1].event[e-1].data[1] = file.readInt(1);
							MIDI.track[t-1].event[e-1].data[2] = file.readInt(1);
							MIDI.track[t-1].event[e-1].data[3] = file.readInt(1);
							break;
						default :
							file.readInt(metaEventLength);
							MIDI.track[t-1].event[e-1].data = file.readInt(metaEventLength);
							if (this.debug) console.info('Unimplemented 0xFF event! data block readed as Integer');
					}
				}else{
					statusByte = statusByte.toString(16).split('');
					if(!statusByte[1]) statusByte.unshift('0');
					MIDI.track[t-1].event[e-1].type = parseInt(statusByte[0], 16);// first byte is EVENT TYPE ID
					MIDI.track[t-1].event[e-1].channel = parseInt(statusByte[1], 16);// second byte is channel
					switch(MIDI.track[t-1].event[e-1].type){
						case 0xF:
							var event_length = file.readIntVLV();
							MIDI.track[t-1].event[e-1].data = file.readInt(event_length);
							if (this.debug) console.info('Unimplemented 0xF exclusive events! data block readed as Integer');
							break;
						case 0xA:
						case 0xB:
						case 0xE:
						case 0x8:
						case 0x9:
							MIDI.track[t-1].event[e-1].data = [];
							MIDI.track[t-1].event[e-1].data[0] = file.readInt(1);
							MIDI.track[t-1].event[e-1].data[1] = file.readInt(1);
							break;
						case 0xC:
						case 0xD:
							MIDI.track[t-1].event[e-1].data = file.readInt(1);
							break;
						case -1:
							endOfTrack = true;
							break;
 						default:
							console.warn('Unknown EVENT detected.... reading cancelled!');
							return false;
					}
				}
			}
		}
		return MIDI;
	}
};


if(typeof module !== 'undefined') module.exports = MIDIParser;