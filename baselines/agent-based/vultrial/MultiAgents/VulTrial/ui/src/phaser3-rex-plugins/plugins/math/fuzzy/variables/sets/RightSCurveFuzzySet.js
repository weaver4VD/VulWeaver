import FuzzySet from './FuzzySet.js';


class RightSCurveFuzzySet extends FuzzySet {
	constructor(left, midpoint, right) {
		const representativeValue = (midpoint + right) / 2;
		super(representativeValue);

		this.left = left;
		this.midpoint = midpoint;
		this.right = right;

	}

	computeDegreeOfMembership(value) {

		const midpoint = this.midpoint;
		const left = this.left;
		const right = this.right;

		if ((value >= left) && (value <= midpoint)) {
			if (value <= ((left + midpoint) / 2)) {
				return 2 * (Math.pow((value - left) / (midpoint - left), 2));

			} else {
				return 1 - (2 * (Math.pow((value - midpoint) / (midpoint - left), 2)));

			}
		}
		if ((value > midpoint) && (value <= right)) {
			return 1;

		}
		return 0;

	}
}

export default RightSCurveFuzzySet;
