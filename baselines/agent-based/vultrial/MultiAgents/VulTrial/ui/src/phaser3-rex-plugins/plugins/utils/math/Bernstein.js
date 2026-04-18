

import Factorial from './Factorial.js';


var Bernstein = function (n, i) {
    return Factorial(n) / Factorial(i) / Factorial(n - i);
};

export default Bernstein;
