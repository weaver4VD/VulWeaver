import FuzzySet from './FuzzySet.js';


class RightShoulderFuzzySet extends FuzzySet {
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
			const grad = 1 / (midpoint - left);
			return grad * (value - left);

		}
		if ((value > midpoint) && (value <= right)) {
			return 1;

		}
		return 0;

	}
}

export default RightShoulderFuzzySet;
