const frag = `\
vec3 RGBToHSV(vec3 color) {
  float minv, maxv, delta;
  vec3 res;
  minv = min(min(color.r, color.g), color.b);
  maxv = max(max(color.r, color.g), color.b);
  res.z = maxv;

  delta = maxv - minv;
  if( maxv != 0.0 ) {
    res.y = delta / maxv;
  } else {
    res.y = 0.0;
    res.x = -1.0;
    return res;
  }

  if( color.r == maxv ) {
    res.x = ( color.g - color.b ) / delta;
  } else if( color.g == maxv ) {
    res.x = 2.0 + ( color.b - color.r ) / delta;
  } else {
    res.x = 4.0 + ( color.r - color.g ) / delta;
  }

  res.x = res.x * 60.0;
  if( res.x < 0.0 ) {
    res.x = res.x + 360.0;
  }
   
  return res;
}
`;

export default frag;