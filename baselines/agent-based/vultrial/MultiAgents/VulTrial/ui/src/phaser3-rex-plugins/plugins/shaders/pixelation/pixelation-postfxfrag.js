
const frag = `\
#ifdef GL_FRAGMENT_PRECISION_HIGH
#define highmedp highp
#else
#define highmedp mediump
#endif
precision highmedp float;
uniform sampler2D uMainSampler; 
varying vec2 outTexCoord;
uniform vec2 texSize;
uniform vec2 pixelSize;

void main (void) {
  if ((pixelSize.x > 0.0) || (pixelSize.y > 0.0)) {
    vec2 dxy = pixelSize/texSize;
    vec2 tc = vec2(
      dxy.x*( floor(outTexCoord.x/dxy.x) + 0.5 ), 
      dxy.y*( floor(outTexCoord.y/dxy.y) + 0.5 )
    );
    gl_FragColor = texture2D(uMainSampler, tc);
  } else {        
    gl_FragColor = texture2D(uMainSampler, outTexCoord);
  }
}
`;

export default frag;