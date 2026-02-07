import FuzzySet from './FuzzySet.js';


class LeftSCurveFuzzySet extends FuzzySet {
	constructor(left, midpoint, right) {
		const representativeValue = (midpoint + left) / 2;
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

			return 1;

		}

		if ((value > midpoint) && (value <= right)) {
			if (value >= ((midpoint + right) / 2)) {
				return 2 * (Math.pow((value - right) / (midpoint - right), 2));

			} else {
				return 1 - (2 * (Math.pow((value - midpoint) / (midpoint - right), 2)));

			}

		}
		return 0;

	}
}

export default LeftSCurveFuzzySet;
